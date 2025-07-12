from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json
import hashlib
from typing import Optional
from redis_client import get_cache_manager
import logging

logger = logging.getLogger(__name__)

class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_routes: Optional[list] = None, ttl: int = 300):
        super().__init__(app)
        self.cache_routes = cache_routes or ["/notes", "/users"]
        self.ttl = ttl
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем, нужно ли кешировать этот маршрут
        if not self._should_cache(request.url.path, request.method):
            return await call_next(request)
        
        # Генерируем ключ кеша
        cache_key = self._generate_cache_key(request)
        
        # Получаем менеджер кеша
        cache_manager = await get_cache_manager()
        
        # Для GET запросов - проверяем кеш
        if request.method == "GET":
            cached_response = await cache_manager.get(cache_key)
            if cached_response:
                logger.info(f"🔄 Returning cached response for {request.url.path}")
                return JSONResponse(
                    content=cached_response,
                    status_code=200,
                    headers={"X-Cache": "HIT"}
                )
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Кешируем успешные GET ответы
        if request.method == "GET" and response.status_code == 200:
            try:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Парсим JSON для кеширования
                try:
                    json_data = json.loads(response_body.decode())
                    await cache_manager.set(cache_key, json_data, self.ttl)
                    logger.info(f"💾 Cached response for {request.url.path}")
                except json.JSONDecodeError:
                    logger.warning(f"Could not cache non-JSON response for {request.url.path}")
                
                # Возвращаем новый response с тем же содержимым
                return JSONResponse(
                    content=json_data,
                    status_code=200,
                    headers={"X-Cache": "MISS"}
                )
            except Exception as e:
                logger.error(f"Error caching response: {e}")
        
        # Для модифицирующих запросов - инвалидируем кеш
        elif request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            await self._invalidate_cache(request.url.path, cache_manager)
        
        return response
    
    def _should_cache(self, path: str, method: str) -> bool:
        """Определяет, нужно ли кешировать запрос"""
        # Кешируем только GET запросы для определенных маршрутов
        if method != "GET":
            return False
        
        return any(route in path for route in self.cache_routes)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Генерирует уникальный ключ кеша для запроса"""
        # Базовый ключ
        key_parts = [request.method, request.url.path]
        
        # Добавляем query параметры
        if request.query_params:
            query_string = str(request.query_params)
            key_parts.append(query_string)
        
        # Добавляем заголовки авторизации (если есть)
        auth_header = request.headers.get("authorization")
        if auth_header:
            key_parts.append(auth_header)
        
        # Создаем хеш
        key_string = "|".join(key_parts)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def _invalidate_cache(self, path: str, cache_manager):
        """Инвалидирует кеш для определенного пути"""
        try:
            # Удаляем все ключи, связанные с этим путем
            pattern = f"cache:*"
            await cache_manager.delete_pattern(pattern)
            logger.info(f"🗑️ Invalidated cache for path: {path}")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

# Функция для создания middleware
def create_cache_middleware(app, cache_routes: Optional[list] = None, ttl: int = 300):
    """Создает и возвращает middleware для кеширования"""
    return CacheMiddleware(app, cache_routes, ttl) 