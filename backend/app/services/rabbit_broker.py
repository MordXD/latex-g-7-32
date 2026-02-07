import os
import logging
from typing import Callable, Optional
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter

logger = logging.getLogger(__name__)

# RabbitMQ connection settings
RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@localhost:5672/"
)

# Queue names
LATEX_TASKS_QUEUE = os.getenv("LATEX_TASKS_QUEUE", "latex_tasks")
LATEX_RESULTS_QUEUE = os.getenv("LATEX_RESULTS_QUEUE", "latex_results")

# Create RabbitMQ broker
rabbit_broker = RabbitBroker(url=RABBITMQ_URL)

# Router for FastAPI integration
rabbit_router = RabbitRouter(
    broker=rabbit_broker,
    prefix="/api/queue",
    tags=["queue"]
)

# Callback storage for result handling
_result_callbacks: dict[str, Callable] = {}


def register_result_callback(task_id: str, callback: Callable):
    """Register a callback for task result processing"""
    _result_callbacks[task_id] = callback


def unregister_result_callback(task_id: str):
    """Unregister a callback for task result processing"""
    _result_callbacks.pop(task_id, None)


def get_result_callback(task_id: str) -> Optional[Callable]:
    """Get a callback for task result processing"""
    return _result_callbacks.get(task_id)


async def publish_compilation_task(
    content: Optional[str] = None,
    file_path: Optional[str] = None,
    compiler_options: Optional[dict] = None
) -> str:
    """
    Publish a compilation task to RabbitMQ

    Returns:
        task_id: The task identifier
    """
    import uuid
    import json

    task_id = str(uuid.uuid4())

    task_message = {
        "task_id": task_id,
        "content": content,
        "file_path": file_path,
        "compiler_options": compiler_options or {}
    }

    logger.info(f"Publishing compilation task {task_id} to queue {LATEX_TASKS_QUEUE}")

    await rabbit_broker.publish(
        message=task_message,
        queue=LATEX_TASKS_QUEUE
    )

    return task_id


async def publish_task_result(
    task_id: str,
    status: str,
    result: dict
) -> None:
    """
    Publish a task result to RabbitMQ results queue

    Args:
        task_id: The task identifier
        status: Task status (success, error, etc.)
        result: Result data
    """
    result_message = {
        "task_id": task_id,
        "status": status,
        **result
    }

    logger.info(f"Publishing result for task {task_id} to queue {LATEX_RESULTS_QUEUE}")

    await rabbit_broker.publish(
        message=result_message,
        queue=LATEX_RESULTS_QUEUE
    )


async def initialize_broker():
    """Initialize RabbitMQ broker and declare queues"""
    logger.info("Initializing RabbitMQ broker...")
    await rabbit_broker.connect()

    # Declare queues (idempotent)
    await rabbit_broker.declare_queue(LATEX_TASKS_QUEUE, durable=True)
    await rabbit_broker.declare_queue(LATEX_RESULTS_QUEUE, durable=True)

    logger.info("RabbitMQ broker initialized successfully")


async def close_broker():
    """Close RabbitMQ broker connection"""
    logger.info("Closing RabbitMQ broker...")
    await rabbit_broker.close()
    logger.info("RabbitMQ broker closed")
