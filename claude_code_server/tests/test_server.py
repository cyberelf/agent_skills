"""
Integration tests for server API
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from claude_code_server.server import app
from claude_code_server.models import TaskRequest


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "active_sessions" in data


@pytest.mark.asyncio
async def test_readiness_check():
    """Test readiness check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


@pytest.mark.asyncio
@patch("claude_code_server.server.session_manager")
async def test_create_task(mock_session_manager):
    """Test task creation endpoint"""
    # Mock session
    mock_session = MagicMock()
    mock_session.session_id = "test-session"
    mock_session.add_task = MagicMock()
    
    mock_session_manager.create_session = AsyncMock(return_value=mock_session)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        request_data = {
            "task_id": "test-task",
            "prompt": "Test prompt",
            "workspace": "/tmp/test",
            "options": {},
            "session": {"reuse_existing": False}
        }
        
        response = await client.post("/api/v1/tasks", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task"
        assert data["status"] == "running"
        assert "websocket_url" in data


@pytest.mark.asyncio
async def test_task_not_found():
    """Test getting status of non-existent task"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks/nonexistent")
        
        assert response.status_code == 404
