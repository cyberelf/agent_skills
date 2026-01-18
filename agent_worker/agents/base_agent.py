"""
Base Agent Interface

Defines the abstract interface for all coding agents.
This allows easy extension to support different AI backends.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class AgentException(Exception):
    """Base exception for agent errors"""
    pass


class BaseAgent(ABC):
    """Abstract base class for coding agents"""
    
    def __init__(self, config, run_config, logger: logging.Logger):
        """
        Initialize agent
        
        Args:
            config: Main configuration object
            run_config: Run-specific configuration
            logger: Logger instance
        """
        self.config = config
        self.run_config = run_config
        self.logger = logger
    
    @abstractmethod
    def get_execution_script(self) -> str:
        """
        Get the execution script content for this agent
        
        Returns:
            Path to execution script
        """
        pass
    
    @abstractmethod
    def execute(self, container, docker_manager) -> Dict[str, Any]:
        """
        Execute the agent in a container
        
        Args:
            container: Docker container object
            docker_manager: DockerManager instance
        
        Returns:
            Dictionary with execution results:
            {
                'exit_code': int,
                'token_usage': {'total': int, 'input': int, 'output': int},
                'output': str
            }
        """
        pass
    
    @abstractmethod
    def parse_output(self, output: str) -> Dict[str, Any]:
        """
        Parse agent output for statistics
        
        Args:
            output: Raw output from agent execution
        
        Returns:
            Dictionary with parsed statistics
        """
        pass
    
    def create_task_file(self) -> None:
        """Create task description file in run directory"""
        self.run_config.create_task_file()
        self.logger.info(f"📝 Task file created: {self.run_config.task_file}")
