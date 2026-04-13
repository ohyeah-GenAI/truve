from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.modules.qa.router import router as qa_router
from src.modules.receipts.router import router as receipts_router

class HealthResponse(BaseModel):
    status: str

class JudgeRequest(BaseModel):
    problem_id: str
    user_answer: str

class JudgeResponse(BaseModel):
    is_human: bool
    module: str
    passed: bool

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
def judge(request: JudgeRequest):
    """
    내부 봇 판별 (단일 엔드포인트) - ModuleController에서 호출됨
    """
    # TODO: 실제 영수증 정답 검증 로직 연결 (현재는 dummy 반환)
    # response example: is_human=True, module="receipt", passed=True
    return JudgeResponse(
        is_human=True,
        module="receipt",
        passed=True
    )
