"""
Server Client for Claude Code Server

Provides async HTTP and WebSocket client for communicating with Claude Code Server.
"""

import asyncio
import logging
from typing import AsyncIterator, Dict, Any, Optional
from pathlib import Path

import aiohttp


logger = logging.getLogger(__name__)


class ServerClientException(Exception):
    """Exception raised by ServerClient"""
    pass


class ServerClient:
    """
    Client for Claude Code Server API
    
    Handles task submission, status queries, and WebSocket streaming.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize server client
        
        Args:
            base_url: Base URL of Claude Code Server (e.g., http://localhost:8000)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = {}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
        
        logger.info(f"Server client initialized: {self.base_url}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health
        
        Returns:
            Health status dict
        
        Raises:
            ServerClientException: If health check fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/health",
                    headers=self.headers
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            raise ServerClientException(f"Health check failed: {e}")
    
    async def submit_task(
        self,
        task_id: str,
        prompt: str,
        workspace: str,
        options: Optional[Dict[str, Any]] = None,
        session_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit a task to the server
        
        Args:
            task_id: Unique task identifier
            prompt: Task prompt for Claude
            workspace: Workspace directory path
            options: Task execution options
            session_config: Session configuration
        
        Returns:
            Task response with task_id, session_id, status, websocket_url
        
        Raises:
            ServerClientException: If submission fails
        """
        workspace_path = Path(workspace).resolve()
        if not workspace_path.exists():
            raise ServerClientException(f"Workspace does not exist: {workspace}")
        
        payload = {
            'task_id': task_id,
            'prompt': prompt,
            'workspace': str(workspace_path),
            'options': options or {},
            'session': session_config or {'reuse_existing': False}
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=payload,
                    headers=self.headers
                ) as response:
                    if response.status == 400:
                        error = await response.json()
                        raise ServerClientException(f"Invalid request: {error.get('detail', 'Unknown error')}")
                    elif response.status == 503:
                        raise ServerClientException("Server at capacity, please retry later")
                    
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"Task submitted: {task_id} -> session {result['session_id']}")
                    return result
        
        except aiohttp.ClientError as e:
            raise ServerClientException(f"Failed to submit task: {e}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task status dict with progress and result
        
        Raises:
            ServerClientException: If query fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 404:
                        raise ServerClientException(f"Task {task_id} not found")
                    
                    response.raise_for_status()
                    return await response.json()
        
        except aiohttp.ClientError as e:
            raise ServerClientException(f"Failed to get task status: {e}")
    
    async def interrupt_task(self, task_id: str) -> Dict[str, Any]:
        """
        Interrupt a running task
        
        Args:
            task_id: Task identifier
        
        Returns:
            Interrupt response
        
        Raises:
            ServerClientException: If interruption fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/v1/tasks/{task_id}/interrupt",
                    headers=self.headers
                ) as response:
                    if response.status == 404:
                        raise ServerClientException(f"Task {task_id} not found")
                    
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"Task interrupted: {task_id}")
                    return result
        
        except aiohttp.ClientError as e:
            raise ServerClientException(f"Failed to interrupt task: {e}")
    
    async def stream_progress(self, task_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream task progress via WebSocket
        
        Args:
            task_id: Task identifier
        
        Yields:
            Event dicts with type, timestamp, and data
        
        Raises:
            ServerClientException: If streaming fails
        """
        ws_url = self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        ws_url = f"{ws_url}/ws/tasks/{task_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(ws_url) as ws:
                    logger.info(f"WebSocket connected for task: {task_id}")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            event = msg.json()
                            yield event
                            
                            # Stop streaming on completion
                            if event.get('type') == 'complete':
                                logger.info(f"Task completed: {task_id}")
                                break
                        
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            raise ServerClientException(f"WebSocket error: {ws.exception()}")
                        
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.info(f"WebSocket closed for task: {task_id}")
                            break
        
        except aiohttp.ClientError as e:
            raise ServerClientException(f"WebSocket connection failed: {e}")
    
    async def list_sessions(self) -> Dict[str, Any]:
        """
        List all active sessions
        
        Returns:
            Sessions list
        
        Raises:
            ServerClientException: If query fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/api/v1/sessions",
                    headers=self.headers
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        
        except aiohttp.ClientError as e:
            raise ServerClientException(f"Failed to list sessions: {e}")
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Deletion confirmation
        
        Raises:
            ServerClientException: If deletion fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.delete(
                    f"{self.base_url}/api/v1/sessions/{session_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 404:
                        raise ServerClientException(f"Session {session_id} not found")
                    
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"Session deleted: {session_id}")
                    return result
        
        except aiohttp.ClientError as e:
            raise ServerClientException(f"Failed to delete session: {e}")
