import os
import logging
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.models.compilation import CompilationRequest, CompilationResponse
from app.services.latex_service import latex_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/compile", response_model=CompilationResponse)
async def compile_latex_document(
    request: CompilationRequest
):
    """
    Compile a LaTeX document

    Either provide content as string or file_path to existing .tex file
    """
    try:
        logger.info(f"Received compilation request: content={'<text>' if request.content else 'None'}, file_path={request.file_path}")

        result = latex_service.compile_latex_document(
            content=request.content,
            file_path=request.file_path,
            compiler_options=request.compiler_options
        )

        logger.info(f"Compilation completed: success={result.success}, status={result.status}")
        return result

    except Exception as e:
        logger.error(f"Compilation request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")

@router.post("/compile/upload")
async def compile_uploaded_file(
    file: UploadFile = File(...),
    compiler_options: Optional[str] = Form(None)
):
    """
    Upload and compile a LaTeX file
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.tex', '.latex')):
            raise HTTPException(status_code=400, detail="Only .tex and .latex files are supported")

        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8', errors='replace')

        # Parse compiler options if provided
        options = {}
        if compiler_options:
            import json
            try:
                options = json.loads(compiler_options)
            except json.JSONDecodeError:
                logger.warning(f"Invalid compiler options JSON: {compiler_options}")

        result = latex_service.compile_latex_document(
            content=content_str,
            compiler_options=options
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload compilation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")

@router.get("/download/{filename}")
async def download_pdf(filename: str):
    """
    Download a compiled PDF file
    """
    try:
        file_path = Path("pdf") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed for {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/download/{compilation_id}/pdf")
async def download_compilation_pdf(compilation_id: str):
    """
    Download PDF by compilation ID
    """
    filename = f"{compilation_id}.pdf"
    return await download_pdf(filename)

@router.get("/download/{compilation_id}/log")
async def download_compilation_log(compilation_id: str):
    """
    Download compilation log by compilation ID
    """
    try:
        # Try error log first, then success log
        for suffix in ["_error.log", ".log"]:
            filename = f"{compilation_id}{suffix}"
            file_path = Path("pdf") / filename

            if file_path.exists():
                return FileResponse(
                    path=str(file_path),
                    filename=filename,
                    media_type="text/plain"
                )

        raise HTTPException(status_code=404, detail="Log file not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Log download failed for {compilation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/templates")
async def get_available_templates():
    """
    Get list of available LaTeX templates
    """
    try:
        templates = []
        latex_dir = Path("latex")

        if latex_dir.exists():
            for tex_file in latex_dir.glob("*.tex"):
                templates.append({
                    "name": tex_file.stem,
                    "filename": tex_file.name,
                    "description": f"Template file: {tex_file.name}",
                    "size": tex_file.stat().st_size
                })

        return {"templates": templates}

    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.get("/templates/{template_name}")
async def get_template_content(template_name: str):
    """
    Get content of a specific template
    """
    try:
        template_file = Path("latex") / f"{template_name}.tex"

        if not template_file.exists():
            raise HTTPException(status_code=404, detail="Template not found")

        content = template_file.read_text(encoding='utf-8')

        return {
            "name": template_name,
            "filename": template_file.name,
            "content": content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@router.get("/status")
async def get_service_status():
    """
    Get service status and LaTeX availability
    """
    try:
        output_dir = Path("pdf")
        pdf_files = list(output_dir.glob("*.pdf")) if output_dir.exists() else []

        return {
            "status": "running",
            "pdflatex_available": latex_service.check_pdflatex_available(),
            "total_compilations": len(pdf_files),
            "output_directory_exists": output_dir.exists(),
            "log_files": len(list(output_dir.glob("*.log"))) if output_dir.exists() else 0
        }

    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_files():
    """
    Clean up old compilation files
    """
    try:
        import time

        output_dir = Path("pdf")
        if not output_dir.exists():
            return {"message": "No files to clean up"}

        current_time = time.time()
        cleanup_age = 24 * 60 * 60  # 24 hours

        deleted_files = []
        for file_path in output_dir.glob("*"):
            if file_path.is_file() and current_time - file_path.stat().st_mtime > cleanup_age:
                file_path.unlink()
                deleted_files.append(file_path.name)

        return {
            "message": f"Cleaned up {len(deleted_files)} files",
            "deleted_files": deleted_files
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")