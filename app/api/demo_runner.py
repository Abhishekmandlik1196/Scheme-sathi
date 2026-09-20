"""
Demo-persona runner — instant, zero-risk live demos.

Feeds a pre-built persona's answers through the REAL intake + engine pipeline
(same parsers, same rules as a live user) and returns the full transcript +
report. Judges see realistic output instantly; no maps, no fakes, no typos —
and no demo-day stage fright.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from ..agents import intake as intake_mod
from ..agents.prompts import DONE_EN, DONE_HI, PROFILE_NOTE_EN, PROFILE_NOTE_HI, WELCOME_EN, WELCOME_HI
from ..core import llm
from ..engine.reasoner import build_report

_PERSONAS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "demo", "personas.json")

_persona_cache: Optional[list] = None


def load_personas() -> list[dict]:
    global _persona_cache
    if _persona_cache is None:
        with open(_PERSONAS_PATH, encoding="utf-8") as f:
            _persona_cache = json.load(f)
    return _persona_cache


def persona_meta() -> list[dict]:
    return [
        {
            "id": p["id"],
            "title_en": p["title_en"],
            "title_hi": p["title_hi"],
            "blurb_en": p["blurb_en"],
            "blurb_hi": p["blurb_hi"],
        }
        for p in load_personas()
    ]


def run_persona(persona_id: str, session: dict) -> dict:
    persona = next((p for p in load_personas() if p["id"] == persona_id), None)
    if not persona:
        raise ValueError(f"Unknown persona: {persona_id}")

    profile: dict = {}
    transcript: list[dict] = [{"sender": "bot", "text": WELCOME_EN + "\n---\n" + WELCOME_HI}]

    q = intake_mod.get_question("language")
    while q:
        lang = profile.get("language") or "en"
        transcript.append({"sender": "bot", "text": intake_mod.render_question(q, profile, lang)})

        raw = persona["answers"].get(q["id"])
        if raw is None:
            raise ValueError(f"Persona '{persona_id}' is missing an answer for '{q['id']}'")
        transcript.append({"sender": "user", "text": raw})

        ok, value = intake_mod.parse_answer(q, raw, profile)
        if not ok:
            raise ValueError(f"Persona '{persona_id}' answer for '{q['id']}' did not parse: {raw!r}")

        field = q.get("field", q["id"])
        profile[field] = value
        if q["id"] == "language":
            profile["language"] = value
            lang = value
        if q["id"] == "occupation":
            note = (PROFILE_NOTE_HI if profile.get("language") == "hi" else PROFILE_NOTE_EN).get(value)
            if note:
                transcript.append({"sender": "bot", "text": note})

        q = intake_mod.next_question(profile)

    report = build_report(profile)
    lang = profile.get("language") or "en"
    polished = llm.polish_summary(profile, report, lang)
    if polished:
        report["summary_llm"] = polished

    done_tmpl = DONE_HI if lang == "hi" else DONE_EN
    transcript.append({
        "sender": "bot",
        "text": done_tmpl.format(name=profile.get("name", ""), total=report["n_checked"]),
    })

    session["profile"] = profile
    session["current_qid"] = None
    session["done"] = True
    session["report"] = report
    session["history"] = transcript

    return {"transcript": transcript, "report": report, "persona": persona["title_en"]}
