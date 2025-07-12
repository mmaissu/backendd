
import redis.asyncio as redis
import json
from typing import Optional, Any
import logging
from config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

async def get_redis() -> redis.Redis:
    return redis_client

class CacheManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = settings.CACHE_TTL
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить данные из кеша"""
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                logger.info(f"📦 Cache HIT for key: {key}")
                return json.loads(cached_data)
            logger.info(f"❌ Cache MISS for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    async def set(self, key: str, data: Any, ttl: int = None) -> bool:
        """Сохранить данные в кеш"""
        try:
            ttl = ttl or self.default_ttl
            await self.redis.set(key, json.dumps(data), ex=ttl)
            logger.info(f"💾 Cached data for key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить данные из кеша"""
        try:
            await self.redis.delete(key)
            logger.info(f"🗑️ Deleted cache key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """Удалить все ключи по паттерну"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🗑️ Deleted {len(keys)} cache keys with pattern: {pattern}")
            return True
        except Exception as e:
            logger.error(f"Error deleting pattern from cache: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Проверка здоровья Redis"""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

# Создаем глобальный экземпляр CacheManager
cache_manager = CacheManager(redis_client)

async def get_cache_manager() -> CacheManager:
    return cache_manager

