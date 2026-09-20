"""
Reasoning & report engine.

Turns raw match results into a beautiful, fully-explained bilingual report:
  - eligible schemes ranked with match % and the exact criteria satisfied
  - near-miss section with precise gap analysis + actionable tips
  - summary paragraph (template-based by default; Gemini-polished if a key
    is configured — see app/core/llm.py, with graceful fallback)

Everything the UI renders comes from here as structured JSON.
"""

from __future__ import annotations

from .matcher import match_all_schemes
from .near_miss import near_miss_analysis, failed_reasons_summary
from .ranker import rank_matches


def _scheme_card(match: dict, rank: int) -> dict:
    """Build the render-ready card for one eligible scheme."""
    s = match["scheme"]
    return {
        "rank": rank,
        "scheme_id": s["id"],
        "status": "eligible",
        "match_percent": match["match_percent"],
        "score_breakdown": match.get("score_breakdown", {}),
        "name_en": s["name_en"],
        "name_hi": s["name_hi"],
        "category_en": s["category_en"],
        "category_hi": s["category_hi"],
        "ministry_en": s["ministry_en"],
        "ministry_hi": s["ministry_hi"],
        "description_en": s["description_en"],
        "description_hi": s["description_hi"],
        "benefit_en": s["benefit_en"],
        "benefit_hi": s["benefit_hi"],
        "apply_url": s["apply_url"],
        "apply_mode_en": s["apply_mode_en"],
        "apply_mode_hi": s["apply_mode_hi"],
        "documents_en": s["documents_en"],
        "documents_hi": s["documents_hi"],
        "reasons_en": [m["desc_en"] for m in match["matched"] if m.get("desc_en")],
        "reasons_hi": [m["desc_hi"] for m in match["matched"] if m.get("desc_hi")],
        "gaps_en": [],
        "gaps_hi": [],
        "tips_en": [],
        "tips_hi": [],
    }


def _near_miss_card(match: dict) -> dict:
    s = match["scheme"]
    nm = near_miss_analysis(match)
    return {
        "rank": None,
        "scheme_id": s["id"],
        "status": "near_miss",
        "match_percent": match.get("match_percent"),
        "name_en": s["name_en"],
        "name_hi": s["name_hi"],
        "category_en": s["category_en"],
        "category_hi": s["category_hi"],
        "description_en": s["description_en"],
        "description_hi": s["description_hi"],
        "benefit_en": s["benefit_en"],
        "benefit_hi": s["benefit_hi"],
        "apply_url": s["apply_url"],
        "reasons_en": nm["reasons_en"],
        "reasons_hi": nm["reasons_hi"],
        "gaps_en": nm["gaps_en"],
        "gaps_hi": nm["gaps_hi"],
        "tips_en": nm["tips_en"],
        "tips_hi": nm["tips_hi"],
        "documents_en": s["documents_en"],
        "documents_hi": s["documents_hi"],
    }


def _not_eligible_brief(match: dict) -> dict:
    s = match["scheme"]
    fr = failed_reasons_summary(match)
    return {
        "scheme_id": s["id"],
        "status": "not_eligible",
        "name_en": s["name_en"],
        "name_hi": s["name_hi"],
        "reasons_en": fr["reasons_en"][:2],
        "reasons_hi": fr["reasons_hi"][:2],
    }


def _template_summary(profile: dict, n_eligible: int, n_near: int, top: list[dict]) -> tuple[str, str]:
    name = profile.get("name") or ("दोस्त" if profile.get("language") == "hi" else "friend")
    top_names_en = ", ".join(c["name_en"].split(" (")[0] for c in top[:3])
    top_names_hi = ", ".join(c["name_hi"] for c in top[:3])
    en = (
        f"{name}, great news! Based on your profile you are fully eligible for "
        f"{n_eligible} government scheme{'s' if n_eligible != 1 else ''}"
        + (f" — top matches: {top_names_en}." if top else ".")
        + (
            f" You are also very close to {n_near} more — see the near-miss section for exact gaps and how to close them."
            if n_near
            else ""
        )
        + " All details, documents and apply links are below."
    )
    hi = (
        f"{name} जी, बधाई हो! आपकी प्रोफ़ाइल के अनुसार आप {n_eligible} सरकारी योजनाओं के लिए पूरी तरह पात्र हैं"
        + (f" — शीर्ष मैच: {top_names_hi}." if top else ".")
        + (
            f" आप {n_near} और योजनाओं के बहुत करीब हैं — नियर-मिस सेक्शन में सटीक अंतर और उसे पूरा करने का तरीका देखें।"
            if n_near
            else ""
        )
        + " सारा विवरण, दस्तावेज़ और आवेदन लिंक नीचे दिए गए हैं।"
    )
    return en, hi


def build_report(profile: dict) -> dict:
    """Full pipeline: match -> rank -> explain -> structured report."""
    results = match_all_schemes(profile)

    eligible_ranked = rank_matches(results["eligible"], profile)
    # near-misses ranked by how close (match_ratio) they are
    near = sorted(results["near_miss"], key=lambda m: m["match_ratio"], reverse=True)

    eligible_cards = [_scheme_card(m, i + 1) for i, m in enumerate(eligible_ranked)]
    near_cards = [_near_miss_card(m) for m in near]
    not_eligible = [_not_eligible_brief(m) for m in results["not_eligible"]]

    total_top_benefit = sum(
        (m["scheme"].get("benefit_amount") or 0) for m in eligible_ranked[:5]
    )

    summary_en, summary_hi = _template_summary(
        profile, len(eligible_cards), len(near_cards), eligible_cards
    )

    return {
        "profile": profile,
        "summary_en": summary_en,
        "summary_hi": summary_hi,
        "summary_llm": None,  # filled by graph layer if Gemini is configured
        "n_eligible": len(eligible_cards),
        "n_near_miss": len(near_cards),
        "n_checked": results["total"],
        "top_benefit_estimate": total_top_benefit,
        "eligible": eligible_cards,
        "near_miss": near_cards,
        "not_eligible": not_eligible,
    }
