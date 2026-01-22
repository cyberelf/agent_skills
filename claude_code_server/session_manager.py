"""
Session Manager

Manages Agent SDK client sessions, including creation, cleanup, and event distribution.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

from .models import SessionStatus, SessionInfo
from .config import config


logger = logging.getLogger(__name__)


class Session:
    """Represents a single Agent SDK session"""
    
    def __init__(
        self,
        session_id: str,
        workspace: str,
        options: ClaudeAgentOptions,
        client: ClaudeSDKClient
    ):
        self.session_id = session_id
        self.workspace = workspace
        self.options = options
        self.client = client
        self.status = SessionStatus.ACTIVE
        self.tasks: list[str] = []
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.event_queues: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()
    
    def add_task(self, task_id: str):
        """Add task to session"""
        self.tasks.append(task_id)
        self.last_activity = datetime.utcnow()
    
    def remove_task(self, task_id: str):
        """Remove task from session"""
        if task_id in self.tasks:
            self.tasks.remove(task_id)
        self.last_activity = datetime.utcnow()
    
    def subscribe_task(self, task_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific task"""
        if task_id not in self.event_queues:
            self.event_queues[task_id] = asyncio.Queue()
        return self.event_queues[task_id]
    
    def unsubscribe_task(self, task_id: str):
        """Unsubscribe from task events"""
        if task_id in self.event_queues:
            del self.event_queues[task_id]
    
    async def publish_event(self, task_id: str, event: Dict[str, Any]):
        """Publish event to task subscribers"""
        if task_id in self.event_queues:
            await self.event_queues[task_id].put(event)
    
    def is_idle(self, idle_timeout_seconds: int) -> bool:
        """Check if session is idle"""
        if len(self.tasks) > 0:
            return False
        
        idle_time = datetime.utcnow() - self.last_activity
        return idle_time.total_seconds() > idle_timeout_seconds
    
    def to_info(self) -> SessionInfo:
        """Convert to SessionInfo model"""
        return SessionInfo(
            session_id=self.session_id,
            tasks=self.tasks.copy(),
            status=self.status,
            created_at=self.created_at,
            last_activity=self.last_activity
        )


class SessionManager:
    """Manages Agent SDK sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("Session manager initialized")
    
    async def start(self):
        """Start session manager"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session manager started")
    
    async def stop(self):
        """Stop session manager and cleanup all sessions"""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all sessions
        async with self._lock:
            for session in self.sessions.values():
                try:
                    await session.client.disconnect()
                    logger.info(f"Disconnected session: {session.session_id}")
                except Exception as e:
                    logger.error(f"Error disconnecting session {session.session_id}: {e}")
            
            self.sessions.clear()
        
        logger.info("Session manager stopped")
    
    async def create_session(
        self,
        session_id: str,
        workspace: str,
        options: Dict[str, Any]
    ) -> Session:
        """Create a new Agent SDK session"""
        
        async with self._lock:
            if session_id in self.sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            # Check concurrent session limit
            if len(self.sessions) >= config.session.max_concurrent:
                raise RuntimeError(
                    f"Maximum concurrent sessions ({config.session.max_concurrent}) reached"
                )
            
            # Convert workspace to Path
            workspace_path = Path(workspace).resolve()
            if not workspace_path.exists():
                raise ValueError(f"Workspace directory does not exist: {workspace}")
            
            # Build ClaudeAgentOptions
            claude_options = ClaudeAgentOptions(
                allowed_tools=options.get("allowed_tools", config.claude_sdk.default_allowed_tools),
                permission_mode=options.get("permission_mode", config.claude_sdk.default_permission_mode),
                max_turns=options.get("max_turns", config.claude_sdk.max_turns),
                model=options.get("model", config.claude_sdk.default_model),
                cwd=str(workspace_path),
                env={"ANTHROPIC_API_KEY": config.anthropic_api_key}
            )
            
            # Create ClaudeSDKClient
            client = ClaudeSDKClient(options=claude_options)
            
            # Connect to Claude
            try:
                await client.connect()
                logger.info(f"Connected to Claude SDK for session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to connect to Claude SDK: {e}")
                raise
            
            # Create session
            session = Session(
                session_id=session_id,
                workspace=str(workspace_path),
                options=claude_options,
                client=client
            )
            
            self.sessions[session_id] = session
            logger.info(f"Created session: {session_id} (total: {len(self.sessions)})")
            
            return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        async with self._lock:
            return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str):
        """Delete a session"""
        async with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            # Disconnect client
            try:
                await session.client.disconnect()
                logger.info(f"Disconnected session: {session_id}")
            except Exception as e:
                logger.error(f"Error disconnecting session {session_id}: {e}")
            
            # Remove from sessions
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id} (remaining: {len(self.sessions)})")
    
    async def list_sessions(self) -> list[SessionInfo]:
        """List all sessions"""
        async with self._lock:
            return [session.to_info() for session in self.sessions.values()]
    
    def get_active_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    async def _cleanup_loop(self):
        """Background task to cleanup idle sessions"""
        logger.info("Session cleanup loop started")
        
        while self._running:
            try:
                await asyncio.sleep(config.session.cleanup_interval_seconds)
                await self._cleanup_idle_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_idle_sessions(self):
        """Clean up idle sessions"""
        async with self._lock:
            idle_sessions = [
                session_id
                for session_id, session in self.sessions.items()
                if session.is_idle(config.session.idle_timeout_seconds)
            ]
            
            for session_id in idle_sessions:
                try:
                    session = self.sessions[session_id]
                    await session.client.disconnect()
                    del self.sessions[session_id]
                    logger.info(f"Cleaned up idle session: {session_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up session {session_id}: {e}")
            
            if idle_sessions:
                logger.info(
                    f"Cleaned up {len(idle_sessions)} idle sessions "
                    f"(remaining: {len(self.sessions)})"
                )


# Global session manager instance
session_manager = SessionManager()
