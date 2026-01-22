"""
Server Agent Implementation

Implements the BaseAgent interface for Claude Code Server execution.
Uses the ServerClient to submit tasks via REST API and stream progress via WebSocket.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import sys

from .base_agent import BaseAgent, AgentException

# Import ServerClient from parent package
sys.path.insert(0, str(Path(__file__).parent.parent))
from server_client import ServerClient, ServerClientException


class ServerAgent(BaseAgent):
    """Agent implementation for Claude Code Server"""
    
    def __init__(self, config, run_config, logger: logging.Logger):
        super().__init__(config, run_config, logger)
        
        # Create server client
        self.client = ServerClient(
            base_url=config.server_url,
            api_key=config.server_api_key,
            timeout=30
        )
        
        # Track statistics
        self.stats = {
            'turns': 0,
            'tokens_used': 0,
            'tokens_input': 0,
            'tokens_output': 0,
            'files_modified': 0,
            'elapsed_time_ms': 0
        }
    
    def get_execution_script(self) -> str:
        """Server agent doesn't use scripts"""
        return ""
    
    def execute(self, container, docker_manager) -> Dict[str, Any]:
        """
        Execute task via Claude Code Server
        
        Note: This method is synchronous but runs async code internally.
        The container and docker_manager parameters are not used in server mode.
        
        Args:
            container: Unused (kept for interface compatibility)
            docker_manager: Unused (kept for interface compatibility)
        
        Returns:
            Dictionary with execution results
        """
        try:
            self.logger.info("🌐 Executing task via Claude Code Server...")
            
            # Run async execution
            result = asyncio.run(self._execute_async())
            
            return result
        
        except Exception as e:
            raise AgentException(f"Server execution failed: {e}")
    
    async def _execute_async(self):
        """Async execution of task"""
        try:
            # Check server health
            await self._check_server_health()
            
            # Submit task
            task_response = await self._submit_task()
            task_id = task_response['task_id']
            
            self.logger.info(f"✅ Task submitted: {task_id}")
            self.logger.info(f"📡 Session: {task_response['session_id']}")
            
            # Stream progress
            await self._stream_progress(task_id)
            
            # Return results
            return {
                'exit_code': 0,
                'token_usage': {
                    'total': self.stats['tokens_used'],
                    'input': self.stats['tokens_input'],
                    'output': self.stats['tokens_output']
                },
                'output': f"Task completed via server. Tokens: {self.stats['tokens_used']}, "
                         f"Files: {self.stats['files_modified']}, "
                         f"Turns: {self.stats['turns']}"
            }
        
        except ServerClientException as e:
            self.logger.error(f"❌ Server error: {e}")
            raise AgentException(str(e))
    
    async def _check_server_health(self):
        """Check if server is healthy"""
        try:
            health = await self.client.health_check()
            self.logger.info(f"🏥 Server health: {health['status']}")
            self.logger.info(f"   Active sessions: {health['active_sessions']}")
            self.logger.info(f"   Active tasks: {health['active_tasks']}")
        
        except ServerClientException as e:
            raise AgentException(f"Server health check failed: {e}")
    
    async def _submit_task(self) -> Dict[str, Any]:
        """Submit task to server"""
        try:
            # Build task options
            options = {
                'allowed_tools': ['Read', 'Write', 'Edit', 'Bash'],
                'permission_mode': 'acceptEdits',
                'max_turns': 50,
                'timeout': self.config.timeout,
            }
            
            # Create task file content as prompt
            task_prompt = self._build_task_prompt()
            
            # Submit to server
            return await self.client.submit_task(
                task_id=self.run_config.run_id,
                prompt=task_prompt,
                workspace=str(self.config.project_path),
                options=options
            )
        
        except ServerClientException as e:
            raise AgentException(f"Failed to submit task: {e}")
    
    def _build_task_prompt(self) -> str:
        """Build comprehensive task prompt"""
        prompt = f"""I have a task for you. Please complete the following:

# Task Description
{self.config.task_description}

# Instructions
- Analyze the codebase in the current workspace
- Implement the required changes
- Test your changes if applicable
- Follow best practices and code quality standards

# Context
- Task ID: {self.run_config.run_id}
- Branch: {self.config.branch_name}
- Timestamp: {datetime.now().isoformat()}

Please work autonomously until the task is complete. When done, provide a summary of what you've accomplished.
"""
        return prompt
    
    async def _stream_progress(self, task_id: str):
        """Stream and process task progress"""
        try:
            async for event in self.client.stream_progress(task_id):
                await self._handle_event(event)
        
        except ServerClientException as e:
            raise AgentException(f"Failed to stream progress: {e}")
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle incoming event from server"""
        event_type = event.get('type')
        data = event.get('data', {})
        
        if event_type == 'message':
            self._handle_message_event(data)
        
        elif event_type == 'tool_use':
            self._handle_tool_use_event(data)
        
        elif event_type == 'tool_result':
            self._handle_tool_result_event(data)
        
        elif event_type == 'progress':
            self._handle_progress_event(data)
        
        elif event_type == 'complete':
            self._handle_complete_event(data)
        
        elif event_type == 'error':
            self._handle_error_event(data)
    
    def _handle_message_event(self, data: Dict[str, Any]):
        """Handle message event"""
        msg_type = data.get('message_type', '')
        content = data.get('content', '')
        
        if msg_type == 'assistant':
            # Show abbreviated assistant message
            preview = content[:100] + '...' if len(content) > 100 else content
            self.logger.info(f"💬 Claude: {preview}")
        
        elif msg_type == 'thinking':
            self.logger.debug(f"💭 Thinking: {content[:80]}...")
    
    def _handle_tool_use_event(self, data: Dict[str, Any]):
        """Handle tool use event"""
        tool_name = data.get('tool_name', '')
        self.logger.info(f"🔧 Using tool: {tool_name}")
    
    def _handle_tool_result_event(self, data: Dict[str, Any]):
        """Handle tool result event"""
        is_error = data.get('is_error', False)
        if is_error:
            self.logger.warning(f"⚠️  Tool execution had errors")
        else:
            self.logger.debug(f"✅ Tool executed successfully")
    
    def _handle_progress_event(self, data: Dict[str, Any]):
        """Handle progress update event"""
        # Update statistics
        self.stats['turns'] = data.get('turns', 0)
        self.stats['tokens_used'] = data.get('tokens_used', 0)
        self.stats['tokens_input'] = data.get('tokens_input', 0)
        self.stats['tokens_output'] = data.get('tokens_output', 0)
        self.stats['files_modified'] = data.get('files_modified', 0)
        self.stats['elapsed_time_ms'] = data.get('elapsed_time_ms', 0)
        
        # Log progress
        self.logger.info(
            f"📊 Progress: turns={self.stats['turns']}, "
            f"tokens={self.stats['tokens_used']}, "
            f"files={self.stats['files_modified']}, "
            f"time={self.stats['elapsed_time_ms']}ms"
        )
    
    def _handle_complete_event(self, data: Dict[str, Any]):
        """Handle completion event"""
        summary = data.get('summary', '')
        exit_code = data.get('exit_code', 0)
        
        if exit_code == 0:
            self.logger.info(f"✅ Task completed: {summary}")
        else:
            errors = data.get('errors', [])
            self.logger.error(f"❌ Task failed: {summary}")
            if errors:
                for error in errors:
                    self.logger.error(f"   - {error}")
    
    def _handle_error_event(self, data: Dict[str, Any]):
        """Handle error event"""
        error = data.get('error', 'Unknown error')
        self.logger.error(f"❌ Server error: {error}")
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """
        Parse output (not needed for server mode as stats are tracked in real-time)
        
        Args:
            output: Raw output (unused)
        
        Returns:
            Statistics dictionary
        """
        return {
            'token_usage': {
                'total': self.stats['tokens_used'],
                'input': self.stats['tokens_input'],
                'output': self.stats['tokens_output']
            },
            'conversation_turns': self.stats['turns'],
            'files_modified': self.stats['files_modified']
        }
