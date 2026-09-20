"""Shared state for the Scheme Saathi conversation graph."""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class GraphState(TypedDict, total=False):
    # inputs
    message: str
    profile: dict
    current_qid: Optional[str]

    # carry-over
    language: str

    # outputs
    bot_messages: list[str]
    quick_replies: list[dict]
    input_type: str
    step: int
    total_steps: int
    ready_to_report: bool
    done: bool
    report: Optional[dict]
    next_qid: Optional[str]
