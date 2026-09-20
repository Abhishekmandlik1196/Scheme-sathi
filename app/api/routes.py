"""API endpoints for Scheme Saathi."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..engine.matcher import load_schemes
from ..graph.main_graph import HAS_LANGGRAPH, process_message, welcome_state
from ..core import config
from . import demo_runner
from .models import ChatRequest, ChatResponse, MetaResponse, SessionResponse
from .report_html import render_html_report
from .session import create_session, get_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Session & chat
# ---------------------------------------------------------------------------


@router.post("/api/session/new", response_model=SessionResponse)
def new_session():
    session = create_session()
    state = welcome_state()
    session["current_qid"] = state.get("next_qid")
    return SessionResponse(
        session_id=session["id"],
        messages=state["bot_messages"],
        quick_replies=state["quick_replies"],
        step=state.get("step", 0),
        total_steps=state.get("total_steps", 0),
    )


@router.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Start a new session.")

    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Empty message.")

    session["history"].append({"sender": "user", "text": message})
    had_report = bool(session.get("report"))
    state = process_message(
        profile=session["profile"],
        message=message,
        current_qid=session["current_qid"],
        done=session["done"],
        report=session["report"],
    )

    session["current_qid"] = state.get("next_qid")
    session["done"] = bool(state.get("done", session["done"]))
    if state.get("report"):
        session["report"] = state["report"]
    for m in state.get("bot_messages", []):
        session["history"].append({"sender": "bot", "text": m})

    return ChatResponse(
        messages=state.get("bot_messages", []),
        quick_replies=state.get("quick_replies", []),
        step=state.get("step", 0),
        total_steps=state.get("total_steps", 0),
        done=session["done"],
        # report goes out ONLY on the turn it is generated — follow-up chat
        # answers must not force the UI back to the report view
        report=state.get("report") if (state.get("report") and not had_report) else None,
        profile=session["profile"],
        language=session["profile"].get("language") or "en",
        input_type=state.get("input_type", "text"),
    )


@router.get("/api/report/{session_id}")
def get_report(session_id: str):
    session = get_session(session_id)
    if not session or not session.get("report"):
        raise HTTPException(status_code=404, detail="Report not found. Complete the questionnaire first.")
    return session["report"]


@router.get("/api/report/{session_id}/html", response_class=HTMLResponse)
def get_report_html(session_id: str, lang: str = ""):
    session = get_session(session_id)
    if not session or not session.get("report"):
        raise HTTPException(status_code=404, detail="Report not found.")
    language = lang or (session["profile"].get("language") or "en")
    return HTMLResponse(render_html_report(session["report"], language))


# ---------------------------------------------------------------------------
# Data & metadata
# ---------------------------------------------------------------------------


@router.get("/api/schemes")
def list_schemes():
    return [
        {
            "id": s["id"],
            "name_en": s["name_en"],
            "name_hi": s["name_hi"],
            "category_en": s["category_en"],
            "category_hi": s["category_hi"],
            "benefit_en": s["benefit_en"],
            "benefit_hi": s["benefit_hi"],
            "apply_url": s["apply_url"],
            "n_rules": sum(len(g.get("rules", [])) for g in s.get("rule_groups", [])),
        }
        for s in load_schemes()
    ]


@router.get("/api/meta", response_model=MetaResponse)
def meta():
    return MetaResponse(
        total_schemes=len(load_schemes()),
        langgraph=HAS_LANGGRAPH,
        llm_enabled=config.LLM_ENABLED,
        personas=demo_runner.persona_meta(),
    )


# ---------------------------------------------------------------------------
# Demo personas (zero-risk live demo)
# ---------------------------------------------------------------------------


@router.post("/api/demo/{persona_id}")
def run_demo(persona_id: str):
    session = create_session()
    try:
        result = demo_runner.run_persona(persona_id, session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"session_id": session["id"], **result}
