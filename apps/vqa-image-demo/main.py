from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.modules.qa import service as qa_service
from src.modules.qa.router import router as qa_router
from src.modules.receipts.router import router as receipts_router
from src.schemas import JudgeRequest, JudgeResponse


class HealthResponse(BaseModel):
    status: str


app = FastAPI(
    title="Receipt CAPTCHA API",
    description="영수증 캡챠 서비스 - 영수증 이미지와 Q&A 제공",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts_router, prefix="/api/v1")
app.include_router(qa_router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}


@app.get("/internal/ai/health", tags=["Health"], response_model=HealthResponse)
def ai_health_check():
    """AI health check internal endpoint"""
    return {"status": "ok"}


@app.post("/judge", tags=["AI Verification"], response_model=JudgeResponse)
def judge(request: JudgeRequest, db: Session = Depends(get_db)):
    """
    내부 봇 판별 엔드포인트 - ModuleController에서 호출됨.
    problem_id는 qa_pairs 테이블의 question_id(int)에 해당.
    """
    try:
        question_id = int(request.problem_id)
    except (ValueError, TypeError):
        return JudgeResponse(is_human=False, module="receipt", passed=False)

    passed = qa_service.verify_single_answer(db, question_id, request.user_answer)
    return JudgeResponse(is_human=passed, module="receipt", passed=passed)
