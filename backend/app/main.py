from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator
from app.routers import compilation, websocket
from app.services import latex_service
from app.models.compilation import CompilationStatus

load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting FastAPI LaTeX compilation service")
    # Ensure directories exist
    os.makedirs("pdf", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    yield
    # Shutdown
    logger.info("Shutting down FastAPI LaTeX compilation service")

app = FastAPI(
    title="LaTeX Compilation API",
    description="FastAPI backend for compiling LaTeX documents with ГОСТ 7-32 templates",
    version="1.0.0",
    lifespan=lifespan
)
Instrumentator().instrument(app).expose(app)
# Configure CORS
origins = os.getenv("CORS_ORIGINS", '["http://localhost:3000"]').replace(" ", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(compilation.router, prefix="/api", tags=["compilation"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Mount static files for PDF serving
app.mount("/pdf", StaticFiles(directory="pdf"), name="pdf")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LaTeX Compilation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pdflatex_available": latex_service.check_pdflatex_available()
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )