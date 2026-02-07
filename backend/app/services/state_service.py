import redis.asyncio as redis
import json
import logging
import time
from app.config import settings
from app.models.compilation import CompilationStatus

logger = logging.getLogger(__name__)

class StateService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def set_task_status(self, task_id: str, status: CompilationStatus, **kwargs):
        """Сохраняет состояние задачи в Redis"""
        data = {
            "task_id": task_id,
            "status": status,
            "updated_at": time.time(),
            **kwargs
        }
        await self.redis.set(
            f"task:{task_id}", 
            json.dumps(data), 
            ex=settings.REDIS_TASK_TTL
        )

    async def get_task_status(self, task_id: str) -> dict:
        """Получает состояние задачи из Redis"""
        data = await self.redis.get(f"task:{task_id}")
        return json.loads(data) if data else None

    async def publish_progress(self, task_id: str, message: dict):
        """Отправляет Real-time лог в канал Pub/Sub"""
        channel = f"task:progress:{task_id}"
        await self.redis.publish(channel, json.dumps(message))

    def get_pubsub(self):
        """Возвращает объект для подписки"""
        return self.redis.pubsub()

state_service = StateService()