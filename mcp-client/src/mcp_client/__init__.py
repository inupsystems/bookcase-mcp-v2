"""MCP Client - A Python client for Model Context Protocol servers."""

__version__ = "0.1.0"
__author__ = "MCP Client Team"
__email__ = "team@example.com"

try:
    from .client import MCPClient
    from .config import MCPConfig, ServerConfig
    from .connection_manager import ConnectionManager
    from .tool_discovery import ToolDiscovery
    from .tool_executor import ToolExecutor
    from .models import Tool, ToolInvocation, ToolResult, ServerInfo
    
    __all__ = [
        "MCPClient",
        "MCPConfig", 
        "ServerConfig",
        "ConnectionManager",
        "ToolDiscovery",
        "ToolExecutor",
        "Tool",
        "ToolInvocation", 
        "ToolResult",
        "ServerInfo",
    ]
except ImportError:
    # Handle import errors gracefully during development
    __all__ = []
