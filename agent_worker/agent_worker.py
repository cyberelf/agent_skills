"""
Agent Worker - Containerized Coding Agent Orchestrator

A robust tool for orchestrating containerized AI coding agents with support
for multiple backends (Claude Code, etc.) and both local and remote execution.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import Config, RunConfig
from docker_manager import DockerManager, DockerException
from agents.claude_agent import ClaudeAgent
from agents.base_agent import AgentException


class AgentWorkerException(Exception):
    """Base exception for Agent Worker errors"""
    pass


class AgentWorker:
    """Main orchestrator for containerized agent execution"""
    
    def __init__(self, config: Config):
        self.config = config
        self.run_config: Optional[RunConfig] = None
        self.docker_manager: Optional[DockerManager] = None
        self.agent = None
        self.stats = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0,
            'token_usage': {'total': 0, 'input': 0, 'output': 0},
            'loc_changes': {'added': 0, 'removed': 0},
            'files_changed': 0,
            'exit_code': None,
            'errors': []
        }
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with both file and console handlers"""
        self.logger = logging.getLogger('AgentWorker')
        self.logger.setLevel(logging.DEBUG if self.config.debug else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(levelname)s [%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def _setup_run_directory(self):
        """Initialize run directory structure"""
        try:
            self.run_config = RunConfig.create(
                self.config.project_path,
                self.config.task_description,
                self.config.branch_name
            )
            
            # Add file handler for this run
            file_handler = logging.FileHandler(self.run_config.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(levelname)s [%(asctime)s] %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
            
            self.logger.info(f"📁 Run directory: {self.run_config.run_dir}")
            self.logger.info(f"📝 Logs: {self.run_config.log_file}")
            
        except Exception as e:
            raise AgentWorkerException(f"Failed to setup run directory: {e}")
    
    def _validate_prerequisites(self):
        """Validate all prerequisites before execution"""
        self.logger.info("🔍 Validating prerequisites...")
        
        # Check API key
        if not self.config.api_key:
            raise AgentWorkerException(
                "ANTHROPIC_API_KEY not set. Please provide via --api-key or environment variable."
            )
        
        # Check project path
        if not self.config.project_path.exists():
            raise AgentWorkerException(f"Project directory does not exist: {self.config.project_path}")
        
        # Find and validate git repository
        git_root = self._find_git_root(self.config.project_path)
        if not git_root:
            raise AgentWorkerException(f"Not a git repository: {self.config.project_path}")
        
        # Update project path to git root
        self.config.project_path = git_root
        self.logger.info(f"📂 Using git repository root: {git_root}")
        
        # Check for uncommitted changes
        self._check_clean_working_tree()
        
        # Check Docker availability
        try:
            import docker
            client = docker.from_env()
            client.ping()
            self.logger.info("🐳 Docker is available")
        except Exception as e:
            raise AgentWorkerException(f"Docker is not available: {e}")
        
        self.logger.info("✅ Prerequisites validated")
    
    def _find_git_root(self, path: Path) -> Optional[Path]:
        """Find git repository root"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None
    
    def _check_clean_working_tree(self):
        """Ensure git working tree is clean before starting"""
        try:
            import subprocess
            
            # Check for uncommitted changes
            result = subprocess.run(
                ['git', '-C', str(self.config.project_path), 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                self.logger.error("❌ Working tree has uncommitted changes:")
                self.logger.error(result.stdout)
                raise AgentWorkerException(
                    "Git working tree must be clean before running agent. "
                    "Please commit or stash your changes first."
                )
            
            self.logger.info("✅ Git working tree is clean")
            
        except subprocess.CalledProcessError as e:
            raise AgentWorkerException(f"Failed to check git status: {e.stderr}")
    
    def _create_git_branch(self):
        """Create a new git branch for the task"""
        try:
            import subprocess
            
            # Get current branch
            result = subprocess.run(
                ['git', '-C', str(self.config.project_path), 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            self.logger.info(f"🌿 Current branch: {current_branch}")
            
            # Create and checkout new branch
            subprocess.run(
                ['git', '-C', str(self.config.project_path), 'checkout', '-b', self.config.branch_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"✅ Branch {self.config.branch_name} created successfully")
            
        except subprocess.CalledProcessError as e:
            raise AgentWorkerException(f"Failed to create git branch: {e.stderr}")
    
    def _initialize_docker(self):
        """Initialize Docker manager"""
        try:
            self.docker_manager = DockerManager(
                config=self.config,
                run_config=self.run_config,
                logger=self.logger
            )
        except DockerException as e:
            raise AgentWorkerException(f"Failed to initialize Docker: {e}")
    
    def _initialize_agent(self):
        """Initialize the coding agent based on configuration"""
        try:
            if self.config.agent_type == 'claude':
                self.agent = ClaudeAgent(
                    config=self.config,
                    run_config=self.run_config,
                    logger=self.logger
                )
            else:
                raise AgentWorkerException(f"Unknown agent type: {self.config.agent_type}")
            
            self.logger.info(f"🤖 Initialized {self.config.agent_type} agent")
            
        except AgentException as e:
            raise AgentWorkerException(f"Failed to initialize agent: {e}")
    
    def _execute_agent(self):
        """Execute the agent in container"""
        try:
            self.stats['start_time'] = time.time()
            self.logger.info("🚀 Starting agent execution...")
            self.logger.info(f"📋 Task: {self.config.task_description}")
            
            # Build Docker image
            self.docker_manager.build_image()
            
            # Create and start container
            container = self.docker_manager.create_container()
            
            # Copy agent script to container
            self.docker_manager.copy_agent_script(self.agent)
            
            # Execute agent
            result = self.agent.execute(container, self.docker_manager)
            
            self.stats['end_time'] = time.time()
            self.stats['duration_seconds'] = self.stats['end_time'] - self.stats['start_time']
            self.stats['exit_code'] = result.get('exit_code', 0)
            self.stats['token_usage'] = result.get('token_usage', self.stats['token_usage'])
            
            if self.stats['exit_code'] == 0:
                self.logger.info("✅ Agent execution completed successfully")
            else:
                self.logger.error(f"❌ Agent execution failed with exit code {self.stats['exit_code']}")
            
        except (DockerException, AgentException) as e:
            self.stats['errors'].append(str(e))
            self.stats['exit_code'] = 1
            raise AgentWorkerException(f"Agent execution failed: {e}")
        finally:
            self.stats['end_time'] = self.stats['end_time'] or time.time()
            self.stats['duration_seconds'] = self.stats['end_time'] - self.stats['start_time']
    
    def _collect_git_stats(self):
        """Collect git statistics after execution"""
        try:
            import subprocess
            
            # Get changed files count
            result = subprocess.run(
                ['git', '-C', str(self.config.project_path), 'diff', '--name-only', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            self.stats['files_changed'] = len(changed_files)
            
            # Get LOC changes
            result = subprocess.run(
                ['git', '-C', str(self.config.project_path), 'diff', '--shortstat', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout:
                import re
                added = re.search(r'(\d+) insertion', result.stdout)
                removed = re.search(r'(\d+) deletion', result.stdout)
                
                if added:
                    self.stats['loc_changes']['added'] = int(added.group(1))
                if removed:
                    self.stats['loc_changes']['removed'] = int(removed.group(1))
            
            self.logger.info("📊 Git statistics collected")
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to collect git stats: {e}")
    
    def _save_stats(self):
        """Save execution statistics"""
        try:
            stats_data = {
                **self.stats,
                'run_id': self.run_config.run_id,
                'timestamp': datetime.now().isoformat(),
                'task': self.config.task_description,
                'branch': self.config.branch_name,
                'project_path': str(self.config.project_path),
            }
            
            with open(self.run_config.stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
            
            self.logger.info(f"💾 Statistics saved to {self.run_config.stats_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
    
    def _print_report(self):
        """Print execution report"""
        duration_minutes = int(self.stats['duration_seconds'] // 60)
        duration_seconds = int(self.stats['duration_seconds'] % 60)
        
        print("\n" + "═" * 65)
        print("                    AGENT EXECUTION REPORT")
        print("═" * 65)
        print(f"  Branch:           {self.config.branch_name}")
        print(f"  Duration:         {duration_minutes}m {duration_seconds}s")
        print(f"  Exit Code:        {self.stats['exit_code']}")
        print("─" * 65)
        print("  TOKEN USAGE")
        print(f"    Total:          {self.stats['token_usage']['total']}")
        print(f"    Input:          {self.stats['token_usage']['input']}")
        print(f"    Output:         {self.stats['token_usage']['output']}")
        print("─" * 65)
        print("  CODE CHANGES")
        print(f"    Lines Added:    {self.stats['loc_changes']['added']}")
        print(f"    Lines Removed:  {self.stats['loc_changes']['removed']}")
        print(f"    Files Changed:  {self.stats['files_changed']}")
        print("═" * 65)
        
        if self.stats['errors']:
            print("\n⚠️  Errors:")
            for error in self.stats['errors']:
                print(f"  • {error}")
        
        print(f"\n📁 Run directory: {self.run_config.run_dir}")
        print(f"📝 Full logs: {self.run_config.log_file}\n")
    
    def _cleanup(self):
        """Cleanup resources"""
        if self.docker_manager:
            try:
                self.docker_manager.cleanup()
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    def run(self) -> int:
        """Main execution flow"""
        try:
            # Validate prerequisites
            self._validate_prerequisites()
            
            # Setup run directory
            self._setup_run_directory()
            
            # Create git branch
            self._create_git_branch()
            
            # Initialize Docker
            self._initialize_docker()
            
            # Initialize agent
            self._initialize_agent()
            
            # Execute agent
            self._execute_agent()
            
            # Collect git statistics
            self._collect_git_stats()
            
            # Save statistics
            self._save_stats()
            
            # Print report
            self._print_report()
            
            return self.stats['exit_code']
            
        except AgentWorkerException as e:
            self.logger.error(f"❌ Agent worker failed: {e}")
            if self.stats.get('errors') is not None:
                self.stats['errors'].append(str(e))
            return 1
        except KeyboardInterrupt:
            self.logger.warning("⚠️  Interrupted by user")
            return 130
        except Exception as e:
            self.logger.exception(f"💥 Unexpected error: {e}")
            return 1
        finally:
            self._cleanup()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Agent Worker - Containerized Coding Agent Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --task "Fix all ESLint errors"
  %(prog)s --task "Add tests" --branch feature/tests
  %(prog)s --project /path/to/project --task "Refactor auth"
  %(prog)s --agent-type claude --remote-docker tcp://host:2375
        """
    )
    
    parser.add_argument('--project', type=Path, default=Path.cwd(),
                        help='Path to project directory (default: current directory)')
    parser.add_argument('--branch', default=None,
                        help='Git branch name (default: agent-task-<timestamp>)')
    parser.add_argument('--task', required=True,
                        help='Task description for the agent')
    parser.add_argument('--agent-type', default='claude', choices=['claude'],
                        help='Agent type to use (default: claude)')
    parser.add_argument('--api-key',
                        help='Anthropic API key (or set ANTHROPIC_API_KEY)')
    parser.add_argument('--base-url',
                        help='Base URL for Claude API (or set ANTHROPIC_BASE_URL)')
    parser.add_argument('--remote-docker',
                        help='Remote Docker host (e.g., tcp://host:2375)')
    parser.add_argument('--timezone', default=os.getenv('TZ', 'UTC'),
                        help='Timezone for container (default: system timezone)')
    parser.add_argument('--timeout', type=int, default=3600,
                        help='Agent execution timeout in seconds (default: 3600)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--force-rebuild', action='store_true',
                        help='Force rebuild Docker image even if it exists')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    
    args = parser.parse_args()
    
    # Create configuration
    try:
        config = Config.from_args(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Create and run worker
    worker = AgentWorker(config)
    return worker.run()


if __name__ == '__main__':
    sys.exit(main())
