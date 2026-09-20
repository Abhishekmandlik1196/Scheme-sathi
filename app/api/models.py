"""Pydantic request/response models for the API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    messages: list[str]
    quick_replies: list[dict] = []
    step: int = 0
    total_steps: int = 0
    done: bool = False
    report: Optional[dict] = None
    profile: dict = {}
    language: str = "en"
    input_type: str = "text"


class SessionResponse(BaseModel):
    session_id: str
    messages: list[str]
    quick_replies: list[dict]
    step: int = 0
    total_steps: int = 0
    done: bool = False


class MetaResponse(BaseModel):
    total_schemes: int
    langgraph: bool
    llm_enabled: bool
    personas: list[dict] = []
