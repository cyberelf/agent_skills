"""
Claude Code Server

FastAPI server providing REST API and WebSocket interface for Claude Code task execution.
"""

import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from . import __version__
from .config import config
from .models import (
    TaskRequest,
    TaskResponse,
    TaskStatusResponse,
    TaskStatus,
    TaskProgress,
    InterruptResponse,
    SessionListResponse,
    HealthResponse,
    HealthStatus,
)
from .session_manager import session_manager
from .task_executor import TaskExecutor


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.server.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


# Track running tasks and server start time
running_tasks: Dict[str, Dict[str, Any]] = {}
server_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app"""
    # Startup
    logger.info("Starting Claude Code Server...")
    logger.info(f"Version: {__version__}")
    
    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Start session manager
    await session_manager.start()
    
    logger.info(f"Server started on {config.server.host}:{config.server.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Claude Code Server...")
    await session_manager.stop()
    logger.info("Server stopped")


# Create FastAPI app
app = FastAPI(
    title="Claude Code Server",
    description="Server for executing Claude Code tasks via the Agent SDK",
    version=__version__,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication dependency (basic implementation)
async def verify_api_key(api_key: str = None) -> bool:
    """Verify API key if authentication is enabled"""
    if not config.api.auth_enabled:
        return True
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if api_key != config.api.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    uptime = int(time.time() - server_start_time)
    
    return HealthResponse(
        status=HealthStatus.HEALTHY,
        version=__version__,
        active_sessions=session_manager.get_active_count(),
        active_tasks=len(running_tasks),
        uptime_seconds=uptime
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Check if session manager is ready
    if session_manager.get_active_count() >= config.session.max_concurrent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server at capacity"
        )
    
    return {"status": "ready"}


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(
    request: TaskRequest,
    authenticated: bool = Depends(verify_api_key)
) -> TaskResponse:
    """
    Submit a new task for execution
    
    Args:
        request: Task request with prompt, workspace, and options
    
    Returns:
        TaskResponse with task_id, session_id, and WebSocket URL
    """
    logger.info(f"Creating task: {request.task_id}")
    
    try:
        # Get or create session
        if request.session.reuse_existing and request.session.session_id:
            session = await session_manager.get_session(request.session.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {request.session.session_id} not found"
                )
            logger.info(f"Reusing session: {session.session_id}")
        else:
            # Generate session ID from task ID
            session_id = f"session-{request.task_id}"
            session = await session_manager.create_session(
                session_id=session_id,
                workspace=request.workspace,
                options=request.options.model_dump()
            )
            logger.info(f"Created new session: {session.session_id}")
        
        # Add task to session
        session.add_task(request.task_id)
        
        # Create task executor and start execution
        executor = TaskExecutor(session)
        task = asyncio.create_task(
            executor.execute(
                task_id=request.task_id,
                prompt=request.prompt,
                timeout=request.options.timeout
            )
        )
        
        # Track running task
        running_tasks[request.task_id] = {
            "task": task,
            "session_id": session.session_id,
            "status": TaskStatus.RUNNING,
            "created_at": datetime.utcnow(),
            "executor": executor
        }
        
        # Build WebSocket URL
        ws_url = f"ws://{config.server.host}:{config.server.port}/ws/tasks/{request.task_id}"
        
        return TaskResponse(
            task_id=request.task_id,
            session_id=session.session_id,
            status=TaskStatus.RUNNING,
            websocket_url=ws_url,
            created_at=datetime.utcnow()
        )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Server error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    authenticated: bool = Depends(verify_api_key)
) -> TaskStatusResponse:
    """
    Get task status and progress
    
    Args:
        task_id: Task identifier
    
    Returns:
        TaskStatusResponse with status, progress, and result
    """
    if task_id not in running_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    task_info = running_tasks[task_id]
    executor = task_info["executor"]
    
    # Determine status
    if task_info["task"].done():
        if task_info["task"].exception():
            status_val = TaskStatus.FAILED
        else:
            status_val = TaskStatus.COMPLETED
    else:
        status_val = task_info["status"]
    
    return TaskStatusResponse(
        task_id=task_id,
        session_id=task_info["session_id"],
        status=status_val,
        progress=executor.progress,
        result=None,  # TODO: Store final result
        created_at=task_info["created_at"],
        updated_at=datetime.utcnow()
    )


@app.post("/api/v1/tasks/{task_id}/interrupt", response_model=InterruptResponse)
async def interrupt_task(
    task_id: str,
    authenticated: bool = Depends(verify_api_key)
) -> InterruptResponse:
    """
    Interrupt a running task
    
    Args:
        task_id: Task identifier
    
    Returns:
        InterruptResponse with interruption status
    """
    if task_id not in running_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    task_info = running_tasks[task_id]
    session = await session_manager.get_session(task_info["session_id"])
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found for task {task_id}"
        )
    
    try:
        # Interrupt the Agent SDK client
        await session.client.interrupt()
        task_info["status"] = TaskStatus.INTERRUPTED
        
        logger.info(f"Interrupted task: {task_id}")
        
        return InterruptResponse(
            task_id=task_id,
            status=TaskStatus.INTERRUPTED,
            interrupted_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error interrupting task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to interrupt task: {str(e)}"
        )


@app.get("/api/v1/sessions", response_model=SessionListResponse)
async def list_sessions(
    authenticated: bool = Depends(verify_api_key)
) -> SessionListResponse:
    """
    List all active sessions
    
    Returns:
        SessionListResponse with list of sessions
    """
    sessions = await session_manager.list_sessions()
    return SessionListResponse(sessions=sessions)


@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(
    session_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Delete a session
    
    Args:
        session_id: Session identifier
    
    Returns:
        Success message
    """
    try:
        await session_manager.delete_session(session_id)
        logger.info(f"Deleted session: {session_id}")
        return {"message": f"Session {session_id} deleted"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for streaming task progress
    
    Args:
        websocket: WebSocket connection
        task_id: Task identifier
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for task: {task_id}")
    
    try:
        # Wait for task to be created
        retries = 10
        while task_id not in running_tasks and retries > 0:
            await asyncio.sleep(0.1)
            retries -= 1
        
        if task_id not in running_tasks:
            await websocket.send_json({
                "type": "error",
                "data": {"error": f"Task {task_id} not found"}
            })
            await websocket.close(code=1008)
            return
        
        task_info = running_tasks[task_id]
        session = await session_manager.get_session(task_info["session_id"])
        
        if not session:
            await websocket.send_json({
                "type": "error",
                "data": {"error": "Session not found"}
            })
            await websocket.close(code=1011)
            return
        
        # Subscribe to task events
        event_queue = session.subscribe_task(task_id)
        
        try:
            # Stream events until completion
            while True:
                event = await event_queue.get()
                await websocket.send_json(event)
                
                # Break on completion
                if event.get("type") == "complete":
                    break
        
        finally:
            # Unsubscribe from events
            session.unsubscribe_task(task_id)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task: {task_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"error": str(e)}
            })
        except:
            pass
    
    finally:
        try:
            await websocket.close()
        except:
            pass


def main():
    """Main entry point for running the server"""
    uvicorn.run(
        "claude_code_server.server:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.server.log_level.lower()
    )


if __name__ == "__main__":
    main()
