from pydantic import BaseModel


class JudgeRequest(BaseModel):
    problem_id: str
    user_answer: str


class JudgeResponse(BaseModel):
    is_human: bool
    module: str
    passed: bool
