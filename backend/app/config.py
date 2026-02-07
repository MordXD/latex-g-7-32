import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    LATEX_TASKS_QUEUE: str = "latex_tasks"

    # Redis (State & Pub/Sub)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_TASK_TTL: int = 86400  # 24 часа

    # S3 / MinIO (Storage)
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    S3_BUCKET_NAME: str = "latex-artifacts"
    S3_REGION: str = "us-east-1"
    PRESIGNED_URL_EXPIRATION: int = 3600  # 1 час

    # LaTeX
    LATEX_TIMEOUT: int = 120

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()