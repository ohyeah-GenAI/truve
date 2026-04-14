from __future__ import annotations

import os

import aiomysql

from src.config import PERF_LEVEL_CACHE_TTL
from src.redis_client import get_redis


async def get_security_level(performance_id: str) -> str:
    """공연 ID로 보안 레벨 조회. Redis 캐시 우선, miss 시 MySQL RDS 직접 조회."""
    redis = get_redis()
    cache_key = f"perf_level:{performance_id}"

    cached = await redis.get(cache_key)
    if cached:
        return cached

    async with aiomysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        db=os.environ["DB_NAME"],
        autocommit=True,
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT security_level FROM performances WHERE id = %s",
                (performance_id,),
            )
            row = await cur.fetchone()
            level: str = row[0] if row else "LOW"

    await redis.setex(cache_key, PERF_LEVEL_CACHE_TTL, level)
    return level
