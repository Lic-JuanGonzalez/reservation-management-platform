from __future__ import annotations

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings


_redis_pool: Redis | None = None


def get_redis_pool() -> Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            str(settings.REDIS_URL),
            password=settings.REDIS_PASSWORD or None,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis_pool


async def get_redis() -> AsyncGenerator[Redis, None]:
    redis = get_redis_pool()
    try:
        yield redis
    finally:
        pass  # Pool manages connections


async def close_redis_pool() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


class RedisKeys:
    @staticmethod
    def access_token_blacklist(jti: str) -> str:
        return f"token:blacklist:{jti}"

    @staticmethod
    def refresh_token(user_id: str, jti: str) -> str:
        return f"token:refresh:{user_id}:{jti}"

    @staticmethod
    def email_verification(token: str) -> str:
        return f"email:verify:{token}"

    @staticmethod
    def password_reset(token: str) -> str:
        return f"password:reset:{token}"

    @staticmethod
    def availability_cache(tenant_id: str, resource_id: str, date: str) -> str:
        return f"avail:{tenant_id}:{resource_id}:{date}"

    @staticmethod
    def tenant_config(tenant_id: str) -> str:
        return f"tenant:{tenant_id}:config"

    @staticmethod
    def resource_list(tenant_id: str) -> str:
        return f"tenant:{tenant_id}:resources"

    @staticmethod
    def rate_limit(identifier: str, endpoint: str) -> str:
        return f"rl:{identifier}:{endpoint}"

    @staticmethod
    def session(user_id: str) -> str:
        return f"session:{user_id}"
