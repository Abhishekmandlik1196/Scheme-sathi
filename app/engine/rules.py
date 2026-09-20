"""
Rule evaluation primitives for the Scheme Saathi eligibility engine.

Every scheme's eligibility is data-driven (see data/schemes.json). A scheme has
rule_groups; each group has logic 'all' (every rule must pass) or 'any'
(at least one rule must pass). Each rule references a field of the user
profile and an operator.

This module is deliberately dependency-free and deterministic — the same
logic runs in tests, in the API, and in front of the judges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Formatting helpers (Indian conventions)
# ---------------------------------------------------------------------------


def inr(amount: float) -> str:
    """Format a number as Indian Rupees: 100000 -> '₹1,00,000'."""
    n = int(round(amount))
    s = str(abs(n))
    if len(s) <= 3:
        grouped = s
    else:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        grouped = ",".join(parts + [tail])
    sign = "-" if n < 0 else ""
    return f"{sign}₹{grouped}"


def fmt_value(value: Any, unit: Optional[str] = None) -> str:
    """Human-friendly rendering of a value for explanations."""
    if value is None:
        return "—"
    if unit == "inr":
        try:
            return inr(float(value))
        except (TypeError, ValueError):
            return str(value)
    if unit == "hectares":
        try:
            return f"{float(value):g}"
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, list):
        return "–".join(str(v) for v in value)
    return str(value)


# ---------------------------------------------------------------------------
# Operator semantics
# ---------------------------------------------------------------------------


def _to_number(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_op(op: str, current: Any, expected: Any) -> bool:
    """Pure operator evaluation. Missing current values fail safely."""
    if op == "eq":
        return current == expected
    if op == "neq":
        return current != expected
    if op == "in":
        return current in (expected or [])
    if op == "not_in":
        return current not in (expected or [])
    if op == "contains":
        # profile field is a list; expected must be present in it
        return isinstance(current, (list, tuple, set)) and expected in current
    if op == "is_true":
        return current is True
    if op == "is_false":
        return current is False
    if op in ("lt", "lte", "gt", "gte"):
        cur = _to_number(current)
        exp = _to_number(expected)
        if cur is None or exp is None:
            return False
        if op == "lt":
            return cur < exp
        if op == "lte":
            return cur <= exp
        if op == "gt":
            return cur > exp
        return cur >= exp
    if op == "between":
        cur = _to_number(current)
        if cur is None or not isinstance(expected, (list, tuple)) or len(expected) != 2:
            return False
        lo, hi = _to_number(expected[0]), _to_number(expected[1])
        return lo is not None and hi is not None and lo <= cur <= hi
    raise ValueError(f"Unknown operator: {op}")


# ---------------------------------------------------------------------------
# Rule / group evaluation with explanation + gap analysis data
# ---------------------------------------------------------------------------


@dataclass
class RuleResult:
    rule: dict
    passed: bool
    current: Any = None
    # numeric gap info (only when failed on a numeric rule)
    required: Optional[float] = None
    diff: Optional[float] = None
    bound_label: str = ""  # "≤ 300000" style


@dataclass
class GroupResult:
    logic: str
    passed: bool
    rule_results: list = field(default_factory=list)


def _numeric_gap(rule: dict, current: Any) -> tuple[Optional[float], Optional[float], str]:
    """Return (required, diff, bound_label) for failed numeric rules."""
    op, cur = rule.get("op"), _to_number(current)
    if cur is None:
        return None, None, ""
    unit = rule.get("unit")
    if op == "lte":
        req = _to_number(rule.get("value"))
        if req is not None and cur > req:
            return req, cur - req, f"≤ {fmt_value(req, unit)}"
    if op == "gte":
        req = _to_number(rule.get("value"))
        if req is not None and cur < req:
            return req, req - cur, f"≥ {fmt_value(req, unit)}"
    if op == "between":
        val = rule.get("value") or []
        if len(val) == 2:
            lo, hi = _to_number(val[0]), _to_number(val[1])
            if lo is not None and cur < lo:
                return lo, lo - cur, f"≥ {fmt_value(lo, unit)}"
            if hi is not None and cur > hi:
                return hi, cur - hi, f"≤ {fmt_value(hi, unit)}"
    return None, None, ""


def evaluate_rule(rule: dict, profile: dict) -> RuleResult:
    field_name = rule.get("field")
    current = profile.get(field_name)
    passed = evaluate_op(rule.get("op"), current, rule.get("value"))
    result = RuleResult(rule=rule, passed=passed, current=current)
    if not passed:
        req, diff, bound = _numeric_gap(rule, current)
        result.required, result.diff, result.bound_label = req, diff, bound
    return result


def evaluate_group(group: dict, profile: dict) -> GroupResult:
    logic = group.get("logic", "all")
    results = [evaluate_rule(r, profile) for r in group.get("rules", [])]
    if logic == "any":
        passed = any(r.passed for r in results)
    else:
        passed = all(r.passed for r in results)
    return GroupResult(logic=logic, passed=passed, rule_results=results)
