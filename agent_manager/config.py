"""
Configuration Management for Agent Manager

Handles environment variables, command-line arguments, and run-specific settings.
"""

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Load .env file if it exists
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Main configuration for Agent Manager"""
    
    # Project settings
    project_path: Path
    branch_name: str
    task_description: str
    worktree_path: Optional[Path] = None  # Path to git worktree (if created)
    
    # Claude Code Server settings (required)
    server_url: str = None  # Claude Code Server URL (e.g., http://localhost:8000)
    server_api_key: Optional[str] = None  # API key for server authentication
    
    # Execution settings
    timeout: int = 3600
    debug: bool = False
    
    def __post_init__(self):
        """Validate and process configuration"""
        # Ensure project_path is absolute
        self.project_path = self.project_path.resolve()
        
        # Generate branch name if not provided
        if not self.branch_name:
            self.branch_name = f"agent-task-{int(time.time())}"
        
        # Get server URL from environment if not provided
        if not self.server_url:
            self.server_url = os.getenv('CLAUDE_SERVER_URL')
        
        # Get server API key from environment if not provided
        if not self.server_api_key:
            self.server_api_key = os.getenv('CLAUDE_SERVER_API_KEY')
        
        # Validate server URL is provided
        if not self.server_url:
            raise ValueError(
                "server_url is required. Set CLAUDE_SERVER_URL environment variable "
                "or use --server-url argument"
            )
    
    @classmethod
    def from_args(cls, args) -> 'Config':
        """Create Config from argparse arguments"""
        return cls(
            project_path=args.project,
            branch_name=args.branch,
            task_description=args.task,
            server_url=getattr(args, 'server_url', None),
            server_api_key=getattr(args, 'server_api_key', None),
            timeout=args.timeout,
            debug=args.debug,
        )


@dataclass
class RunConfig:
    """Runtime configuration for a specific agent run"""
    
    run_id: str = field(default_factory=lambda: f"run-{int(time.time())}")
    run_dir: Optional[Path] = None
    log_file: Optional[Path] = None
    
    def __post_init__(self):
        """Setup run directory and log file"""
        if not self.run_dir:
            self.run_dir = Path.cwd() / '.agent_runs' / self.run_id
            self.run_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.log_file:
            self.log_file = self.run_dir / 'agent.log'


class ConfigException(Exception):
    """Configuration-related errors"""
    pass
