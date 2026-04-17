from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.modules.qa import service as qa_service
from src.modules.qa.router import router as qa_router
from src.modules.receipts import service as receipts_service
from src.modules.receipts.router import router as receipts_router
from src.schemas import GeneratePuzzleResponse, JudgeResponse, SessionJudgeRequest


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


@app.get("/api/puzzle/generate", response_model=GeneratePuzzleResponse)
def generate_puzzle(
    type: str = Query(..., alias="type"),
    db: Session = Depends(get_db),
):
    if type != "vqa-image":
        raise HTTPException(status_code=400, detail=f"Unsupported puzzle type: {type}")

    puzzle = receipts_service.generate_challenge_puzzle(db)
    if not puzzle:
        raise HTTPException(status_code=404, detail="영수증 또는 질문을 찾을 수 없습니다.")
    return GeneratePuzzleResponse(**puzzle)


@app.post("/judge", tags=["AI Verification"], response_model=JudgeResponse)
def judge(request: SessionJudgeRequest):
    """
    내부 봇 판별 엔드포인트 - ModuleController에서 호출됨.
    """
    passed = qa_service.verify_session_answer(request.session_id, request.answer.text)
    return JudgeResponse(is_human=passed, module="vqa-image", passed=passed)
