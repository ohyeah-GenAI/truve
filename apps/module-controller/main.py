from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.proxy import (
    close_http_client,
    init_http_client,
    start_challenge,
    submit_judge,
    verify_challenge,
)
from src.redis_client import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await init_http_client()
    yield
    await close_http_client()
    await close_redis()


app = FastAPI(title="Module Controller", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 요청/응답 스키마
# ---------------------------------------------------------------------------


class ChallengeStartRequest(BaseModel):
    performance_id: str
    # TODO: 백엔드 답변 후 user_key 형태 확정 (현재: 단순 문자열)
    # 가능한 형태: JWT 토큰, queue_token, user_id
    user_key: str


class ChallengeStartResponse(BaseModel):
    flow_session_id: Optional[str] = None
    puzzle_type: Optional[str] = None
    puzzle_config: Optional[Dict[str, Any]] = None
    flow_complete: bool = False
    passed: Optional[bool] = None
    reason: Optional[str] = None


class JudgeRequest(BaseModel):
    flow_session_id: str
    answer: Dict[str, Any]
    events: Optional[List[Dict[str, Any]]] = []  # mouse-quiz 마우스 이벤트


class JudgeResponse(BaseModel):
    passed: bool
    flow_complete: bool
    blocked: bool = False          # 2차 실패 시 차단
    module: Optional[str] = None
    is_human: Optional[bool] = None
    next_puzzle_type: Optional[str] = None   # 다음 단계 or 재도전 퍼즐 공용
    next_puzzle_config: Optional[Dict[str, Any]] = None


class VerifyRequest(BaseModel):
    user_key: str
    performance_id: str


class VerifyResponse(BaseModel):
    passed: bool


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# 엔드포인트
# ---------------------------------------------------------------------------


@app.post("/challenge/start", response_model=ChallengeStartResponse)
async def challenge_start(req: ChallengeStartRequest) -> ChallengeStartResponse:
    """
    대기열 통과 후 챌린지 플로우 시작.

    performance_id로 보안 레벨을 조회하여 챌린지 순서를 결정하고
    첫 번째 퍼즐을 발급한다.

    TODO: 백엔드 연동 방식 확정 후 인증 검증 추가
    """
    result = await start_challenge(req.performance_id, req.user_key)
    return ChallengeStartResponse(**result)


@app.post("/challenge/judge", response_model=JudgeResponse)
async def challenge_judge(req: JudgeRequest) -> JudgeResponse:
    """
    현재 단계 답변 채점.

    - 실패: 플로우 종료
    - 통과 + 다음 단계 있음: 다음 퍼즐 반환
    - 전 단계 통과: flow_complete=True
    """
    result = await submit_judge(req.flow_session_id, req.answer, req.events)
    return JudgeResponse(**result)


@app.post("/challenge/verify", response_model=VerifyResponse)
async def challenge_verify(req: VerifyRequest) -> VerifyResponse:
    """
    백엔드가 티켓팅 시점에 챌린지 통과 여부를 확인하는 엔드포인트.

    /challenge/judge 완료 시 Redis에 저장된 결과를 조회한다.
    """
    passed = await verify_challenge(req.user_key, req.performance_id)
    return VerifyResponse(passed=passed)


@app.get("/internal/ai/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8090, reload=True)
