"""Configuration models and validation for MCP Client."""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ConnectionType(str, Enum):
    """Supported connection types for MCP servers."""
    STDIO = "stdio"
    SOCKET = "socket"
    HTTP = "http"


class ServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    
    command: str = Field(..., description="Command to execute the server")
    args: List[str] = Field(default_factory=list, description="Arguments for the command")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cwd: Optional[str] = Field(None, description="Working directory for the server")
    type: ConnectionType = Field(ConnectionType.STDIO, description="Connection type")
    timeout: int = Field(30000, description="Timeout in milliseconds")
    
    # HTTP-specific settings
    host: Optional[str] = Field(None, description="Host for HTTP connections")
    port: Optional[int] = Field(None, description="Port for HTTP connections")
    
    # Socket-specific settings
    socket_path: Optional[str] = Field(None, description="Path for Unix socket connections")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v
    
    @validator('port')
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    def get_timeout_seconds(self) -> float:
        """Get timeout in seconds."""
        return self.timeout / 1000.0


class MCPConfig(BaseModel):
    """Main configuration for MCP Client."""
    
    servers: Dict[str, ServerConfig] = Field(..., description="Server configurations")
    
    # Global settings
    default_timeout: int = Field(30000, description="Default timeout in milliseconds")
    retry_attempts: int = Field(3, description="Number of retry attempts for failed connections")
    retry_delay: float = Field(1.0, description="Delay between retry attempts in seconds")
    tool_cache_ttl: int = Field(300, description="Tool cache TTL in seconds")
    
    @validator('servers')
    def validate_servers(cls, v):
        if not v:
            raise ValueError('At least one server must be configured')
        return v
    
    @validator('retry_attempts')
    def validate_retry_attempts(cls, v):
        if v < 0:
            raise ValueError('Retry attempts must be non-negative')
        return v
    
    @validator('retry_delay')
    def validate_retry_delay(cls, v):
        if v < 0:
            raise ValueError('Retry delay must be non-negative')
        return v
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "MCPConfig":
        """Load configuration from JSON file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle the format from mcp-exemplo.json (direct server configs)
            if 'servers' not in data:
                # Convert flat format to nested format
                data = {'servers': data}
            
            return cls(**data)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")
    
    def to_file(self, config_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        config_path = Path(config_path)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.dict(), f, indent=2, ensure_ascii=False)
    
    def get_server_names(self) -> List[str]:
        """Get list of configured server names."""
        return list(self.servers.keys())
    
    def get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """Get configuration for a specific server."""
        return self.servers.get(server_name)
    
    def validate_server_configs(self) -> Dict[str, List[str]]:
        """Validate all server configurations and return issues."""
        issues = {}
        
        for name, config in self.servers.items():
            server_issues = []
            
            # Check required fields for each connection type
            if config.type == ConnectionType.HTTP:
                if not config.host:
                    server_issues.append("HTTP servers require 'host' field")
                if not config.port:
                    server_issues.append("HTTP servers require 'port' field")
            
            elif config.type == ConnectionType.SOCKET:
                if not config.socket_path:
                    server_issues.append("Socket servers require 'socket_path' field")
            
            # Check if command exists (basic validation)
            if not config.command:
                server_issues.append("Command cannot be empty")
            
            if server_issues:
                issues[name] = server_issues
        
        return issues
