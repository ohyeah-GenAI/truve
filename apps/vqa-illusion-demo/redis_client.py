from __future__ import annotations

import os

import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None


async def init_redis() -> None:
    global _redis
    _redis = aioredis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        password=os.environ.get("REDIS_PASSWORD") or None,
        decode_responses=True,
    )
    await _redis.ping()


async def close_redis() -> None:
    if _redis:
        await _redis.aclose()


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis client not initialized")
    return _redis
