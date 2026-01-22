"""
Unit tests for models
"""

import pytest
from datetime import datetime

from claude_code_server.models import (
    TaskRequest,
    TaskOptions,
    SessionConfig,
    TaskStatus,
    TaskProgress,
    EventType,
)


def test_task_request_defaults():
    """Test TaskRequest with default values"""
    request = TaskRequest(
        task_id="test-123",
        prompt="Test prompt",
        workspace="/workspace"
    )
    
    assert request.task_id == "test-123"
    assert request.prompt == "Test prompt"
    assert request.workspace == "/workspace"
    assert isinstance(request.options, TaskOptions)
    assert isinstance(request.session, SessionConfig)
    assert request.options.allowed_tools == ["Read", "Write", "Edit", "Bash"]
    assert request.options.permission_mode == "acceptEdits"
    assert request.session.reuse_existing is False


def test_task_options():
    """Test TaskOptions configuration"""
    options = TaskOptions(
        allowed_tools=["Read", "Write"],
        permission_mode="plan",
        max_turns=10,
        timeout=1800
    )
    
    assert options.allowed_tools == ["Read", "Write"]
    assert options.permission_mode == "plan"
    assert options.max_turns == 10
    assert options.timeout == 1800


def test_task_progress():
    """Test TaskProgress tracking"""
    progress = TaskProgress(
        turns=5,
        tokens_used=1000,
        tokens_input=600,
        tokens_output=400,
        files_modified=2
    )
    
    assert progress.turns == 5
    assert progress.tokens_used == 1000
    assert progress.files_modified == 2


def test_task_status_enum():
    """Test TaskStatus enum values"""
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.RUNNING == "running"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"
    assert TaskStatus.INTERRUPTED == "interrupted"


def test_event_type_enum():
    """Test EventType enum values"""
    assert EventType.MESSAGE == "message"
    assert EventType.TOOL_USE == "tool_use"
    assert EventType.TOOL_RESULT == "tool_result"
    assert EventType.PROGRESS == "progress"
    assert EventType.COMPLETE == "complete"
    assert EventType.ERROR == "error"
