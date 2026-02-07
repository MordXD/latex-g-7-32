"""
Results queue handler for API Gateway

This module handles results from the worker and updates task status.
"""
import logging
from typing import Optional
from faststream.rabbit import RabbitBroker

from app.services.rabbit_broker import rabbit_broker, LATEX_RESULTS_QUEUE
from app.models.compilation import CompilationStatus

logger = logging.getLogger(__name__)


async def handle_result_message(message: dict):
    """
    Handle a result message from the worker

    Args:
        message: Result message with task_id, status, and result data
    """
    task_id = message.get("task_id")
    if not task_id:
        logger.warning("Received result message without task_id")
        return

    logger.info(f"Received result for task {task_id}: {message.get('status')}")

    # Import here to avoid circular dependency
    from app.routers.compilation import update_task_status

    # Update task status
    await update_task_status(
        task_id,
        **message
    )


async def start_results_listener(broker: RabbitBroker):
    """
    Start listening to the results queue

    This should be called during API startup
    """
    logger.info(f"Starting results queue listener on {LATEX_RESULTS_QUEUE}")

    @broker.subscriber(queue=LATEX_RESULTS_QUEUE)
    async def process_result(message: dict):
        await handle_result_message(message)

    logger.info("Results queue listener started")
