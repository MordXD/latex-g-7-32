from fastapi import APIRouter, HTTPException
from app.models.compilation import TaskStatusResponse, CompilationStatus
from app.services.state_service import state_service
from app.services.storage_service import storage_service

router = APIRouter()

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_compilation_status(task_id: str):
    # 1. Читаем статус из Redis
    task_data = await state_service.get_task_status(task_id)
    
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    response = TaskStatusResponse(**task_data)

    # 2. Если готово - генерируем S3 ссылку
    if task_data.get("status") == CompilationStatus.SUCCESS:
        s3_key = task_data.get("s3_pdf_key")
        if s3_key:
            # Генерация pre-signed URL (прямой доступ к S3)
            response.pdf_url = storage_service.get_presigned_url(s3_key)
            
    return response