"""In-memory session management (hackathon-appropriate: restarts wipe state)."""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

_sessions: dict[str, dict[str, Any]] = {}
_TTL = 6 * 60 * 60  # 6 hours


def create_session() -> dict[str, Any]:
    sid = uuid.uuid4().hex[:12]
    session = {
        "id": sid,
        "created": time.time(),
        "profile": {},
        "current_qid": "language",
        "done": False,
        "report": None,
        "history": [],
    }
    _gc()
    _sessions[sid] = session
    return session


def get_session(sid: str) -> Optional[dict]:
    return _sessions.get(sid)


def _gc() -> None:
    now = time.time()
    for sid in [s for s, v in _sessions.items() if now - v["created"] > _TTL]:
        _sessions.pop(sid, None)
