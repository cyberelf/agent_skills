"""
Configuration Management for Agent Worker

Handles environment variables, command-line arguments, and run-specific settings.
"""

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

# Load .env file if it exists
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

@dataclass
class Config:
    """Main configuration for Agent Worker"""
    
    # Project settings
    project_path: Path
    branch_name: str
    task_description: str
    worktree_path: Optional[Path] = None  # Path to git worktree (if created)
    
    # Agent settings
    agent_type: str = 'claude'
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    # Docker settings
    remote_docker: Optional[str] = None
    timezone: str = 'UTC'
    container_name: Optional[str] = None
    
    # Execution settings
    timeout: int = 3600
    debug: bool = False
    force_rebuild: bool = False
    
    def __post_init__(self):
        """Validate and process configuration"""
        # Ensure project_path is absolute
        self.project_path = self.project_path.resolve()
        
        # Generate branch name if not provided
        if not self.branch_name:
            self.branch_name = f"agent-task-{int(time.time())}"
        
        # Generate container name if not provided
        if not self.container_name:
            self.container_name = f"agent-worker-{int(time.time())}"
        
        # Get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Get base URL from environment if not provided
        if not self.base_url:
            self.base_url = os.getenv('ANTHROPIC_BASE_URL')
    
    @classmethod
    def from_args(cls, args) -> 'Config':
        """Create Config from argparse arguments"""
        return cls(
            project_path=args.project,
            branch_name=args.branch,
            task_description=args.task,
            agent_type=args.agent_type,
            api_key=args.api_key,
            base_url=args.base_url,
            remote_docker=args.remote_docker,
            timezone=args.timezone,
            timeout=args.timeout,
            debug=args.debug,
            force_rebuild=args.force_rebuild
        )


@dataclass
class RunConfig:
    """Run-specific configuration and paths"""
    
    run_id: str
    run_dir: Path
    task_file: Path
    log_file: Path
    output_file: Path
    stats_file: Path
    docker_build_log: Path
    
    task_description: str
    branch_name: str
    
    @classmethod
    def create(cls, project_path: Path, task_description: str, branch_name: str) -> 'RunConfig':
        """Create a new run configuration with directory structure"""
        run_id = f"run-{int(time.time())}"
        run_dir = project_path / '.agent_run' / run_id
        
        # Create run directory
        run_dir.mkdir(parents=True, exist_ok=True)
        
        return cls(
            run_id=run_id,
            run_dir=run_dir,
            task_file=run_dir / 'task.md',
            log_file=run_dir / 'agent-worker.log',
            output_file=run_dir / 'agent-output.log',
            stats_file=run_dir / 'stats.json',
            docker_build_log=run_dir / 'docker-build.log',
            task_description=task_description,
            branch_name=branch_name
        )
    
    def create_task_file(self) -> None:
        """Create the task description file"""
        from datetime import datetime
        
        task_content = f"""# Agent Task Assignment

## Task Description
{self.task_description}

## Instructions
- Complete the task described above
- Make necessary code changes
- Test your changes if possible
- Commit your work with descriptive messages
- Ensure code quality and follow best practices

## Notes
- You have full access to the workspace
- All changes will be tracked via git
- Use appropriate tools and commands as needed

---
Task assigned: {datetime.now().isoformat()}
Branch: {self.branch_name}
"""
        
        self.task_file.write_text(task_content)
