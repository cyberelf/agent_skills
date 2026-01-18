"""
Claude Agent Implementation

Implements the BaseAgent interface for Claude Code execution.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any

from .base_agent import BaseAgent, AgentException


class ClaudeAgent(BaseAgent):
    """Agent implementation for Claude Code"""
    
    def get_execution_script(self) -> str:
        """Return path to agent_inside.sh script"""
        script_path = self.config.project_path / 'agent_worker' / 'container' / 'agent_inside.sh'
        
        if not script_path.exists():
            raise AgentException(f"Agent script not found: {script_path}")
        
        return str(script_path)
    
    def execute(self, container, docker_manager) -> Dict[str, Any]:
        """Execute Claude Code in container"""
        try:
            self.logger.info("🤖 Executing Claude Code agent...")
            
            # Create task file
            self.create_task_file()
            
            # Open log file for real-time writing
            with open(self.run_config.output_file, 'w') as log_file:
                # Execute agent script with streaming
                result = docker_manager.execute_command(
                    ['/workspace/agent_inside.sh'],
                    stream=True,
                    log_file=log_file  # Pass log file for real-time writing
                )
            
            # Parse output for statistics
            stats = self.parse_output(result['output'])
            
            return {
                'exit_code': result['exit_code'],
                'token_usage': stats.get('token_usage', {'total': 0, 'input': 0, 'output': 0}),
                'output': result['output']
            }
            
        except Exception as e:
            raise AgentException(f"Claude Code execution failed: {e}")
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """
        Parse Claude Code output for token usage and other stats
        
        Looks for patterns like:
        - "X tokens used"
        - "input: X tokens"
        - "output: Y tokens"
        """
        stats = {
            'token_usage': {'total': 0, 'input': 0, 'output': 0},
            'conversation_turns': 0
        }
        
        try:
            # Look for token usage patterns
            total_match = re.search(r'(\d+)\s+tokens?\s+used', output, re.IGNORECASE)
            if total_match:
                stats['token_usage']['total'] = int(total_match.group(1))
            
            # Look for input/output token breakdown
            input_match = re.search(r'input.*?(\d+)', output, re.IGNORECASE)
            if input_match:
                stats['token_usage']['input'] = int(input_match.group(1))
            
            output_match = re.search(r'output.*?(\d+)', output, re.IGNORECASE)
            if output_match:
                stats['token_usage']['output'] = int(output_match.group(1))
            
            # Count conversation turns (appearances of "Assistant:" or "Claude:")
            turns = len(re.findall(r'(Assistant:|Claude:)', output, re.IGNORECASE))
            stats['conversation_turns'] = turns
            
            self.logger.debug(f"Parsed stats: {stats}")
            
        except Exception as e:
            self.logger.warning(f"Failed to parse some output statistics: {e}")
        
        return stats
