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
    STEP_CATALOG,
    VERIFY_RESULT_TTL,
)
from src.dedup import try_claim
from src.redis_client import get_redis

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


def _step_spec(step_id: str) -> Dict[str, Any]:
    try:
        return STEP_CATALOG[step_id]
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=f"지원하지 않는 챌린지 단계입니다: {step_id}") from exc


def _validate_generate_response(step_id: str, data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail=f"{step_id} generate 응답 형식이 올바르지 않습니다.")
    if not isinstance(data.get("session_id"), str):
        raise HTTPException(status_code=502, detail=f"{step_id} generate 응답에 session_id가 없습니다.")
    expected_type = _step_spec(step_id).get("generate_type")
    if isinstance(expected_type, str) and data.get("puzzle_type") != expected_type:
        raise HTTPException(
            status_code=502,
            detail=f"{step_id} generate 응답의 puzzle_type이 예상과 다릅니다.",
        )
    if not isinstance(data.get("puzzle_config"), dict):
        raise HTTPException(status_code=502, detail=f"{step_id} generate 응답에 puzzle_config가 없습니다.")
    return data


def _validate_judge_response(step_id: str, data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail=f"{step_id} judge 응답 형식이 올바르지 않습니다.")
    if not isinstance(data.get("passed"), bool):
        raise HTTPException(status_code=502, detail=f"{step_id} judge 응답에 passed가 없습니다.")
    blocked = data.get("blocked")
    if blocked is not None and not isinstance(blocked, bool):
        raise HTTPException(status_code=502, detail=f"{step_id} judge 응답의 blocked 형식이 올바르지 않습니다.")
    return data


async def _generate_step(step_id: str) -> Dict[str, Any]:
    spec = _step_spec(step_id)
    module = str(spec["module"])
    generate_type = spec["generate_type"]
    if not isinstance(generate_type, str):
        raise HTTPException(status_code=500, detail=f"{step_id} step의 generate_type이 올바르지 않습니다.")
    base_url = MODULE_URLS[module]

    for _ in range(DEDUP_MAX_RETRY):
        try:
            response = await _client().get(
                f"{base_url}/api/puzzle/generate",
                params={"type": generate_type},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"{step_id} generate 호출에 실패했습니다.") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail=f"{step_id} generate 서비스에 연결할 수 없습니다.") from exc

        data = _validate_generate_response(step_id, response.json())
        if await try_claim(step_id, data["puzzle_config"]):
            return data

    raise HTTPException(
        status_code=503,
        detail=f"중복 문제 회피 실패 ({step_id}): 재시도 {DEDUP_MAX_RETRY}회 초과",
    )


def _challenge_payload(step_id: str, puzzle_config: Dict[str, Any]) -> Dict[str, Any]:
    spec = _step_spec(step_id)
    return {
        "puzzle_type": spec["challenge_type"],
        "puzzle_config": puzzle_config,
    }


async def start_challenge(performance_id: str, user_key: str, risk_level: str) -> Dict[str, Any]:
    selected_risk_level = risk_level.upper().strip()
    if selected_risk_level not in SECURITY_POLICY:
        raise HTTPException(status_code=422, detail="지원하지 않는 risk_level 입니다.")

    sequence: List[str] = list(SECURITY_POLICY[selected_risk_level])
    first_step_id = sequence[0]
    first_puzzle = await _generate_step(first_step_id)

    flow_session_id = str(uuid.uuid4())
    flow_data: Dict[str, Any] = {
        "performance_id": performance_id,
        "user_key": user_key,
        "security_level": selected_risk_level,
        "sequence": sequence,
        "current_step": 0,
        "step_session_ids": {step_id: None for step_id in sequence},
        "attempt_counts": {step_id: 0 for step_id in sequence},
        "completed": [],
    }
    flow_data["step_session_ids"][first_step_id] = first_puzzle["session_id"]

    redis = get_redis()
    await redis.setex(
        f"challenge_flow:{flow_session_id}",
        FLOW_SESSION_TTL,
        json.dumps(flow_data),
    )

    return {
        "flow_session_id": flow_session_id,
        **_challenge_payload(first_step_id, first_puzzle["puzzle_config"]),
        "flow_complete": False,
    }


async def submit_judge(
    flow_session_id: str,
    answer: Dict[str, Any],
    events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    redis = get_redis()
    flow_key = f"challenge_flow:{flow_session_id}"

    raw = await redis.get(flow_key)
    if not raw:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 flow_session_id")

    flow: Dict[str, Any] = json.loads(raw)
    current_step_index: int = flow["current_step"]
    sequence: List[str] = flow["sequence"]
    current_step_id = sequence[current_step_index]
    current_spec = _step_spec(current_step_id)
    step_session_id = flow["step_session_ids"][current_step_id]

    judge_payload: Dict[str, Any] = {
        "session_id": step_session_id,
        "puzzle_type": current_spec["generate_type"],
        "answer": answer,
        "events": (events or []) if bool(current_spec["supports_events"]) else [],
    }

    try:
        response = await _client().post(
            f"{MODULE_URLS[str(current_spec['module'])]}/judge",
            json=judge_payload,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 422:
            try:
                detail = exc.response.json().get("detail")
            except ValueError:
                detail = "하위 AI 서비스가 요청 형식을 거부했습니다."
            raise HTTPException(status_code=422, detail=detail) from exc
        raise HTTPException(status_code=502, detail=f"{current_step_id} judge 호출에 실패했습니다.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"{current_step_id} judge 서비스에 연결할 수 없습니다.") from exc

    result = _validate_judge_response(current_step_id, response.json())

    if result.get("blocked") is True:
        await redis.delete(flow_key)
        return {
            "passed": False,
            "flow_complete": False,
            "blocked": True,
            "module": current_spec["module"],
            "is_human": result.get("is_human", False),
        }

    if not result["passed"]:
        attempt_counts: Dict[str, int] = flow.get("attempt_counts", {step_id: 0 for step_id in sequence})
        attempt_counts[current_step_id] = attempt_counts.get(current_step_id, 0) + 1

        if attempt_counts[current_step_id] >= MAX_ATTEMPTS_PER_STEP:
            await redis.delete(flow_key)
        return {
            "passed": False,
            "flow_complete": False,
            "blocked": True,
            "module": current_spec["module"],
            "is_human": result.get("is_human", False),
        }

        retry_puzzle = await _generate_step(current_step_id)
        flow["attempt_counts"] = attempt_counts
        flow["step_session_ids"][current_step_id] = retry_puzzle["session_id"]
        await redis.setex(flow_key, FLOW_SESSION_TTL, json.dumps(flow))

        return {
            "passed": False,
            "flow_complete": False,
            "blocked": False,
            "module": current_spec["module"],
            "is_human": result.get("is_human", False),
            "next_puzzle_type": current_spec["challenge_type"],
            "next_puzzle_config": retry_puzzle["puzzle_config"],
        }

    flow["completed"].append(current_step_id)
    next_step_index = current_step_index + 1

    if next_step_index >= len(sequence):
        await redis.delete(flow_key)
        verify_key = f"challenge_result:{flow['user_key']}:{flow['performance_id']}"
        await redis.setex(verify_key, VERIFY_RESULT_TTL, "1")
        return {
            "passed": True,
            "flow_complete": True,
            "blocked": False,
            "module": current_spec["module"],
        }

    next_step_id = sequence[next_step_index]
    next_spec = _step_spec(next_step_id)
    next_puzzle = await _generate_step(next_step_id)

    flow["current_step"] = next_step_index
    flow["step_session_ids"][next_step_id] = next_puzzle["session_id"]
    await redis.setex(flow_key, FLOW_SESSION_TTL, json.dumps(flow))

    return {
        "passed": True,
        "flow_complete": False,
        "blocked": False,
        "module": current_spec["module"],
        "next_puzzle_type": next_spec["challenge_type"],
        "next_puzzle_config": next_puzzle["puzzle_config"],
    }


async def verify_challenge(user_key: str, performance_id: str) -> bool:
    """백엔드가 티켓팅 시점에 챌린지 통과 여부를 조회. 조회 즉시 키 삭제 (단발성)."""
    redis = get_redis()
    verify_key = f"challenge_result:{user_key}:{performance_id}"
    result = await redis.getdel(verify_key)
    return result == "1"
