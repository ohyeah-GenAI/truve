from datetime import datetime

from pydantic import BaseModel


class QAPair(BaseModel):
    id: int
    receipt_id: str
    question: str
    answer: str
    order: int = 1
    created_at: datetime | None = None


class QuestionOnly(BaseModel):
    id: int
    receipt_id: str
    question: str
    order: int = 1


class CaptchaResponse(BaseModel):
    receipt_id: str
    receipt_type: str | None
    image_data: str | None
    question_id: int
    question: str


class AnswerSubmit(BaseModel):
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
