"""
LangGraph orchestration — one graph invocation per user message.

    START → intake ──┬─ more questions ───────────→ END (bot asks next question)
                     ├─ profile complete → pipeline → END (report generated)
                     └─ already done → followup → END (Q&A about the report)

If langgraph isn't importable the same three nodes run sequentially — identical
behaviour, zero demo risk (graceful degradation is a feature, not a bug).
"""

from __future__ import annotations

from typing import Optional

from ..agents import intake as intake_mod
from ..agents.prompts import (
    DONE_EN, DONE_HI, ERROR_EN, ERROR_HI,
    GENERAL_HELP_EN, GENERAL_HELP_HI,
    PROFILE_NOTE_EN, PROFILE_NOTE_HI, WELCOME_EN, WELCOME_HI,
)
from ..engine.reasoner import build_report
from ..core import llm
from .state import GraphState

try:  # pragma: no cover - depends on environment
    from langgraph.graph import END, START, StateGraph
    HAS_LANGGRAPH = True
except Exception:  # pragma: no cover
    END = START = None
    HAS_LANGGRAPH = False


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _progress(profile: dict) -> tuple[int, int]:
    total = intake_mod.questions_total_for(profile)
    remaining = len(intake_mod.pending_question_ids(profile))
    return total - remaining, total


def _question_payload(state: GraphState, q: dict, prefix: Optional[str] = None) -> GraphState:
    lang = state["language"]
    text = intake_mod.render_question(q, state["profile"], lang)
    if prefix:
        text = prefix + "\n\n" + text
    state["bot_messages"] = [text]
    state["quick_replies"] = intake_mod.render_options(q, lang, state["profile"])
    state["next_qid"] = q["id"]
    state["input_type"] = q.get("type", "text")
    state["step"], state["total_steps"] = _progress(state["profile"])
    return state


def _help_payload(state: GraphState, q: dict, help_kind: str) -> GraphState:
    """The user asked a doubt instead of answering — explain, then gently re-ask.

    With a Gemini key the explanation is conversational (grounded in the curated
    help text); without one we respond with that same template help text, so the
    "ask me anything, anytime" promise holds even fully offline.
    """
    lang = state.get("language") or "en"
    parts: list[str] = []

    explained = llm.explain_doubt(state.get("message", ""), q, state["profile"], lang)
    if explained:
        parts.append(explained)
    else:
        if help_kind == "general":
            parts.append(GENERAL_HELP_HI if lang == "hi" else GENERAL_HELP_EN)
        help_text = intake_mod.help_text_for(q, lang)
        if help_text:
            prefix = "💡 " if help_kind == "question" else ""
            parts.append(prefix + help_text)

    return _question_payload(state, q, prefix="\n\n".join(parts) if parts else None)


def intake_node(state: GraphState) -> GraphState:
    """Parse the user's answer to the pending question, then ask the next one."""
    profile = state["profile"]
    lang = profile.get("language") or "en"

    # Auto-language-detection on the very first free-text touch
    if not profile.get("language") and state.get("message"):
        lang = intake_mod.detect_language(state["message"])
    state["language"] = lang

    current_q = intake_mod.get_question(state.get("current_qid") or "")
    message = (state.get("message") or "").strip()

    if current_q:
        # "Ask anytime": a confused user gets an explanation + the same question
        # again — never an error — and the flow simply continues from there.
        help_kind = intake_mod.looks_like_help(message)
        if help_kind:
            return _help_payload(state, current_q, help_kind)

        ok, value = intake_mod.parse_answer(current_q, message, profile)
        if not ok:
            err = (ERROR_HI if lang == "hi" else ERROR_EN)
            return _question_payload(state, current_q, prefix=err.rstrip() + " ")

        field = current_q.get("field", current_q["id"])
        profile[field] = value

        # answering the language question switches the conversation language
        if current_q["id"] == "language":
            lang = value
            profile["language"] = value
        elif not profile.get("language"):
            profile["language"] = lang
        state["language"] = lang

    nxt = intake_mod.next_question(profile)
    if nxt:
        prefix = None
        # contextual acknowledgment makes the bot feel smart & adaptive
        if current_q and current_q["id"] == "occupation":
            notes = PROFILE_NOTE_HI if lang == "hi" else PROFILE_NOTE_EN
            prefix = notes.get(value)  # type: ignore[arg-type]
        return _question_payload(state, nxt, prefix=prefix)

    state["ready_to_report"] = True
    return state


def pipeline_node(state: GraphState) -> GraphState:
    """Profile complete → match, detect near-misses, rank, reason, report."""
    profile = state["profile"]
    lang = state.get("language", "en")
    report = build_report(profile)

    # Optional Gemini polish — silent fallback to the template summary
    polished = llm.polish_summary(profile, report, lang)
    if polished:
        report["summary_llm"] = polished

    state["report"] = report
    state["done"] = True
    state["ready_to_report"] = False
    done_tmpl = DONE_HI if lang == "hi" else DONE_EN
    state["bot_messages"] = [done_tmpl.format(
        name=profile.get("name", ""), total=report["n_checked"]
    )]
    state["quick_replies"] = []
    state["step"], state["total_steps"] = _progress(profile)
    return state


def followup_node(state: GraphState) -> GraphState:
    """Post-report Q&A. Uses Gemini when a key is configured, else templates."""
    profile = state["profile"]
    lang = state.get("language", "en")
    report = state.get("report") or {}
    msg = (state.get("message") or "").lower()

    llm_answer = llm.answer_followup(state.get("message", ""), profile, report, lang)
    if llm_answer:
        state["bot_messages"] = [llm_answer]
        return state

    if any(k in msg for k in ("document", "दस्तावेज़", "कागज")):
        top = (report.get("eligible") or [{}])[0]
        if top:
            docs = top.get("documents_hi" if lang == "hi" else "documents_en", [])
            head = "आपके टॉप मैच के लिए दस्तावेज़:" if lang == "hi" else f"Documents for your top match — {top.get('name_en')}:"
            state["bot_messages"] = [head + "\n" + "\n".join("📄 " + d for d in docs)]
            return state

    if any(k in msg for k in ("apply", "आवेदन", "कैसे करें", "kaise")):
        links = "\n".join(
            f"🔗 {c['name_hi' if lang == 'hi' else 'name_en'].split(' (')[0]}: {c['apply_url']}"
            for c in (report.get("eligible") or [])[:5]
        )
        head = "ये रहे आपके शीर्ष योजनाओं के आवेदन लिंक:" if lang == "hi" else "Here are the apply links for your top schemes:"
        state["bot_messages"] = [(head + "\n" + links) if links else ("कोई पात्र योजना नहीं मिली।" if lang == "hi" else "No eligible schemes found.")]
        return state

    default = (
        "आपकी रिपोर्ट ऊपर तैयार है! 📊\n• किसी भी कार्ड पर क्लिक कर के पूरा विश्लेषण देखें\n"
        "• 'Documents' पूछें दस्तावेज़ सूची के लिए\n• 'Apply' पूछें आवेदन लिंक के लिए\n"
        "• नई प्रोफ़ाइल के लिए ⟳ Restart दबाएँ"
        if lang == "hi" else
        "Your report is ready above! 📊\n• Tap any card for full reasoning, documents & apply links\n"
        "• Ask me 'documents' for the checklist\n• Ask me 'apply' for all links\n"
        "• Press ⟳ Restart to try a new profile"
    )
    state["bot_messages"] = [default]
    return state


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def welcome_state() -> GraphState:
    """Initial message shown when a session starts."""
    q = intake_mod.QUESTIONS[0]  # language question
    state: GraphState = {
        "profile": {},
        "language": "en",
        "current_qid": None,
        "bot_messages": [WELCOME_EN + "\n---\n" + WELCOME_HI],
        "quick_replies": intake_mod.render_options(q, "en", {}),
        "input_type": q.get("type", "text"),
        "next_qid": q["id"],
        "step": 0,
        "total_steps": len(intake_mod.QUESTIONS),
        "done": False,
    }
    return state


def _router(state: GraphState) -> str:
    if state.get("ready_to_report"):
        return "pipeline"
    if state.get("done"):
        return "followup"
    return "end"


if HAS_LANGGRAPH:
    _builder = StateGraph(GraphState)
    _builder.add_node("intake", intake_node)
    _builder.add_node("pipeline", pipeline_node)
    _builder.add_node("followup", followup_node)
    # if the report already exists, skip intake entirely → straight to Q&A
    _builder.add_conditional_edges(START, lambda s: "followup" if s.get("done") else "intake",
                                   {"followup": "followup", "intake": "intake"})
    _builder.add_conditional_edges("intake", _router, {"pipeline": "pipeline", "followup": "followup", "end": END})
    _builder.add_edge("pipeline", END)
    _builder.add_edge("followup", END)
    _graph = _builder.compile()
else:  # pragma: no cover
    _graph = None


def process_message(profile: dict, message: str, current_qid: Optional[str],
                    done: bool, report: Optional[dict]) -> GraphState:
    """Public entry point used by the API layer. Runs one turn of the graph."""
    language = profile.get("language") or intake_mod.detect_language(message)
    init: GraphState = {
        "message": message,
        "profile": profile,
        "current_qid": current_qid,
        "language": language,
        "done": done,
        "report": report,
    }
    if _graph is not None:
        return _graph.invoke(init)
    # sequential fallback (identical node logic)
    if done:
        return followup_node(init)
    state = intake_node(init)
    if state.get("ready_to_report"):
        state = pipeline_node(state)
    return state
