"""
Scheme ranker: orders eligible schemes by how valuable & relevant they are
to THIS user — not alphabetically, not randomly.

Score (0..100) = weighted blend of:
  benefit_amount   (35%) — bigger benefit matters more (log-ish cap at ₹2 lakh)
  criteria_match   (30%) — share of the scheme's criteria the user satisfies
  occupation_fit   (25%) — scheme is designed for the user's occupation
  popularity       (10%) — well-known, easy-to-apply schemes get a small boost
"""

from __future__ import annotations

BENEFIT_CAP = 200000  # benefit at/above this counts as max
W_BENEFIT, W_CRITERIA, W_OCCUPATION, W_POPULARITY = 0.35, 0.30, 0.25, 0.10


def _benefit_score(amount: float) -> float:
    try:
        return max(0.0, min(float(amount) / BENEFIT_CAP, 1.0))
    except (TypeError, ValueError):
        return 0.0


def _occupation_score(scheme: dict, occupation: str | None) -> float:
    rel = scheme.get("occupation_relevance") or {}
    if not occupation:
        return 0.3  # neutral when unknown
    if not rel:
        return 0.5  # universal schemes (insurance, pension, health) suit everyone
    return float(rel.get(occupation, 0.1))


def score_match(match_result: dict, profile: dict) -> float:
    scheme = match_result["scheme"]
    s = (
        W_BENEFIT * _benefit_score(scheme.get("benefit_amount", 0))
        + W_CRITERIA * match_result.get("match_ratio", 0.0)
        + W_OCCUPATION * _occupation_score(scheme, profile.get("occupation"))
        + W_POPULARITY * min((scheme.get("popularity", 5)) / 10.0, 1.0)
    )
    return round(s * 100)


def rank_matches(matches: list[dict], profile: dict) -> list[dict]:
    """Attach match_percent + score_breakdown and sort best-first."""
    for m in matches:
        scheme = m["scheme"]
        m["score_breakdown"] = {
            "benefit": round(_benefit_score(scheme.get("benefit_amount", 0)) * 100),
            "criteria": round(m.get("match_ratio", 0.0) * 100),
            "occupation_fit": round(_occupation_score(scheme, profile.get("occupation")) * 100),
            "popularity": round(min((scheme.get("popularity", 5)) / 10.0, 1.0) * 100),
        }
        m["match_percent"] = score_match(m, profile)
    matches.sort(key=lambda m: m["match_percent"], reverse=True)
    return matches
