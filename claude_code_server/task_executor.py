"""
Task Executor

Wraps ClaudeSDKClient to execute tasks and emit events for WebSocket streaming.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)

from .models import (
    TaskStatus,
    TaskProgress,
    TaskResult,
    EventType,
    MessageEvent,
    ToolUseEvent,
    ToolResultEvent,
    ProgressEvent,
    CompleteEvent,
    ErrorEvent,
)
from .session_manager import Session


logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executes tasks using Agent SDK and emits events"""
    
    def __init__(self, session: Session):
        self.session = session
        self.client = session.client
        self.task_id: Optional[str] = None
        self.progress = TaskProgress()
        self.start_time: Optional[datetime] = None
    
    async def execute(self, task_id: str, prompt: str, timeout: int = 3600):
        """
        Execute a task using the Agent SDK
        
        Args:
            task_id: Unique task identifier
            prompt: Task prompt for Claude
            timeout: Task timeout in seconds
        """
        self.task_id = task_id
        self.start_time = datetime.utcnow()
        
        logger.info(f"Starting task execution: {task_id}")
        
        try:
            # Execute with timeout
            await asyncio.wait_for(
                self._execute_task(prompt),
                timeout=timeout
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out after {timeout}s")
            await self._emit_error("Task execution timed out")
            await self._complete_task(success=False, error="Timeout")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            await self._emit_error(str(e))
            await self._complete_task(success=False, error=str(e))
        
        finally:
            # Remove task from session
            self.session.remove_task(task_id)
    
    async def _execute_task(self, prompt: str):
        """Internal task execution"""
        try:
            # Send query to Claude
            await self.client.query(prompt)
            logger.debug(f"Task {self.task_id}: Query sent to Claude")
            
            # Stream messages
            async for message in self.client.receive_response():
                await self._handle_message(message)
                
                # Check if we received final result
                if isinstance(message, ResultMessage):
                    await self._handle_result(message)
                    break
            
            # Mark task complete
            await self._complete_task(success=True)
            
        except Exception as e:
            logger.error(f"Error in task execution: {e}")
            raise
    
    async def _handle_message(self, message):
        """Handle different message types from Agent SDK"""
        
        if isinstance(message, AssistantMessage):
            await self._handle_assistant_message(message)
        
        elif isinstance(message, UserMessage):
            await self._handle_user_message(message)
        
        elif isinstance(message, SystemMessage):
            await self._handle_system_message(message)
        
        elif isinstance(message, ResultMessage):
            # Handled separately in _handle_result
            pass
        
        else:
            logger.debug(f"Unknown message type: {type(message)}")
    
    async def _handle_assistant_message(self, message: AssistantMessage):
        """Handle assistant message"""
        self.progress.turns += 1
        
        # Process content blocks
        for block in message.content:
            if isinstance(block, TextBlock):
                await self._emit_message({
                    "message_type": "assistant",
                    "content": block.text,
                    "model": message.model
                })
            
            elif isinstance(block, ThinkingBlock):
                await self._emit_message({
                    "message_type": "thinking",
                    "content": block.thinking,
                    "signature": block.signature
                })
            
            elif isinstance(block, ToolUseBlock):
                await self._emit_tool_use(block)
            
            elif isinstance(block, ToolResultBlock):
                await self._emit_tool_result(block)
        
        # Emit progress update
        await self._emit_progress()
    
    async def _handle_user_message(self, message: UserMessage):
        """Handle user message"""
        content = message.content if isinstance(message.content, str) else str(message.content)
        
        await self._emit_message({
            "message_type": "user",
            "content": content
        })
    
    async def _handle_system_message(self, message: SystemMessage):
        """Handle system message"""
        await self._emit_message({
            "message_type": "system",
            "subtype": message.subtype,
            "data": message.data
        })
    
    async def _handle_result(self, result: ResultMessage):
        """Handle final result message"""
        
        # Update progress with final statistics
        if result.usage:
            self.progress.tokens_used = result.usage.get("total_tokens", 0)
            self.progress.tokens_input = result.usage.get("input_tokens", 0)
            self.progress.tokens_output = result.usage.get("output_tokens", 0)
        
        self.progress.turns = result.num_turns
        self.progress.elapsed_time_ms = result.duration_ms
        
        # Emit final progress
        await self._emit_progress()
        
        logger.info(
            f"Task {self.task_id} result: "
            f"turns={result.num_turns}, "
            f"tokens={self.progress.tokens_used}, "
            f"duration={result.duration_ms}ms, "
            f"error={result.is_error}"
        )
    
    async def _emit_message(self, data: Dict[str, Any]):
        """Emit message event"""
        event = MessageEvent(
            type=EventType.MESSAGE,
            timestamp=datetime.utcnow(),
            data=data
        )
        await self.session.publish_event(self.task_id, event.model_dump())
    
    async def _emit_tool_use(self, block: ToolUseBlock):
        """Emit tool use event"""
        event = ToolUseEvent(
            type=EventType.TOOL_USE,
            timestamp=datetime.utcnow(),
            data={
                "tool_id": block.id,
                "tool_name": block.name,
                "tool_input": block.input
            }
        )
        await self.session.publish_event(self.task_id, event.model_dump())
    
    async def _emit_tool_result(self, block: ToolResultBlock):
        """Emit tool result event"""
        event = ToolResultEvent(
            type=EventType.TOOL_RESULT,
            timestamp=datetime.utcnow(),
            data={
                "tool_use_id": block.tool_use_id,
                "content": block.content,
                "is_error": block.is_error
            }
        )
        await self.session.publish_event(self.task_id, event.model_dump())
        
        # Count file modifications (approximate)
        if isinstance(block.content, list):
            for item in block.content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if "written successfully" in text.lower() or "modified" in text.lower():
                        self.progress.files_modified += 1
    
    async def _emit_progress(self):
        """Emit progress update event"""
        if self.start_time:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            self.progress.elapsed_time_ms = int(elapsed * 1000)
        
        event = ProgressEvent(
            type=EventType.PROGRESS,
            timestamp=datetime.utcnow(),
            data=self.progress
        )
        await self.session.publish_event(self.task_id, event.model_dump())
    
    async def _emit_error(self, error: str):
        """Emit error event"""
        event = ErrorEvent(
            type=EventType.ERROR,
            timestamp=datetime.utcnow(),
            data={"error": error}
        )
        await self.session.publish_event(self.task_id, event.model_dump())
    
    async def _complete_task(self, success: bool, error: Optional[str] = None):
        """Emit task completion event"""
        result = TaskResult(
            exit_code=0 if success else 1,
            summary="Task completed successfully" if success else f"Task failed: {error}",
            errors=[error] if error else []
        )
        
        event = CompleteEvent(
            type=EventType.COMPLETE,
            timestamp=datetime.utcnow(),
            data=result
        )
        await self.session.publish_event(self.task_id, event.model_dump())
        
        status = "completed" if success else "failed"
        logger.info(f"Task {self.task_id} {status}")
