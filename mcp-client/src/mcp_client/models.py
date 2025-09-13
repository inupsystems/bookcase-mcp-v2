"""Models for MCP protocol communication."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ServerStatus(str, Enum):
    """Status of MCP server connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    TIMEOUT = "timeout"


class ToolParameter(BaseModel):
    """Model for tool parameter definition."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    param_schema: Optional[Dict[str, Any]] = Field(None, alias="schema")


class Tool(BaseModel):
    """Model for MCP tool definition."""
    name: str
    description: Optional[str] = None
    parameters: List[ToolParameter] = Field(default_factory=list)
    input_schema: Optional[Dict[str, Any]] = None
    server_name: Optional[str] = None
    
    def validate_parameters(self, inputs: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate input parameters against tool schema."""
        errors = {}
        
        # Check required parameters
        required_params = [p.name for p in self.parameters if p.required]
        missing_params = [p for p in required_params if p not in inputs]
        if missing_params:
            errors['missing'] = missing_params
        
        # Check parameter types (basic validation)
        type_errors = []
        for param in self.parameters:
            if param.name in inputs:
                value = inputs[param.name]
                expected_type = param.type
                
                # Basic type checking
                if expected_type == "string" and not isinstance(value, str):
                    type_errors.append(f"{param.name}: expected string, got {type(value).__name__}")
                elif expected_type == "integer" and not isinstance(value, int):
                    type_errors.append(f"{param.name}: expected integer, got {type(value).__name__}")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    type_errors.append(f"{param.name}: expected number, got {type(value).__name__}")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    type_errors.append(f"{param.name}: expected boolean, got {type(value).__name__}")
        
        if type_errors:
            errors['type_errors'] = type_errors
        
        return errors


class ServerInfo(BaseModel):
    """Information about a connected MCP server."""
    name: str
    status: ServerStatus
    connection_type: str
    tools: List[Tool] = Field(default_factory=list)
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int = 0
    
    def is_healthy(self) -> bool:
        """Check if server is in a healthy state."""
        return self.status == ServerStatus.CONNECTED and self.error_count < 3


class ToolInvocation(BaseModel):
    """Model for tool invocation request."""
    tool_name: str
    server_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[float] = None


class ToolResult(BaseModel):
    """Model for tool execution result."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    server_name: Optional[str] = None
    tool_name: Optional[str] = None


class MCPMessage(BaseModel):
    """Base model for MCP protocol messages."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class InitializeRequest(MCPMessage):
    """Initialize request for MCP server."""
    method: str = "initialize"
    params: Dict[str, Any] = Field(default_factory=lambda: {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "mcp-client",
            "version": "0.1.0"
        }
    })


class ToolsListRequest(MCPMessage):
    """Tools list request for MCP server."""
    method: str = "tools/list"
    params: Dict[str, Any] = Field(default_factory=dict)


class ToolCallRequest(MCPMessage):
    """Tool call request for MCP server."""
    method: str = "tools/call"
    
    def __init__(self, tool_name: str, arguments: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.params = {
            "name": tool_name,
            "arguments": arguments
        }
