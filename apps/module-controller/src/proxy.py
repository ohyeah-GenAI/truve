from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from src.config import (
    DEDUP_MAX_RETRY,
    FLOW_SESSION_TTL,
    MAX_ATTEMPTS_PER_STEP,
    MODULE_URLS,
    SECURITY_POLICY,
)
from src.dedup import try_claim
from src.redis_client import get_redis

# 앱 수명 동안 유지하는 커넥션 풀 (매 요청마다 TCP 재연결 방지)
_http_client: httpx.AsyncClient | None = None


async def init_http_client() -> None:
    global _http_client
    _http_client = httpx.AsyncClient(timeout=10.0)


async def close_http_client() -> None:
    if _http_client:
        await _http_client.aclose()


def _client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client not initialized")
    return _http_client


async def _generate_puzzle(puzzle_type: str) -> dict:
    """AI 모듈에서 문제를 가져오고 VQA dedup을 통과할 때까지 재시도."""
    base_url = MODULE_URLS[puzzle_type]
    for _ in range(DEDUP_MAX_RETRY):
        r = await _client().get(
            f"{base_url}/api/puzzle/generate",
            params={"type": puzzle_type},
        )
        r.raise_for_status()
        data = r.json()
        if await try_claim(puzzle_type, data.get("puzzle_config", {})):
            return data
    raise HTTPException(
        status_code=503,
        detail=f"중복 문제 회피 실패 ({puzzle_type}): 재시도 {DEDUP_MAX_RETRY}회 초과",
    )


async def start_challenge(performance_id: str, user_key: str) -> dict:
    """
    챌린지 플로우 시작.

    확정 (2026-04-14 백엔드 팀 답변):
      - user_key: API Gateway가 HTTP 헤더(X-User-Id)로 전달하는 UUID 문자열
      - 진입 방향: 백엔드 서버 → 컨트롤러 서버 간 호출 (A안 확정)
      - JWT 검증: Gateway에서 처리, 컨트롤러 자체 검증 불필요
    """
    from src.db_client import get_security_level

    security_level = await get_security_level(performance_id)
    sequence: list[str] = SECURITY_POLICY.get(security_level, SECURITY_POLICY["LOW"])

    first_type = sequence[0]
    first_puzzle = await _generate_puzzle(first_type)

    flow_session_id = str(uuid.uuid4())
    flow_data: Dict[str, Any] = {
        "performance_id": performance_id,
        "user_key": user_key,
        "security_level": security_level,
        "sequence": sequence,
        "current_step": 0,
        "step_session_ids": {t: None for t in sequence},
        "attempt_counts": {t: 0 for t in sequence},  # 단계별 시도 횟수
        "completed": [],
    }
    flow_data["step_session_ids"][first_type] = first_puzzle["session_id"]

    redis = get_redis()
    await redis.setex(
        f"challenge_flow:{flow_session_id}",
        FLOW_SESSION_TTL,
        json.dumps(flow_data),
    )

    return {
        "flow_session_id": flow_session_id,
        "puzzle_type": first_type,
        "puzzle_config": first_puzzle["puzzle_config"],
        "flow_complete": False,
    }


async def submit_judge(
    flow_session_id: str,
    answer: Dict[str, Any],
    events: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """현재 단계 채점 → 통과 시 다음 단계 발급 또는 플로우 완료."""
    redis = get_redis()
    flow_key = f"challenge_flow:{flow_session_id}"

    raw = await redis.get(flow_key)
    if not raw:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 flow_session_id")

    flow: Dict[str, Any] = json.loads(raw)
    current_step: int = flow["current_step"]
    sequence: list[str] = flow["sequence"]
    current_type = sequence[current_step]
    step_session_id = flow["step_session_ids"][current_type]

    judge_payload: Dict[str, Any] = {
        "session_id": step_session_id,
        "puzzle_type": current_type,
        "answer": answer,
        "events": events or [],
    }
    r = await _client().post(
        f"{MODULE_URLS[current_type]}/judge",
        json=judge_payload,
    )
    r.raise_for_status()
    result = r.json()

    if not result.get("passed", False):
        attempt_counts: Dict[str, int] = flow.get("attempt_counts", {t: 0 for t in sequence})
        attempt_counts[current_type] = attempt_counts.get(current_type, 0) + 1

        if attempt_counts[current_type] >= MAX_ATTEMPTS_PER_STEP:
            # 2차 실패 → 차단
            await redis.delete(flow_key)
            return {
                "passed": False,
                "flow_complete": False,
                "blocked": True,
                "module": current_type,
                "is_human": result.get("is_human", False),
            }

        # 1차 실패 → 재도전 허용, 새 퍼즐 발급
        retry_puzzle = await _generate_puzzle(current_type)
        flow["attempt_counts"] = attempt_counts
        flow["step_session_ids"][current_type] = retry_puzzle["session_id"]
        await redis.setex(flow_key, FLOW_SESSION_TTL, json.dumps(flow))
        return {
            "passed": False,
            "flow_complete": False,
            "blocked": False,
            "module": current_type,
            "is_human": result.get("is_human", False),
            "next_puzzle_type": current_type,
            "next_puzzle_config": retry_puzzle["puzzle_config"],
        }

    flow["completed"].append(current_type)
    next_step = current_step + 1

    if next_step >= len(sequence):
        # 모든 단계 통과 → 플로우 종료
        await redis.delete(flow_key)
        return {"passed": True, "flow_complete": True}

    # 다음 단계 퍼즐 발급
    next_type = sequence[next_step]
    next_puzzle = await _generate_puzzle(next_type)

    flow["current_step"] = next_step
    flow["step_session_ids"][next_type] = next_puzzle["session_id"]
    await redis.setex(flow_key, FLOW_SESSION_TTL, json.dumps(flow))

    return {
        "passed": True,
        "flow_complete": False,
        "next_puzzle_type": next_type,
        "next_puzzle_config": next_puzzle["puzzle_config"],
    }
