from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.receipts.router import router as receipts_router
from app.modules.qa.router import router as qa_router

app = FastAPI(
    title="Receipt CAPTCHA API",
    description="영수증 캡챠 서비스 - 영수증 이미지와 Q&A 제공",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트엔드 연동 후 도메인으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts_router, prefix="/api/v1")
app.include_router(qa_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
