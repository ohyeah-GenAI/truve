from __future__ import annotations

import hashlib
import json

from src.config import DEDUP_TTL
from src.redis_client import get_redis

# dedup 적용 대상 모듈 (mouse-quiz 제외)
DEDUP_TYPES = {"vqa-image", "vqa-illusion"}


def _dedup_key(puzzle_type: str, puzzle_config: dict) -> str:
    # AI 모듈이 problem_id를 반환하면 그대로 사용, 없으면 config 해시로 fallback
    problem_id = puzzle_config.get("problem_id") or puzzle_config.get("id")
    if problem_id:
        return f"dedup:{puzzle_type}:{problem_id}"
    h = hashlib.sha256(
        json.dumps(puzzle_config, sort_keys=True).encode()
    ).hexdigest()[:16]
    return f"dedup:{puzzle_type}:{h}"


async def try_claim(puzzle_type: str, puzzle_config: dict) -> bool:
    """
    중복 문제 점유 시도.
    Returns True  → 점유 성공 (이 문제를 출제해도 됨)
    Returns False → 이미 다른 사용자가 점유 중 (재시도 필요)
    """
    if puzzle_type not in DEDUP_TYPES:
        return True

    key = _dedup_key(puzzle_type, puzzle_config)
    return bool(await get_redis().set(key, 1, ex=DEDUP_TTL, nx=True))
