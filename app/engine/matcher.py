"""
Eligibility matcher: runs a completed user profile against every scheme's
rule groups and classifies each scheme as eligible / near_miss / not_eligible.

Output is fully explainable: every matched and failed criterion is carried
through with bilingual descriptions so the UI (and judges) can see exactly
*why* a decision was made. No black box.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from .rules import evaluate_group, fmt_value

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes.json")

_scheme_cache: Optional[list] = None


def load_schemes() -> list[dict]:
    global _scheme_cache
    if _scheme_cache is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _scheme_cache = json.load(f)
    return _scheme_cache


def _interpolate(text: str, current, unit: Optional[str]) -> str:
    """Replace {current} placeholder in rule descriptions with the user value."""
    if not text:
        return ""
    if "{current}" in text:
        text = text.replace("{current}", fmt_value(current, unit))
    return text


def match_scheme(scheme: dict, profile: dict) -> dict:
    """Evaluate one scheme against the profile.

    Returns a dict with:
      status: 'eligible' | 'near_miss' | 'not_eligible'
      matched: [{desc_en, desc_hi}]          criteria the user satisfies
      failed:  [{rule_result-ish dict}]      criteria the user fails
      match_ratio: float 0..1                share of criteria satisfied
    """
    group_results = [evaluate_group(g, profile) for g in scheme.get("rule_groups", [])]

    matched: list[dict] = []
    failed: list[dict] = []
    total_rules = 0
    passed_rules = 0

    for gr in group_results:
        group_rule_results = gr.rule_results
        if gr.logic == "any":
            total_rules += 1  # an ANY-group counts as one composite criterion
            if gr.passed:
                passed_rules += 1
                # explain with each criterion that matched (usually exactly one)
                for rr in group_rule_results:
                    if rr.passed:
                        unit = rr.rule.get("unit")
                        matched.append({
                            "desc_en": _interpolate(rr.rule.get("desc_en", ""), rr.current, unit),
                            "desc_hi": _interpolate(rr.rule.get("desc_hi", ""), rr.current, unit),
                        })
            else:
                # composite failure: carry every option + its near-miss tip
                tips_en, tips_hi = [], []
                descs_en, descs_hi = [], []
                near_missable = False
                for rr in group_rule_results:
                    unit = rr.rule.get("unit")
                    descs_en.append(_interpolate(rr.rule.get("fail_en", ""), rr.current, unit))
                    descs_hi.append(_interpolate(rr.rule.get("fail_hi", ""), rr.current, unit))
                    nm = rr.rule.get("near_miss")
                    # fields that were never asked (not applicable to this user)
                    # must NOT create false near-misses
                    if nm and rr.current is not None:
                        near_missable = True
                        if nm.get("tip_en"):
                            tips_en.append(nm["tip_en"])
                        if nm.get("tip_hi"):
                            tips_hi.append(nm["tip_hi"])
                failed.append({
                    "composites": True,
                    "desc_en": descs_en,
                    "desc_hi": descs_hi,
                    "tips_en": tips_en,
                    "tips_hi": tips_hi,
                    "near_missable": near_missable,
                    "gap": None,
                })
        else:  # logic == 'all'
            for rr in group_rule_results:
                total_rules += 1
                unit = rr.rule.get("unit")
                if rr.passed:
                    passed_rules += 1
                    matched.append({
                        "desc_en": _interpolate(rr.rule.get("desc_en", ""), rr.current, unit),
                        "desc_hi": _interpolate(rr.rule.get("desc_hi", ""), rr.current, unit),
                    })
                else:
                    nm = rr.rule.get("near_miss") or {}
                    gap = None
                    # unanswered (not-applicable) fields fail hard, never as a near-miss
                    near_missable = bool(nm) and rr.current is not None
                    if rr.diff is not None and rr.required is not None:
                        max_gap = nm.get("max_gap")
                        gap = {
                            "label_en": rr.rule.get("label_en", rr.rule.get("field", "")),
                            "label_hi": rr.rule.get("label_hi", rr.rule.get("field", "")),
                            "current": rr.current,
                            "current_fmt": fmt_value(rr.current, unit),
                            "required": rr.required,
                            "required_fmt": fmt_value(rr.required, unit),
                            "diff": rr.diff,
                            "diff_fmt": fmt_value(rr.diff, unit),
                            "bound_label": rr.bound_label,
                            "unit": unit,
                        }
                        # numeric near-miss only counts if within the allowed window
                        if max_gap is not None:
                            near_missable = rr.diff <= max_gap
                    failed.append({
                        "composites": False,
                        "desc_en": [_interpolate(rr.rule.get("fail_en", ""), rr.current, unit)],
                        "desc_hi": [_interpolate(rr.rule.get("fail_hi", ""), rr.current, unit)],
                        "tips_en": [nm["tip_en"]] if nm.get("tip_en") else [],
                        "tips_hi": [nm["tip_hi"]] if nm.get("tip_hi") else [],
                        "near_missable": near_missable,
                        "gap": gap,
                    })

    if not failed:
        status = "eligible"
    elif len(failed) <= 2 and all(f.get("near_missable") for f in failed):
        # One (or two very soft) failures, all within reach => near miss
        status = "near_miss" if len(failed) == 1 else "not_eligible"
    else:
        status = "not_eligible"

    match_ratio = (passed_rules / total_rules) if total_rules else 0.0

    return {
        "scheme_id": scheme["id"],
        "status": status,
        "match_ratio": round(match_ratio, 3),
        "matched": matched,
        "failed": failed,
    }


def match_all_schemes(profile: dict, schemes: Optional[list] = None) -> dict:
    """Run the profile against every scheme; bucket by status."""
    schemes = schemes if schemes is not None else load_schemes()
    eligible, near_miss, not_eligible = [], [], []
    for scheme in schemes:
        result = match_scheme(scheme, profile)
        result["scheme"] = scheme
        if result["status"] == "eligible":
            eligible.append(result)
        elif result["status"] == "near_miss":
            near_miss.append(result)
        else:
            not_eligible.append(result)
    return {
        "eligible": eligible,
        "near_miss": near_miss,
        "not_eligible": not_eligible,
        "total": len(schemes),
    }
