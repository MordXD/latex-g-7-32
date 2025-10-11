from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
import time

class CompilationStatus(str, Enum):
    PENDING = "pending"
    COMPILING = "compiling"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

class CompilationRequest(BaseModel):
    content: Optional[str] = None
    file_path: Optional[str] = None
    compiler_options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "interaction": "nonstopmode",
            "shell_escape": False,
            "output_directory": "pdf"
        }
    )

class CompilationResponse(BaseModel):
    success: bool
    status: CompilationStatus
    message: str
    pdf_url: Optional[str] = None
    compilation_time: float
    warnings: Optional[str] = None
    error: Optional[str] = None
    output: Optional[str] = None
    log_file: Optional[str] = None

class CompilationProgress(BaseModel):
    compilation_id: str
    status: CompilationStatus
    progress: Optional[float] = None
    message: str
    timestamp: float = Field(default_factory=time.time)
    warnings: Optional[str] = None
    error: Optional[str] = None

class LaTeXFileInfo(BaseModel):
    file_path: str
    file_size: int
    last_modified: float
    content_preview: str

class CompilationHistory(BaseModel):
    compilation_id: str
    timestamp: float
    status: CompilationStatus
    compilation_time: float
    success: bool
    error_message: Optional[str] = None