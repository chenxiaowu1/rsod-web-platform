"""Redis 服务 — 检测结果缓存 + 请求限流。"""
import json
import hashlib
import logging
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger("rsod.redis")


class RedisService:
    def __init__(self):
        self.client: aioredis.Redis | None = None

    async def connect(self):
        try:
            self.client = aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis 连接成功: %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Redis 不可用，缓存和限流功能关闭: %s", e)
            self.client = None

    async def close(self):
        if self.client:
            await self.client.close()

    # ── 检测结果缓存 ──

    async def cache_detection(self, image_bytes: bytes, result: dict, ttl: int = 3600):
        """缓存检测结果，相同图片哈希直接返回。"""
        if not self.client:
            return
        image_hash = hashlib.md5(image_bytes).hexdigest()
        await self.client.setex(f"det:{image_hash}", ttl, json.dumps(result, default=str))

    async def get_cached_detection(self, image_bytes: bytes) -> dict | None:
        if not self.client:
            return None
        image_hash = hashlib.md5(image_bytes).hexdigest()
        data = await self.client.get(f"det:{image_hash}")
        return json.loads(data) if data else None

    # ── 请求限流 ──

    async def check_rate_limit(self, user_id: int, limit: int = 30, window: int = 60) -> bool:
        """每用户每分钟最多 limit 次检测请求。返回 True 表示未超限。"""
        if not self.client:
            return True
        key = f"rate:det:{user_id}"
        current = await self.client.incr(key)
        if current == 1:
            await self.client.expire(key, window)
        return current <= limit

    async def check_rate_limit_str(self, key_suffix: str, limit: int = 10, window: int = 60) -> bool:
        """通用字符串 key 限流。返回 True 表示未超限。"""
        if not self.client:
            return True
        key = f"rate:{key_suffix}"
        current = await self.client.incr(key)
        if current == 1:
            await self.client.expire(key, window)
        return current <= limit


redis_service = RedisService()
