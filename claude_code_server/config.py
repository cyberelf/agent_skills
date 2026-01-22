"""
Configuration management for Claude Code Server

Uses pydantic-settings for environment variable loading and validation.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class ServerConfig(BaseSettings):
    """Server configuration settings"""
    
    model_config = SettingsConfigDict(
        env_prefix='SERVER_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of workers")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    log_level: str = Field(default="INFO", description="Logging level")


class APIConfig(BaseSettings):
    """API configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='API_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    version: str = Field(default="v1", description="API version")
    auth_enabled: bool = Field(default=False, description="Enable authentication")
    auth_type: str = Field(default="bearer", description="Authentication type")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=100, description="Requests per minute")


class ClaudeSDKConfig(BaseSettings):
    """Claude SDK configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='CLAUDE_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    api_key: str = Field(..., description="Anthropic API key")
    base_url: Optional[str] = Field(default=None, description="API base URL")
    default_model: Optional[str] = Field(default=None, description="Default Claude model")
    default_permission_mode: str = Field(default="acceptEdits", description="Default permission mode")
    default_allowed_tools: List[str] = Field(
        default=["Read", "Write", "Edit", "Bash"],
        description="Default allowed tools"
    )
    max_turns: int = Field(default=50, description="Maximum conversation turns")


class SessionConfig(BaseSettings):
    """Session management configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='SESSION_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    max_concurrent: int = Field(default=10, description="Max concurrent sessions")
    idle_timeout_seconds: int = Field(default=1800, description="Session idle timeout")
    cleanup_interval_seconds: int = Field(default=300, description="Cleanup interval")


class TaskConfig(BaseSettings):
    """Task execution configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='TASK_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    default_timeout_seconds: int = Field(default=3600, description="Default task timeout")
    max_queue_size: int = Field(default=100, description="Maximum task queue size")


class StorageConfig(BaseSettings):
    """Storage configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='STORAGE_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    type: str = Field(default="memory", description="Storage type: memory, redis, sqlite")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")


class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='MONITORING_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")
    logging_format: str = Field(default="json", description="Logging format: json, text")


class Config:
    """Main configuration aggregator"""
    
    def __init__(self):
        self.server = ServerConfig()
        self.api = APIConfig()
        self.claude_sdk = ClaudeSDKConfig()
        self.session = SessionConfig()
        self.task = TaskConfig()
        self.storage = StorageConfig()
        self.monitoring = MonitoringConfig()
    
    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from Claude SDK config"""
        return self.claude_sdk.api_key
    
    def validate(self):
        """Validate configuration"""
        if not self.claude_sdk.api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")
        
        if self.api.auth_enabled and not self.api.api_key:
            raise ValueError("API_API_KEY required when authentication is enabled")
        
        return True


# Global config instance
config = Config()
