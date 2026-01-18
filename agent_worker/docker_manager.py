"""
Docker Manager - Handle container operations for Agent Worker

Supports both local and remote Docker hosts with comprehensive error handling.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import docker
from docker.errors import DockerException as DockerSDKException, BuildError, APIError


class DockerException(Exception):
    """Custom exception for Docker operations"""
    pass


class DockerManager:
    """Manage Docker operations for agent execution"""
    
    def __init__(self, config, run_config, logger: logging.Logger):
        self.config = config
        self.run_config = run_config
        self.logger = logger
        self.container = None
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Docker client (local or remote)"""
        try:
            if self.config.remote_docker:
                self.logger.info(f"🌐 Connecting to remote Docker: {self.config.remote_docker}")
                self.client = docker.DockerClient(base_url=self.config.remote_docker)
            else:
                self.logger.info("🐳 Using local Docker")
                self.client = docker.from_env()
            
            # Test connection
            self.client.ping()
            self.logger.info("✅ Docker connection established")
            
        except DockerSDKException as e:
            raise DockerException(f"Failed to connect to Docker: {e}")
    
    def image_exists(self, tag: str = 'agent-worker:latest') -> bool:
        """Check if Docker image already exists"""
        try:
            self.client.images.get(tag)
            return True
        except DockerSDKException:
            return False
    
    def build_image(self):
        """Build Docker image for agent execution"""
        try:
            # Check if image already exists and skip if not forcing rebuild
            if not self.config.force_rebuild and self.image_exists():
                self.logger.info("✅ Docker image 'agent-worker:latest' already exists (skipping build)")
                self.logger.info("   Use --force-rebuild to rebuild the image")
                return
            
            if self.config.force_rebuild:
                self.logger.info("🔨 Force rebuilding Docker image...")
            else:
                self.logger.info("🔨 Building Docker image...")
            
            # Find Dockerfile in container directory
            container_dir = self.config.project_path / 'agent_worker' / 'container'
            dockerfile_path = container_dir / 'Dockerfile'
            
            if not dockerfile_path.exists():
                raise DockerException(f"Dockerfile not found: {dockerfile_path}")
            
            # Build image
            with open(self.run_config.docker_build_log, 'w') as log_file:
                try:
                    image, build_logs = self.client.images.build(
                        path=str(container_dir),
                        dockerfile='Dockerfile',
                        tag='agent-worker:latest',
                        buildargs={
                            'TZ': self.config.timezone,
                            'CLAUDE_CODE_VERSION': 'latest'
                        },
                        rm=True,
                        forcerm=True
                    )
                    
                    # Write build logs
                    for log_entry in build_logs:
                        if 'stream' in log_entry:
                            log_file.write(log_entry['stream'])
                            log_file.flush()
                    
                    self.logger.info("✅ Docker image built successfully")
                    
                except BuildError as e:
                    for log_entry in e.build_log:
                        if 'stream' in log_entry:
                            log_file.write(log_entry['stream'])
                    raise DockerException(f"Build failed. See {self.run_config.docker_build_log}")
                    
        except DockerSDKException as e:
            raise DockerException(f"Docker build error: {e}")
    
    def create_container(self):
        """Create and start the agent container"""
        try:
            self.logger.info(f"🚀 Creating container: {self.config.container_name}")
            
            # Create volume for command history if needed
            try:
                self.client.volumes.create(name='agent-worker-commandhistory')
            except APIError:
                pass  # Volume already exists
            
            # Environment variables for container
            env_vars = {
                'ANTHROPIC_API_KEY': self.config.api_key,
                'TZ': self.config.timezone,
                'TASK_DESCRIPTION': self.config.task_description,
                'AGENT_RUN_DIR': f'/workspace/.agent_run/{self.run_config.run_id}'
            }
            
            if self.config.base_url:
                env_vars['ANTHROPIC_BASE_URL'] = self.config.base_url
            
            # Create container
            self.container = self.client.containers.create(
                image='agent-worker:latest',
                name=self.config.container_name,
                command='tail -f /dev/null',
                environment=env_vars,
                volumes={
                    str(self.config.project_path): {'bind': '/workspace', 'mode': 'rw'},
                    'agent-worker-commandhistory': {'bind': '/commandhistory', 'mode': 'rw'}
                },
                working_dir='/workspace',
                detach=True,
                tty=True,
                auto_remove=False
            )
            
            # Start container
            self.container.start()
            self.logger.info("✅ Container started successfully")
            
            return self.container
            
        except DockerSDKException as e:
            raise DockerException(f"Failed to create container: {e}")
    
    def copy_agent_script(self, agent):
        """Copy agent execution script to container"""
        try:
            self.logger.info("📋 Copying agent script to container...")
            
            # Get the agent script path from the agent itself
            script_path = agent.get_execution_script()
            
            if not os.path.exists(script_path):
                raise DockerException(f"Agent script not found: {script_path}")
            
            # Use docker cp command for reliability
            cmd = ['docker', 'cp', str(script_path), f'{self.config.container_name}:/workspace/agent_inside.sh']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise DockerException(f"Failed to copy agent script: {result.stderr}")
            
            # Make script executable
            exec_result = self.container.exec_run(['chmod', '+x', '/workspace/agent_inside.sh'])
            if exec_result.exit_code != 0:
                raise DockerException(f"Failed to make script executable: {exec_result.output}")
            
            self.logger.info("✅ Agent script copied successfully")
            
        except DockerSDKException as e:
            raise DockerException(f"Error copying agent script: {e}")
    
    def execute_command(self, command: list, stream: bool = True, log_file=None) -> Dict[str, Any]:
        """Execute a command in the container"""
        try:
            if not self.container:
                raise DockerException("Container not initialized")
            
            if stream:
                exec_instance = self.container.exec_run(
                    command,
                    stream=True,
                    demux=True,
                    environment={
                        'TASK_DESCRIPTION': self.config.task_description,
                        'ANTHROPIC_API_KEY': self.config.api_key,
                        'ANTHROPIC_BASE_URL': self.config.base_url or '',
                        'AGENT_RUN_DIR': f'/workspace/.agent_run/{self.run_config.run_id}'
                    }
                )
                
                # Stream output in real-time
                output_lines = []
                for stdout, stderr in exec_instance.output:
                    if stdout:
                        line = stdout.decode('utf-8')
                        output_lines.append(line)
                        print(line, end='')
                        
                        # Write to log file in real-time if provided
                        if log_file:
                            log_file.write(line)
                            log_file.flush()
                    
                    if stderr:
                        line = stderr.decode('utf-8')
                        output_lines.append(line)
                        print(line, end='', file=sys.stderr)
                        
                        # Write to log file in real-time if provided
                        if log_file:
                            log_file.write(line)
                            log_file.flush()
                
                return {
                    'exit_code': exec_instance.exit_code,
                    'output': ''.join(output_lines)
                }
            else:
                result = self.container.exec_run(command)
                return {
                    'exit_code': result.exit_code,
                    'output': result.output.decode('utf-8')
                }
                
        except DockerSDKException as e:
            raise DockerException(f"Command execution failed: {e}")
    
    def cleanup(self):
        """Stop and remove container"""
        if self.container:
            try:
                self.logger.info("🧹 Cleaning up container...")
                self.container.stop(timeout=10)
                self.container.remove()
                self.logger.info("✅ Container removed")
            except DockerSDKException as e:
                self.logger.warning(f"Cleanup warning: {e}")
