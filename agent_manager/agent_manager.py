"""
Agent Manager - AI Coding Agent Orchestrator

Orchestrates AI coding agents via Claude Code Server API.
Manages git branches, executes tasks, and collects comprehensive statistics.
"""

import argparse
import json
import logging
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import Config, RunConfig, ConfigException
from agents.server_agent import ServerAgent
from agents.base_agent import AgentException


class AgentManagerException(Exception):
    """Base exception for Agent Manager errors"""
    pass


class AgentManager:
    """Main orchestrator for AI agent execution via Claude Code Server"""
    
    def __init__(self, config: Config):
        self.config = config
        self.run_config: Optional[RunConfig] = None
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
        self.logger = logging.getLogger('AgentManager')
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
            self.run_config = RunConfig()
            
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
            raise AgentManagerException(f"Failed to setup run directory: {e}")
    
    def _validate_prerequisites(self):
        """Validate all prerequisites before execution"""
        self.logger.info("🔍 Validating prerequisites...")
        
        # Check project path
        if not self.config.project_path.exists():
            raise AgentManagerException(f"Project directory does not exist: {self.config.project_path}")
        
        # Find and validate git repository
        git_root = self._find_git_root(self.config.project_path)
        if not git_root:
            raise AgentManagerException(f"Not a git repository: {self.config.project_path}")
        
        # Update project path to git root
        self.config.project_path = git_root
        self.logger.info(f"📂 Using git repository root: {git_root}")
        
        # Check for uncommitted changes
        self._check_clean_working_tree()
        
        self.logger.info("✅ Prerequisites validated")
    
    def _find_git_root(self, path: Path) -> Optional[Path]:
        """Find git repository root"""
        try:
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
            # Check for uncommitted changes
            result = subprocess.run(
                ['git', '-C', str(self.config.project_path), 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                uncommitted_files = [line.strip() for line in result.stdout.strip().split('\n')]
                raise AgentManagerException(
                    f"Working tree is not clean. Please commit or stash changes first.\n"
                    f"Uncommitted files:\n" + "\n".join(f"  {f}" for f in uncommitted_files[:10]) +
                    (f"\n  ... and {len(uncommitted_files) - 10} more" if len(uncommitted_files) > 10 else "")
                )
            
            self.logger.info("✅ Working tree is clean")
            
        except subprocess.CalledProcessError as e:
            raise AgentManagerException(f"Failed to check git status: {e}")
    
    def _setup_git_branch(self):
        """Create and checkout a new git branch for agent work"""
        try:
            self.logger.info(f"🌿 Creating git branch: {self.config.branch_name}")
            
            # Create new branch from current HEAD
            subprocess.run(
                ['git', '-C', str(self.config.project_path), 'checkout', '-b', self.config.branch_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"✅ Branch created: {self.config.branch_name}")
            
        except subprocess.CalledProcessError as e:
            raise AgentManagerException(f"Failed to create branch: {e.stderr}")
    
    def _initialize_agent(self):
        """Initialize ServerAgent"""
        try:
            self.logger.info(f"🤖 Initializing ServerAgent")
            self.logger.info(f"🌐 Server URL: {self.config.server_url}")
            
            self.agent = ServerAgent(self.config, self.run_config, self.logger)
            
        except Exception as e:
            raise AgentManagerException(f"Failed to initialize agent: {e}")
    
    def _execute_agent(self):
        """Execute the agent via Claude Code Server"""
        try:
            self.stats['start_time'] = time.time()
            self.logger.info("🚀 Starting agent execution...")
            self.logger.info(f"📋 Task: {self.config.task_description}")
            self.logger.info(f"🌐 Using Claude Code Server at {self.config.server_url}")
            
            # Execute agent via server
            result = self.agent.execute(container=None, docker_manager=None)
            
            self.stats['end_time'] = time.time()
            self.stats['duration_seconds'] = self.stats['end_time'] - self.stats['start_time']
            self.stats['exit_code'] = result.get('exit_code', 0)
            self.stats['token_usage'] = result.get('token_usage', self.stats['token_usage'])
            
            # Get additional statistics from agent
            if hasattr(self.agent, 'stats'):
                self.stats['token_usage']['total'] = self.agent.stats.get('total_tokens', 0)
                self.stats['token_usage']['input'] = self.agent.stats.get('input_tokens', 0)
                self.stats['token_usage']['output'] = self.agent.stats.get('output_tokens', 0)
            
            if self.stats['exit_code'] != 0:
                self.stats['errors'].append(f"Agent exited with code {self.stats['exit_code']}")
            
            self.logger.info(f"✅ Agent execution completed in {self.stats['duration_seconds']:.1f}s")
            
        except AgentException as e:
            self.stats['errors'].append(str(e))
            self.stats['exit_code'] = 1
            raise AgentManagerException(f"Agent execution failed: {e}")
        except Exception as e:
            self.stats['errors'].append(str(e))
            self.stats['exit_code'] = 1
            raise AgentManagerException(f"Unexpected error during agent execution: {e}")
    
    def _collect_git_stats(self):
        """Collect git statistics after agent execution"""
        try:
            self.logger.info("📊 Collecting git statistics...")
            
            # Get list of changed files
            result = subprocess.run(
                ['git', '-C', str(self.config.project_path), 'diff', '--name-only', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            changed_files = [f for f in result.stdout.strip().split('\n') if f]
            self.stats['files_changed'] = len(changed_files)
            
            # Get LOC changes
            result = subprocess.run(
                ['git', '-C', str(self.config.project_path), 'diff', '--numstat', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            
            added, removed = 0, 0
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0] != '-' and parts[1] != '-':
                        try:
                            added += int(parts[0])
                            removed += int(parts[1])
                        except ValueError:
                            pass
            
            self.stats['loc_changes']['added'] = added
            self.stats['loc_changes']['removed'] = removed
            
            self.logger.info(f"📝 Changed files: {self.stats['files_changed']}")
            self.logger.info(f"📝 Lines added: {added}, removed: {removed}")
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to collect git statistics: {e}")
    
    def _print_summary(self):
        """Print execution summary"""
        print("\n" + "=" * 65)
        print("  AGENT EXECUTION SUMMARY")
        print("=" * 65)
        print(f"  Status:         {'✅ SUCCESS' if self.stats['exit_code'] == 0 else '❌ FAILED'}")
        print(f"  Duration:       {self.stats['duration_seconds']:.1f}s")
        print(f"  Branch:         {self.config.branch_name}")
        print()
        print("  TOKEN USAGE")
        print(f"    Total:          {self.stats['token_usage']['total']:,}")
        print(f"    Input:          {self.stats['token_usage']['input']:,}")
        print(f"    Output:         {self.stats['token_usage']['output']:,}")
        print()
        print("  CODE CHANGES")
        print(f"    Lines Added:    {self.stats['loc_changes']['added']}")
        print(f"    Lines Removed:  {self.stats['loc_changes']['removed']}")
        print(f"    Files Changed:  {self.stats['files_changed']}")
        print("=" * 65)
        
        if self.stats['errors']:
            print("\n⚠️  Errors:")
            for error in self.stats['errors']:
                print(f"  • {error}")
        
        print(f"\n📁 Run directory: {self.run_config.run_dir}")
        print(f"📝 Full logs: {self.run_config.log_file}")
        
        print(f"\n🌿 Git branch: {self.config.branch_name}")
        print(f"   To review changes: git diff {self.config.branch_name}")
        print(f"   To merge changes:  git merge {self.config.branch_name}")
        print(f"   To delete branch:  git branch -d {self.config.branch_name}\n")
    
    def run(self) -> int:
        """Main execution flow"""
        try:
            self._setup_run_directory()
            self._validate_prerequisites()
            self._setup_git_branch()
            self._initialize_agent()
            self._execute_agent()
            self._collect_git_stats()
            self._print_summary()
            
            return 0 if self.stats['exit_code'] == 0 else 1
            
        except (AgentManagerException, ConfigException, AgentException) as e:
            self.logger.error(f"❌ {e}")
            if self.stats.get('errors'):
                self._print_summary()
            return 1
        except KeyboardInterrupt:
            self.logger.warning("\n⚠️  Interrupted by user")
            return 130
        except Exception as e:
            self.logger.exception(f"❌ Unexpected error: {e}")
            return 1


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Agent Manager - AI Coding Agent Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --task "Fix all ESLint errors"
  %(prog)s --task "Add tests" --branch feature/tests
  %(prog)s --project /path/to/project --task "Refactor auth"
  %(prog)s --server-url http://server:8000 --task "Add feature"
        """
    )
    
    parser.add_argument('--project', type=Path, default=Path.cwd(),
                        help='Path to project directory (default: current directory)')
    parser.add_argument('--branch', default=None,
                        help='Git branch name (default: agent-task-<timestamp>)')
    parser.add_argument('--task', required=True,
                        help='Task description for the agent')
    parser.add_argument('--server-url',
                        help='Claude Code Server URL (required, or set CLAUDE_SERVER_URL)')
    parser.add_argument('--server-api-key',
                        help='Claude Code Server API key (or set CLAUDE_SERVER_API_KEY)')
    parser.add_argument('--timeout', type=int, default=3600,
                        help='Agent execution timeout in seconds (default: 3600)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--version', action='version', version='%(prog)s 3.0.0')
    
    args = parser.parse_args()
    
    # Create configuration
    try:
        config = Config.from_args(args)
    except Exception as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        return 1
    
    # Create and run manager
    manager = AgentManager(config)
    return manager.run()


if __name__ == '__main__':
    sys.exit(main())
