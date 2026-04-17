from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SessionJudgeAnswer(BaseModel):
    text: str


class SessionJudgeRequest(BaseModel):
    session_id: str
    puzzle_type: str
    answer: SessionJudgeAnswer
    events: List[Dict[str, Any]] = Field(default_factory=list)


class JudgeResponse(BaseModel):
    is_human: bool
    module: str
    passed: bool


class GeneratePuzzleResponse(BaseModel):
    session_id: str
    puzzle_type: str
    puzzle_config: Dict[str, Any]
