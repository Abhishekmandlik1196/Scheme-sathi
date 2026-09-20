"""
Adaptive conversational intake engine.

Walks the QUESTIONS list in order, skipping questions whose ask_if(profile)
fails (that's the adaptivity judges love: farmers get land questions,
entrepreneurs get business questions, students get education questions).
Parses messy real-world answers ("1.5 lakh", "haan", "2", "UP") into values.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .prompts import QUESTIONS

DEVANAGARI = re.compile(r"[ऀ-ॿ]")

YES_WORDS = {"yes", "y", "haan", "ha", "han", "hanji", "haanji", "हाँ", "हां", "हा", "जी", "true", "1"}
NO_WORDS = {"no", "n", "nahi", "nahin", "na", "नहीं", "ना", "न", "false", "0"}


def detect_language(text: str) -> str:
    """Devanagari anywhere in the message => Hindi, else English."""
    return "hi" if DEVANAGARI.search(text or "") else "en"


def get_question(qid: str) -> Optional[dict]:
    return next((q for q in QUESTIONS if q["id"] == qid), None)


def next_question(profile: dict) -> Optional[dict]:
    """First question (in order) that applies to this profile and is unanswered."""
    for q in QUESTIONS:
        ask_if = q.get("ask_if")
        if ask_if and not ask_if(profile):
            continue
        field = q.get("field", q["id"])
        if profile.get(field) is None:
            return q
    return None


def pending_question_ids(profile: dict) -> list[str]:
    return [
        (q.get("field", q["id"]))
        for q in QUESTIONS
        if (not q.get("ask_if") or q["ask_if"](profile)) and profile.get(q.get("field", q["id"])) is None
    ]


def questions_total_for(profile: dict) -> int:
    return sum(1 for q in QUESTIONS if (not q.get("ask_if") or q["ask_if"](profile)))


# ---------------------------------------------------------------------------
# "Ask anytime" help detection
# ---------------------------------------------------------------------------


def looks_like_help(message: str) -> str:
    """Is this message a doubt/help request instead of an answer?

    Returns:
      'general'  — generic cry for help ("help", "madad", "??")
      'question' — the user is confused by/asking about the current question
                   ("BPL kya hai?", "nahi pata", "samajh nahi aaya", "?")
      ''         — a genuine answer attempt; parse it normally

    Deliberately conservative about real answers: plain "nahi"/"na"/"haan"
    and everything the parsers understand must NOT be treated as help.
    """
    from .prompts import GENERAL_HELP_WORDS, QUESTION_PHRASES, QUESTION_TOKENS

    t = (message or "").strip().lower()
    if not t:
        return ""
    if t in GENERAL_HELP_WORDS:
        return "general"
    # strong phrase signals (checked before tokens so "nahi pata" wins)
    for phrase in QUESTION_PHRASES:
        if phrase in t:
            return "question"
    # whole-word question tokens (kya, kyu, matlab, help, why, how, ...)
    tokens = set(re.findall(r"\w+", t, re.UNICODE))
    if tokens & QUESTION_TOKENS:
        return "question"
    return ""


def help_text_for(q: dict, language: str) -> str:
    return q.get("help_hi" if language == "hi" else "help_en") or q.get("help_en") or ""


# ---------------------------------------------------------------------------
# Answer parsing
# ---------------------------------------------------------------------------


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def _parse_number(text: str) -> Optional[float]:
    """Extract a number; supports 'lakh', 'lac', 'k', decimal inputs."""
    t = _norm(text).replace(",", "")
    m = re.search(r"(-?\d+(?:\.\d+)?)", t)
    if not m:
        return None
    val = float(m.group(1))
    if "lakh" in t or "lac" in t or "लाख" in t:
        val *= 100000
    elif re.search(r"\d\s?k\b", t):
        val *= 1000
    return val


def visible_options(q: dict, profile: Optional[dict] = None) -> list[dict]:
    """Options after per-option visibility guards — what THIS user should see.

    Rendering and parsing MUST both use this list so numeric answers ("1, 3")
    always map to the buttons actually on screen. profile=None (unknown user)
    means: show everything (used by offline tooling/tests).
    """
    opts = q.get("options") or []
    if profile is None:
        return list(opts)
    return [o for o in opts if not o.get("show_if") or o["show_if"](profile)]


def _match_option(q: dict, token: str, profile: Optional[dict] = None):
    """Match a token against option values, labels (en/hi) or its 1-based index."""
    opts = visible_options(q, profile)
    token = token.strip()
    tn = token.lower()
    if tn.isdigit():
        idx = int(tn) - 1
        if 0 <= idx < len(opts):
            return opts[idx]
    for opt in opts:
        if tn == str(opt["value"]).lower():
            return opt
        if tn in (str(opt.get("label_en", "")).lower(), str(opt.get("label_hi", "")).lower()):
            return opt
    # partial label match (e.g. "female" inside "👧 female")
    for opt in opts:
        if str(opt["value"]).lower() != "none" and tn and (
            tn in str(opt.get("label_en", "")).lower() or tn in str(opt.get("label_hi", ""))
        ):
            return opt
    return None


def parse_answer(q: dict, text: str, profile: Optional[dict] = None) -> tuple[bool, Any]:
    """Parse a raw user message for question q.

    Returns (ok, value). On ok=False, value is None and the caller re-asks.
    `profile` must be the current profile so option indexes match the
    filtered list the user actually saw.
    """
    qtype = q["type"]
    t = (text or "").strip()
    if not t:
        return False, None

    if qtype == "text":
        opt = _match_option(q, t, profile)
        if opt:
            return True, opt["value"]
        # keep it short & clean
        return True, re.sub(r"\s+", " ", t)[:60]

    if qtype in ("int", "float"):
        # 1) EXACT option match only (quick-reply clicks send the full label)
        for opt in q.get("options") or []:
            if t.lower() in (
                str(opt["value"]).lower(),
                str(opt.get("label_en", "")).lower(),
                str(opt.get("label_hi", "")).lower(),
            ):
                v = opt["value"]
                return (True, int(v) if qtype == "int" else float(v))
        # 2) literal number (supports "1.5 lakh", "250k", Devanagari text)
        num = _parse_number(t)
        if num is None:
            return False, None
        return (True, int(num) if qtype == "int" else float(num))

    if qtype == "choice":
        opt = _match_option(q, t, profile)
        if opt:
            return True, opt["value"]
        # Hindi free-text guesses for a few common cases
        guesses = {
            "पुरुष": "male", "महिला": "female", "आदमी": "male", "औरत": "female",
            "गाँव": "rural", "गांव": "rural", "शहर": "urban", "किसान": "farmer",
            "छात्र": "student", "व्यापार": "business", "नौकरी": "employee",
        }
        if t in guesses:
            return True, guesses[t]
        return False, None

    if qtype == "yesno":
        tn = _norm(t).rstrip(".!")
        if tn in YES_WORDS:
            return True, True
        if tn in NO_WORDS:
            return True, False
        # combined quick-reply labels, e.g. "हाँ / Yes" — check every part
        parts = [p.strip() for p in re.split(r"[/|•,؛]", tn) if p.strip()]
        if parts and any(p in YES_WORDS for p in parts):
            return True, True
        if parts and any(p in NO_WORDS for p in parts):
            return True, False
        opt = _match_option(q, t, profile)
        if opt:
            return True, bool(opt["value"])
        return False, None

    if qtype == "multichoice":
        values: list[Any] = []
        for token in re.split(r"[,;/और]| and ", t):
            token = token.strip()
            if not token:
                continue
            opt = _match_option(q, token, profile)
            if opt:
                if opt["value"] == "none":
                    return True, []
                if opt["value"] not in values:
                    values.append(opt["value"])
        if values or _norm(t) in {"none", "no", "nahi", "नहीं", "कोई नहीं"}:
            return True, values
        return False, None

    return False, None


# ---------------------------------------------------------------------------
# Question rendering
# ---------------------------------------------------------------------------


def render_question(q: dict, profile: dict, language: str) -> str:
    key = "text_hi" if language == "hi" else "text_en"
    text = q.get(key) or q["text_en"]
    return text.replace("{name}", str(profile.get("name") or "")).strip()


def render_options(q: dict, language: str, profile: Optional[dict] = None) -> list[dict]:
    opts = []
    for i, opt in enumerate(visible_options(q, profile), 1):
        opts.append({
            "value": opt["value"],
            "label": opt.get("label_hi" if language == "hi" else "label_en") or opt.get("label_en"),
            "index": i,
        })
    if q["type"] == "yesno" and not opts:
        opts = [
            {"value": True, "label": "हाँ / Yes" if language == "hi" else "Yes", "index": 1},
            {"value": False, "label": "नहीं / No" if language == "hi" else "No", "index": 2},
        ]
    return opts
