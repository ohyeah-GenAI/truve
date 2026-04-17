from __future__ import annotations

from typing import Any, Dict
import uuid

_SESSIONS: Dict[str, Dict[str, Any]] = {}


def create_session(receipt_id: str, question_id: int, expected_answer: str) -> str:
    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {
        "session_id": session_id,
        "puzzle_type": "vqa-image",
        "receipt_id": receipt_id,
        "question_id": question_id,
        "expected_answer": expected_answer,
    }
    return session_id


def pop_session(session_id: str) -> Dict[str, Any] | None:
    return _SESSIONS.pop(session_id, None)
