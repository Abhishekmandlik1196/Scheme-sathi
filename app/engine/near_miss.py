"""
Near-miss gap analysis — the feature most teams skip and judges remember.

For every almost-eligible scheme we produce:
  1. What exactly failed (plain language, user's numbers vs the requirement)
  2. The precise gap ("your income is ₹4,00,000, the limit is ₹3,00,000 — ₹1,00,000 over")
  3. An actionable tip to become eligible or an adjacent scheme to try
"""

from __future__ import annotations


def _gap_sentence_en(gap: dict) -> str:
    if not gap:
        return ""
    label = gap.get("label_en", "value")
    return (
        f"Your {label} is {gap['current_fmt']}, the limit is "
        f"{gap['bound_label'] or gap['required_fmt']} — a gap of {gap['diff_fmt']}"
    )


def _gap_sentence_hi(gap: dict) -> str:
    if not gap:
        return ""
    label = gap.get("label_hi", "मान")
    return (
        f"आपका/आपकी {label} {gap['current_fmt']} है, सीमा "
        f"{gap['bound_label'] or gap['required_fmt']} है — {gap['diff_fmt']} का अंतर"
    )


def near_miss_analysis(match_result: dict) -> dict:
    """Given a match result with status near_miss, build bilingual gap analysis."""
    gaps_en, gaps_hi, reasons_en, reasons_hi, tips_en, tips_hi = [], [], [], [], [], []

    for f in match_result.get("failed", []):
        reasons_en.extend(f.get("desc_en", []))
        reasons_hi.extend(f.get("desc_hi", []))
        tips_en.extend(f.get("tips_en", []))
        tips_hi.extend(f.get("tips_hi", []))
        gap = f.get("gap")
        if gap:
            gaps_en.append(_gap_sentence_en(gap))
            gaps_hi.append(_gap_sentence_hi(gap))

    return {
        "reasons_en": reasons_en,
        "reasons_hi": reasons_hi,
        "gaps_en": [g for g in gaps_en if g],
        "gaps_hi": [g for g in gaps_hi if g],
        "tips_en": tips_en,
        "tips_hi": tips_hi,
    }


def failed_reasons_summary(match_result: dict) -> dict:
    """For not-eligible schemes: short bilingual list of why not (kept for detail view)."""
    reasons_en, reasons_hi = [], []
    for f in match_result.get("failed", []):
        reasons_en.extend(f.get("desc_en", []))
        reasons_hi.extend(f.get("desc_hi", []))
    return {"reasons_en": reasons_en, "reasons_hi": reasons_hi}
