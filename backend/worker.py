"""
LaTeX Compilation Worker

This worker is a critical component of the microservices architecture.
It consumes tasks from RabbitMQ, compiles LaTeX documents in an isolated environment,
uploads artifacts to S3, and reports real-time progress via Redis Pub/Sub.

Features:
- Stateless execution using temporary directories
- Real-time log streaming via Redis
- S3 Artifact storage
- Prometheus metrics for monitoring
- Robust error handling
"""

import asyncio
import logging
import os
import time
from faststream.rabbit import RabbitBroker
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# Internal modules
from app.services.latex_service import latex_service
from app.services.storage_service import storage_service
from app.services.state_service import state_service
from app.models.compilation import CompilationStatus
from app.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("worker")

# ==========================================
# Prometheus Metrics Definition
# ==========================================

# Histogram: Tracks how long compilation takes
# Buckets optimized for typical compilation times (1s to 2min)
COMPILATION_DURATION = Histogram(
    'latex_compilation_duration_seconds', 
    'Time spent compiling LaTeX document',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Gauge: Tracks currently running compilations
# Useful for autoscaling decisions (HPA)
ACTIVE_COMPILATIONS = Gauge(
    'latex_active_compilations', 
    'Number of compilations currently in progress'
)

# Counter: Tracks total errors
COMPILATION_ERRORS = Counter(
    'latex_compilation_errors_total', 
    'Total number of failed compilations'
)

# Counter: Tracks total processed tasks
COMPILATIONS_TOTAL = Counter(
    'latex_compilations_total',
    'Total number of processed compilations'
)

# ==========================================
# Broker Configuration
# ==========================================

broker = RabbitBroker(url=settings.RABBITMQ_URL)

async def _handle_error(task_id: str, message: str, full_log: str = None):
    """
    Centralized error handling logic.
    Updates Redis state and notifies listeners via Pub/Sub.
    """
    logger.error(f"❌ Task {task_id} failed: {message}")
    
    # Update state in Redis
    await state_service.set_task_status(
        task_id,
        CompilationStatus.ERROR,
        message=message,
        error=full_log
    )
    
    # Notify subscribers (WebSocket clients)
    await state_service.publish_progress(task_id, {
        "status": "error",
        "message": message,
        "error": message # Send short error message to UI
    })

@broker.subscriber(queue=settings.LATEX_TASKS_QUEUE)
async def process_compilation_task(message: dict):
    """
    Main worker logic processing a compilation task.
    """
    # 1. Metrics: Increment counters
    ACTIVE_COMPILATIONS.inc()
    COMPILATIONS_TOTAL.inc()
    
    task_id = message.get("task_id")
    content = message.get("content")
    options = message.get("compiler_options", {})

    logger.info(f"🚀 Starting processing for task: {task_id}")

    try:
        if not task_id or not content:
            raise ValueError("Invalid task data: missing task_id or content")

        # 2. Update Status: PROCESSING
        await state_service.set_task_status(
            task_id, 
            CompilationStatus.COMPILING,
            message="Worker received task, starting compilation..."
        )

        # Callback function for streaming logs from LaTeX to Redis
        async def progress_reporter(msg: str):
            # This is called for every significant line in pdflatex stdout
            await state_service.publish_progress(task_id, {
                "status": "compiling",
                "message": msg,
                "progress": None # Progress calculation could be added here
            })

        # 3. Compile: Use temporary directory + measure time
        result = None
        with COMPILATION_DURATION.time(): # Measure duration for Prometheus
            
            # Create isolated environment for this task
            with latex_service.temporary_work_dir() as work_dir:
                
                # Execute compilation with stream processing
                result = await latex_service.compile_latex_stream(
                    content=content,
                    work_dir=work_dir,
                    compiler_options=options,
                    progress_callback=progress_reporter
                )

                # 4. Upload Artifacts: If successful, upload to S3
                if result["success"]:
                    logger.info(f"Compilation success for {task_id}, uploading artifacts...")
                    
                    pdf_key = f"pdfs/{task_id}.pdf"
                    log_key = f"logs/{task_id}.log"
                    
                    # Upload PDF
                    pdf_uploaded = False
                    if result["pdf_path"]:
                        pdf_uploaded = storage_service.upload_file(
                            result["pdf_path"], 
                            pdf_key, 
                            "application/pdf"
                        )
                    
                    # Upload Log (always useful)
                    if result["log_path"]:
                        storage_service.upload_file(
                            result["log_path"], 
                            log_key, 
                            "text/plain"
                        )

                    if pdf_uploaded:
                        # 5. Final Success State
                        await state_service.set_task_status(
                            task_id,
                            CompilationStatus.SUCCESS,
                            message="Compilation completed successfully",
                            s3_pdf_key=pdf_key,
                            s3_log_key=log_key,
                            compilation_time=result.get("compilation_time", 0.0) # Optional if calculated
                        )
                        
                        # Notify UI of success
                        await state_service.publish_progress(task_id, {
                            "status": "success",
                            "message": "Compilation complete! Generating download link..."
                        })
                        
                        logger.info(f"✅ Task {task_id} completed successfully")
                    else:
                        raise RuntimeError("Failed to upload PDF artifact to storage")
                else:
                    # Compilation logic returned failure (e.g. syntax error)
                    # Try to upload error log for debugging
                    error_log_key = f"logs/{task_id}_error.log"
                    if result["log_path"]:
                        storage_service.upload_file(
                            result["log_path"], 
                            error_log_key, 
                            "text/plain"
                        )
                    
                    # Raise exception to be caught below
                    raise RuntimeError(f"LaTeX Compilation failed. Check logs.")

    except Exception as e:
        # 6. Error Handling
        COMPILATION_ERRORS.inc()
        
        # Get full log if available from result, otherwise empty
        full_log = result.get("full_log") if result else str(e)
        
        await _handle_error(task_id, str(e), full_log)

    finally:
        # 7. Metrics: Decrement active gauge
        ACTIVE_COMPILATIONS.dec()


async def main():
    """
    Worker entry point.
    Starts Prometheus metrics server and RabbitMQ consumer.
    """
    logger.info("Worker service starting...")
    
    # Verify connections before starting
    try:
        # Check Redis
        await state_service.redis.ping()
        logger.info("Connected to Redis")
        
        # S3 check happens in storage_service init
        logger.info(f"S3 Storage configured: {settings.S3_BUCKET_NAME}")
        
    except Exception as e:
        logger.critical(f"Startup check failed: {e}")
        return

    # Start Prometheus HTTP server
    # Metrics will be available at http://worker-pod-ip:8001/metrics
    try:
        start_http_server(8001)
        logger.info("Prometheus metrics server started on port 8001")
    except Exception as e:
        logger.warning(f"Failed to start metrics server: {e}")

    # Start consuming messages
    logger.info(f"Listening to queue: {settings.LATEX_TASKS_QUEUE}")
    await broker.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")