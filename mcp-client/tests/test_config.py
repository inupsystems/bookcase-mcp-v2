"""Tests for MCP Client configuration module."""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_client.config import ConnectionType, MCPConfig, ServerConfig


class TestServerConfig:
    """Test ServerConfig class."""
    
    def test_basic_config(self):
        """Test basic server configuration."""
        config = ServerConfig(
            command="python",
            args=["-m", "server"],
            env={"API_KEY": "test"},
            type=ConnectionType.STDIO,
            timeout=5000
        )
        
        assert config.command == "python"
        assert config.args == ["-m", "server"]
        assert config.env == {"API_KEY": "test"}
        assert config.type == ConnectionType.STDIO
        assert config.timeout == 5000
        assert config.get_timeout_seconds() == 5.0
    
    def test_http_config(self):
        """Test HTTP server configuration."""
        config = ServerConfig(
            command="python",
            type=ConnectionType.HTTP,
            host="localhost",
            port=8000
        )
        
        assert config.type == ConnectionType.HTTP
        assert config.host == "localhost"
        assert config.port == 8000
    
    def test_validation_errors(self):
        """Test configuration validation errors."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            ServerConfig(command="test", timeout=-1)
        
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerConfig(command="test", port=70000)


class TestMCPConfig:
    """Test MCPConfig class."""
    
    def test_basic_config(self):
        """Test basic MCP configuration."""
        servers = {
            "test_server": ServerConfig(
                command="python",
                args=["-m", "test_server"]
            )
        }
        
        config = MCPConfig(servers=servers)
        
        assert len(config.servers) == 1
        assert "test_server" in config.servers
        assert config.default_timeout == 30000
        assert config.retry_attempts == 3
    
    def test_from_file_nested_format(self):
        """Test loading config from file with nested format."""
        config_data = {
            "servers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "env": {"MEMORY_FILE_PATH": "memory.txt"},
                    "type": "stdio"
                }
            },
            "default_timeout": 15000
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = MCPConfig.from_file(config_path)
            
            assert len(config.servers) == 1
            assert "memory" in config.servers
            assert config.servers["memory"].command == "npx"
            assert config.default_timeout == 15000
        finally:
            Path(config_path).unlink()
    
    def test_from_file_flat_format(self):
        """Test loading config from file with flat format (like mcp-exemplo.json)."""
        config_data = {
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
                "env": {"MEMORY_FILE_PATH": "memory.txt"},
                "type": "stdio"
            },
            "api_server": {
                "command": "./server.sh",
                "type": "http",
                "host": "localhost",
                "port": 8000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = MCPConfig.from_file(config_path)
            
            assert len(config.servers) == 2
            assert "memory" in config.servers
            assert "api_server" in config.servers
            assert config.servers["memory"].command == "npx"
            assert config.servers["api_server"].type == ConnectionType.HTTP
        finally:
            Path(config_path).unlink()
    
    def test_file_not_found(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            MCPConfig.from_file("nonexistent.json")
    
    def test_invalid_json(self):
        """Test error with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                MCPConfig.from_file(config_path)
        finally:
            Path(config_path).unlink()
    
    def test_validation_errors(self):
        """Test configuration validation."""
        config = MCPConfig(servers={
            "http_server": ServerConfig(
                command="test",
                type=ConnectionType.HTTP
                # Missing host and port
            ),
            "socket_server": ServerConfig(
                command="test",
                type=ConnectionType.SOCKET
                # Missing socket_path
            )
        })
        
        issues = config.validate_server_configs()
        
        assert "http_server" in issues
        assert "socket_server" in issues
        assert any("host" in issue for issue in issues["http_server"])
        assert any("port" in issue for issue in issues["http_server"])
        assert any("socket_path" in issue for issue in issues["socket_server"])
    
    def test_server_operations(self):
        """Test server configuration operations."""
        servers = {
            "server1": ServerConfig(command="test1"),
            "server2": ServerConfig(command="test2")
        }
        
        config = MCPConfig(servers=servers)
        
        assert config.get_server_names() == ["server1", "server2"]
        assert config.get_server_config("server1").command == "test1"
        assert config.get_server_config("nonexistent") is None
