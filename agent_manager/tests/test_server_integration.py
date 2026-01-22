"""
Integration tests for server execution mode
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from agent_worker.config import Config, RunConfig
from agent_worker.agents.server_agent import ServerAgent
from agent_worker.server_client import ServerClient, ServerClientException


@pytest.fixture
def mock_config():
    """Create mock configuration"""
    config = MagicMock()
    config.server_url = "http://localhost:8000"
    config.server_api_key = "test-key"
    config.project_path = Path("/tmp/test")
    config.branch_name = "test-branch"
    config.task_description = "Test task"
    config.timeout = 300
    return config


@pytest.fixture
def mock_run_config():
    """Create mock run configuration"""
    run_config = MagicMock()
    run_config.run_id = "test-run-123"
    return run_config


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    return MagicMock()


@pytest.mark.asyncio
async def test_server_client_health_check():
    """Test server client health check"""
    client = ServerClient("http://localhost:8000")
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"status": "healthy"})
        mock_response.raise_for_status = MagicMock()
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.health_check()
        assert result["status"] == "healthy"


@pytest.mark.asyncio
async def test_server_client_submit_task():
    """Test task submission"""
    client = ServerClient("http://localhost:8000")
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "task_id": "test-123",
            "session_id": "session-456",
            "status": "running"
        })
        mock_response.raise_for_status = MagicMock()
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        result = await client.submit_task(
            task_id="test-123",
            prompt="Test prompt",
            workspace="/tmp/test"
        )
        
        assert result["task_id"] == "test-123"
        assert result["status"] == "running"


def test_server_agent_initialization(mock_config, mock_run_config, mock_logger):
    """Test ServerAgent initialization"""
    agent = ServerAgent(mock_config, mock_run_config, mock_logger)
    
    assert agent.client is not None
    assert isinstance(agent.client, ServerClient)
    assert agent.stats['turns'] == 0


def test_config_execution_mode():
    """Test configuration with execution mode"""
    config = Config(
        project_path=Path("/tmp/test"),
        branch_name="test",
        task_description="test",
        execution_mode="server",
        server_url="http://localhost:8000"
    )
    
    assert config.execution_mode == "server"
    assert config.server_url == "http://localhost:8000"


def test_config_validation_server_mode_requires_url():
    """Test that server mode requires server_url"""
    with pytest.raises(ValueError, match="server_url is required"):
        Config(
            project_path=Path("/tmp/test"),
            branch_name="test",
            task_description="test",
            execution_mode="server",
            server_url=None
        )


def test_config_validation_invalid_execution_mode():
    """Test that invalid execution mode raises error"""
    with pytest.raises(ValueError, match="Invalid execution_mode"):
        Config(
            project_path=Path("/tmp/test"),
            branch_name="test",
            task_description="test",
            execution_mode="invalid"
        )
