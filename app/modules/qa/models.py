from pydantic import BaseModel
from datetime import datetime


class QAPair(BaseModel):
    id: int
    receipt_id: str
    question: str
    answer: str
    order: int = 1
    created_at: datetime | None = None


class QuestionOnly(BaseModel):
    """프론트엔드에 질문만 노출 (정답 숨김)"""
    id: int
    receipt_id: str
    question: str
    order: int = 1


class AnswerSubmit(BaseModel):
    """사용자가 제출하는 답변"""
    question_id: int
    answer: str


class VerifyRequest(BaseModel):
    answers: list[AnswerSubmit]


class VerifyResult(BaseModel):
    question_id: int
    correct: bool
    expected: str
    submitted: str


class VerifyResponse(BaseModel):
    receipt_id: str
    total: int
    correct_count: int
    passed: bool
    results: list[VerifyResult]
