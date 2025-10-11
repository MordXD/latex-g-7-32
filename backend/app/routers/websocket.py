import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.models.compilation import CompilationProgress, CompilationStatus

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections and data"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.compilation_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket) -> str:
        """Accept a WebSocket connection and return connection ID"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket

        # Send welcome message
        await self.send_message(connection_id, {
            "type": "connected",
            "message": "Connected to LaTeX compilation service",
            "connection_id": connection_id
        })

        return connection_id

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Cancel any running compilation for this connection
        if connection_id in self.compilation_tasks:
            task = self.compilation_tasks[connection_id]
            if not task.done():
                task.cancel()
            del self.compilation_tasks[connection_id]

    async def send_message(self, connection_id: str, message: dict):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        for connection_id in list(self.active_connections.keys()):
            await self.send_message(connection_id, message)

    async def send_progress(self, connection_id: str, progress: CompilationProgress):
        """Send compilation progress update"""
        await self.send_message(connection_id, {
            "type": "progress",
            "data": progress.dict()
        })

# Global connection manager
manager = ConnectionManager()

async def run_compilation_with_progress(
    content: str,
    connection_id: str,
    compilation_id: str,
    compiler_options: dict = None
):
    """
    Run LaTeX compilation with real-time progress updates
    """
    from app.services.latex_service import latex_service

    try:
        # Start compilation
        await manager.send_progress(
            connection_id,
            CompilationProgress(
                compilation_id=compilation_id,
                status=CompilationStatus.COMPILING,
                progress=0.1,
                message="Starting LaTeX compilation..."
            )
        )

        # Simulate progress steps during actual compilation
        steps = [
            (0.2, "Preparing LaTeX environment..."),
            (0.3, "First compilation pass..."),
            (0.5, "Running BibTeX if needed..."),
            (0.7, "Second compilation pass..."),
            (0.9, "Final compilation pass..."),
            (1.0, "Finalizing PDF...")
        ]

        # Send progress updates
        for progress_value, message in steps:
            await manager.send_progress(
                connection_id,
                CompilationProgress(
                    compilation_id=compilation_id,
                    status=CompilationStatus.COMPILING,
                    progress=progress_value,
                    message=message
                )
            )
            await asyncio.sleep(0.5)  # Small delay to show progress

        # Run actual compilation
        result = latex_service.compile_latex_document(
            content=content,
            compiler_options=compiler_options
        )

        # Send final result
        status = CompilationStatus.SUCCESS if result.success else CompilationStatus.ERROR
        await manager.send_progress(
            connection_id,
            CompilationProgress(
                compilation_id=compilation_id,
                status=status,
                progress=1.0,
                message=result.message,
                warnings=result.warnings,
                error=result.error
            )
        )

        # Send complete response
        await manager.send_message(connection_id, {
            "type": "compilation_complete",
            "compilation_id": compilation_id,
            "result": result.dict()
        })

    except asyncio.CancelledError:
        await manager.send_progress(
            connection_id,
            CompilationProgress(
                compilation_id=compilation_id,
                status=CompilationStatus.ERROR,
                message="Compilation cancelled"
            )
        )
        logger.info(f"Compilation {compilation_id} cancelled")
    except Exception as e:
        logger.error(f"Compilation error: {e}")
        await manager.send_progress(
            connection_id,
            CompilationProgress(
                compilation_id=compilation_id,
                status=CompilationStatus.ERROR,
                message=f"Compilation failed: {str(e)}",
                error=str(e)
            )
        )

@router.websocket("/compile")
async def websocket_compile_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time LaTeX compilation
    """
    connection_id = await manager.connect(websocket)
    logger.info(f"WebSocket connected: {connection_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")
            logger.debug(f"Received {message_type} from {connection_id}")

            if message_type == "compile":
                # Handle compilation request
                content = message.get("content")
                file_path = message.get("file_path")
                compiler_options = message.get("compiler_options", {})

                if not content and not file_path:
                    await manager.send_message(connection_id, {
                        "type": "error",
                        "message": "Either content or file_path must be provided"
                    })
                    continue

                # Generate compilation ID
                compilation_id = str(uuid.uuid4())

                # Cancel any existing compilation for this connection
                if connection_id in manager.compilation_tasks:
                    existing_task = manager.compilation_tasks[connection_id]
                    if not existing_task.done():
                        existing_task.cancel()

                # Start new compilation task
                compilation_task = asyncio.create_task(
                    run_compilation_with_progress(
                        content=content if content else "",
                        connection_id=connection_id,
                        compilation_id=compilation_id,
                        compiler_options=compiler_options
                    )
                )
                manager.compilation_tasks[connection_id] = compilation_task

                # Send compilation started message
                await manager.send_message(connection_id, {
                    "type": "compilation_started",
                    "compilation_id": compilation_id
                })

            elif message_type == "cancel":
                # Cancel current compilation
                if connection_id in manager.compilation_tasks:
                    task = manager.compilation_tasks[connection_id]
                    if not task.done():
                        task.cancel()
                        await manager.send_message(connection_id, {
                            "type": "compilation_cancelled"
                        })
                else:
                    await manager.send_message(connection_id, {
                        "type": "error",
                        "message": "No compilation in progress"
                    })

            elif message_type == "ping":
                # Respond to ping with pong (keepalive)
                await manager.send_message(connection_id, {
                    "type": "pong"
                })

            else:
                await manager.send_message(connection_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)

@router.get("/status")
async def get_websocket_status():
    """
    Get WebSocket service status
    """
    return {
        "active_connections": len(manager.active_connections),
        "active_compilations": len([
            task for task in manager.compilation_tasks.values()
            if not task.done()
        ]),
        "connections": list(manager.active_connections.keys())
    }