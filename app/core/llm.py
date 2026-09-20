"""
Gemini integration — enhancement layer, never a single point of failure.

Every public function returns None on ANY problem (no key, network down,
rate limited, weird response) so callers silently fall back to the
deterministic template output. The demo can never be bricked by the LLM.
"""

from __future__ import annotations

from typing import Optional

from . import config

_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def _generate(prompt: str, max_tokens: int = 512) -> Optional[str]:
    if not config.LLM_ENABLED:
        return None
    try:
        import httpx

        url = _API.format(model=config.GEMINI_MODEL, key=config.GEMINI_API_KEY)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": max_tokens},
        }
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


def polish_summary(profile: dict, report: dict, language: str) -> Optional[str]:
    """A warm, personal 3-4 line summary of the report in the user's language."""
    top = [c["name_en"].split(" (")[0] for c in (report.get("eligible") or [])[:4]]
    near = [c["name_en"].split(" (")[0] for c in (report.get("near_miss") or [])[:3]]
    lang_name = "Hindi (Devanagari)" if language == "hi" else "English"
    prompt = (
        f"You are Scheme Saathi, a warm Indian government-schemes assistant. "
        f"Write a friendly 3-4 sentence summary in {lang_name} for this user. "
        f"Sound encouraging and human, use the name, no markdown headers, max 2 emojis.\n\n"
        f"Name: {profile.get('name')}\n"
        f"Profile: age {profile.get('age')}, {profile.get('gender')}, {profile.get('occupation')}, "
        f"{profile.get('area_type')} {profile.get('state')}, income Rs {profile.get('annual_income')}, "
        f"category {str(profile.get('category', '')).upper()}\n"
        f"Fully eligible for {report.get('n_eligible')} schemes. Top: {', '.join(top) or 'none'}.\n"
        f"Near-miss for {report.get('n_near_miss')} more: {', '.join(near) or 'none'}.\n"
        f"Mention that full details, documents and apply links are shown below."
    )
    return _generate(prompt)


def explain_doubt(doubt: str, question: dict, profile: dict, language: str) -> Optional[str]:
    """Explain the CURRENT intake question in the user's own words.

    Grounded in the question's curated help text so Gemini can never invent
    scheme rules — it only rephrases/exemplifies what we already know is right.
    Returns None when LLM is off → caller falls back to the template help text.
    """
    lang_name = "Hindi (Devanagari)" if language == "hi" else "English"
    q_text = question.get("text_hi" if language == "hi" else "text_en") or question.get("text_en", "")
    q_help = question.get("help_hi" if language == "hi" else "help_en") or question.get("help_en", "")
    opts = ", ".join(str(o.get("label_en", "")) for o in (question.get("options") or [])[:8])
    prompt = (
        f"You are Scheme Saathi, a kind Indian government-schemes assistant talking to a "
        f"{profile.get('age', 'adult')}-year-old {profile.get('occupation', 'person')} who may "
        f"have never used a chatbot. They are stuck on a question and asked a doubt.\n\n"
        f"THE QUESTION THEY'RE STUCK ON: {q_text}\n"
        f"OFFICIAL EXPLANATION (ground truth — do NOT contradict it): {q_help}\n"
        f"ANSWER CHOICES THEY CAN PICK: {opts or 'free text'}\n"
        f"THEIR DOUBT: {doubt}\n\n"
        f"Reply in {lang_name}, <=70 words, warm and reassuring (start with something like "
        f"'Koi baat nahi!' / 'No worries!'), explain in the SIMPLEST everyday words with one "
        f"relatable example, and end by telling them exactly how to answer (tap a button / type it). "
        f"Plain text, no markdown, no headers. Do not invent scheme rules beyond the explanation above."
    )
    return _generate(prompt, max_tokens=256)


def answer_followup(question: str, profile: dict, report: dict, language: str) -> Optional[str]:
    """Answer a free-text question about the user's report, grounded in the data."""
    if not question.strip() or not report:
        return None
    lang_name = "Hindi (Devanagari)" if language == "hi" else "English"
    cards = []
    for c in (report.get("eligible") or [])[:6]:
        cards.append(
            f"- {c['name_en']} | benefit: {c['benefit_en']} | apply: {c['apply_url']} | "
            f"docs: {', '.join(c['documents_en'][:4])} | why eligible: {'; '.join(c['reasons_en'][:3])}"
        )
    for c in (report.get("near_miss") or [])[:4]:
        cards.append(
            f"- NEAR MISS {c['name_en']} | gap: {'; '.join(c['gaps_en'] or c['reasons_en'][:1])} | "
            f"tip: {'; '.join(c['tips_en'][:2])}"
        )
    prompt = (
        f"You are Scheme Saathi. Answer the user's question in {lang_name}, in <=120 words, "
        f"plain text with simple dashes for lists, grounded ONLY in this report data. "
        f"If the answer is not in the data, say so honestly and point to official portals.\n\n"
        f"USER PROFILE: {profile.get('name')}, {profile.get('age')}, {profile.get('occupation')}, "
        f"{profile.get('state')}\nREPORT:\n" + "\n".join(cards) +
        f"\n\nUSER QUESTION: {question}"
    )
    return _generate(prompt)
