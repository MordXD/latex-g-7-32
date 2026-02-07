"""
LaTeX Compilation Worker

This worker listens to RabbitMQ for compilation tasks and executes pdflatex.
"""
import os
import logging
import time
import asyncio
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
from faststream.rabbit import RabbitBroker, RabbitQueue
from faststream.rabbit.types import AioPikaSendableMessage

from app.services.latex_service import LaTeXCompiler
from app.models.compilation import CompilationStatus

load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# RabbitMQ settings
RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@rabbitmq:5672/"
)

LATEX_TASKS_QUEUE = os.getenv("LATEX_TASKS_QUEUE", "latex_tasks")

# Compiler settings
LATEX_TIMEOUT = int(os.getenv("LATEX_TIMEOUT", "60"))
LATEX_OUTPUT_DIR = os.getenv("LATEX_OUTPUT_DIR", "pdf")
LATEX_WORK_DIR = os.getenv("LATEX_WORK_DIR", "latex")

# Task results storage URL (for updating task status)
# In a real distributed system, use Redis or database
TASK_STATUS_API_URL = os.getenv(
    "TASK_STATUS_API_URL",
    "http://backend:8000"
)

# Create RabbitMQ broker
broker = RabbitBroker(url=RABBITMQ_URL)

# Create compiler
compiler = LaTeXCompiler()


async def update_task_status_via_http(task_id: str, result: dict):
    """
    Update task status via HTTP API
    (In production, use Redis or database directly)
    """
    import httpx

    try:
        # Note: This is a simplified approach. In production,
        # the worker should write directly to a shared store (Redis/DB)
        # and the API should read from that store.

        # For now, we'll publish to a results queue that the API listens to
        await broker.publish(
            message={
                "task_id": task_id,
                **result
            },
            queue="latex_results"
        )

        logger.info(f"Published result for task {task_id} to results queue")

    except Exception as e:
        logger.error(f"Failed to update task status for {task_id}: {e}")


@broker.subscriber(queue=LATEX_TASKS_QUEUE)
async def process_compilation_task(message: dict) -> str:
    """
    Process a LaTeX compilation task from RabbitMQ

    Args:
        message: Task message with task_id, content, file_path, compiler_options

    Returns:
        Task ID
    """
    task_id = message.get("task_id")
    content = message.get("content")
    file_path = message.get("file_path")
    compiler_options = message.get("compiler_options", {})

    logger.info(f"Processing task {task_id}...")

    # Update status to compiling
    await update_task_status_via_http(
        task_id,
        {
            "status": CompilationStatus.COMPILING,
            "message": "Compilation in progress",
            "progress": 0.1
        }
    )

    try:
        # Run compilation
        result = compiler.compile_latex_document(
            content=content,
            file_path=file_path,
            compiler_options=compiler_options
        )

        # Prepare result data
        result_data = {
            "status": result.status,
            "message": result.message,
            "compilation_time": result.compilation_time,
            "progress": 1.0
        }

        if result.success:
            result_data.update({
                "pdf_url": result.pdf_url,
                "warnings": result.warnings,
                "log_file": result.log_file
            })
            logger.info(f"Task {task_id} completed successfully")
        else:
            result_data.update({
                "error": result.error,
                "output": result.output,
                "log_file": result.log_file
            })
            logger.error(f"Task {task_id} failed: {result.error}")

        # Update task status with result
        await update_task_status_via_http(task_id, result_data)

    except Exception as e:
        logger.error(f"Unexpected error processing task {task_id}: {e}")

        # Update task status with error
        await update_task_status_via_http(
            task_id,
            {
                "status": CompilationStatus.ERROR,
                "message": f"Compilation failed: {str(e)}",
                "error": str(e),
                "progress": None
            }
        )

    return task_id


async def listen_to_results_queue():
    """
    Listen to results queue and update API's task status store
    (This is for when API and worker run in the same process/container)
    """
    # This is optional - in distributed setup, API would listen to results queue
    # Here we just log results for debugging
    pass


async def main():
    """Main worker entry point"""
    logger.info("Starting LaTeX Compilation Worker...")

    # Ensure directories exist
    os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
    os.makedirs(LATEX_WORK_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Check pdflatex availability
    if not compiler.check_pdflatex_available():
        logger.warning("pdflatex is not available! Compilation will fail.")
    else:
        logger.info("pdflatex is available.")

    # Start consuming messages
    logger.info(f"Listening to queue: {LATEX_TASKS_QUEUE}")
    await broker.start()


if __name__ == "__main__":
    asyncio.run(main())
