import asyncio
import logging
import os
from faststream.rabbit import RabbitBroker
from app.services.latex_service import latex_service
from app.services.storage_service import storage_service
from app.services.state_service import state_service
from app.models.compilation import CompilationStatus
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

broker = RabbitBroker(url=settings.RABBITMQ_URL)

@broker.subscriber(queue=settings.LATEX_TASKS_QUEUE)
async def process_compilation_task(message: dict):
    task_id = message.get("task_id")
    content = message.get("content")
    options = message.get("compiler_options", {})

    logger.info(f"🚀 Processing task {task_id}")

    # 1. Статус -> PROCESSING
    await state_service.set_task_status(
        task_id, 
        CompilationStatus.COMPILING,
        message="Compilation started"
    )

    # Callback для отправки логов в Redis Pub/Sub
    async def progress_reporter(msg: str):
        await state_service.publish_progress(task_id, {
            "status": "compiling",
            "message": msg,
            "progress": None
        })

    # 2. Изолированная компиляция во временной папке
    with latex_service.temporary_work_dir() as work_dir:
        result = await latex_service.compile_latex_stream(
            content=content,
            work_dir=work_dir,
            compiler_options=options,
            progress_callback=progress_reporter
        )

        if result["success"]:
            # 3. Загрузка артефактов в S3
            pdf_key = f"pdfs/{task_id}.pdf"
            log_key = f"logs/{task_id}.log"
            
            s3_pdf = storage_service.upload_file(result["pdf_path"], pdf_key, "application/pdf")
            s3_log = storage_service.upload_file(result["log_path"], log_key, "text/plain")

            if s3_pdf:
                # 4. Успех
                await state_service.set_task_status(
                    task_id,
                    CompilationStatus.SUCCESS,
                    message="Compilation completed successfully",
                    s3_pdf_key=pdf_key,
                    s3_log_key=log_key
                )
                
                # Финальное сообщение в сокет
                await state_service.publish_progress(task_id, {
                    "status": "success",
                    "message": "Done"
                })
                logger.info(f"✅ Task {task_id} completed")
            else:
                await _handle_error(task_id, "Failed to upload artifacts to S3")
        else:
            # Ошибка компиляции
            error_log_key = f"logs/{task_id}_error.log"
            # Пробуем сохранить лог ошибок
            if result["log_path"]:
                storage_service.upload_file(result["log_path"], error_log_key, "text/plain")
            
            await _handle_error(task_id, "LaTeX compilation failed", result["full_log"])

async def _handle_error(task_id: str, message: str, full_log: str = None):
    await state_service.set_task_status(
        task_id,
        CompilationStatus.ERROR,
        message=message,
        error=full_log
    )
    await state_service.publish_progress(task_id, {
        "status": "error",
        "message": message
    })
    logger.error(f"❌ Task {task_id} failed: {message}")

if __name__ == "__main__":
    asyncio.run(broker.start())