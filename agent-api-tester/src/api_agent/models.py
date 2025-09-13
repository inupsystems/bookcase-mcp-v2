"""Core data models for API-Agent."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AuthType(str, Enum):
    """Supported authentication types."""
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class ParamLocation(str, Enum):
    """Parameter locations in HTTP request."""
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


@dataclass
class AuthSpec:
    """Authentication specification for an API endpoint."""
    type: AuthType
    scheme: Optional[str] = None
    bearer_format: Optional[str] = None
    header_name: Optional[str] = None
    query_name: Optional[str] = None
    flows: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_openapi(cls, security_scheme: Dict[str, Any]) -> "AuthSpec":
        """Create AuthSpec from OpenAPI security scheme."""
        scheme_type = security_scheme.get("type", "").lower()
        
        if scheme_type == "http":
            http_scheme = security_scheme.get("scheme", "").lower()
            return cls(
                type=AuthType.BEARER if http_scheme == "bearer" else AuthType.BASIC,
                scheme=http_scheme,
                bearer_format=security_scheme.get("bearerFormat")
            )
        elif scheme_type == "apikey":
            location = security_scheme.get("in", "header")
            return cls(
                type=AuthType.API_KEY,
                header_name=security_scheme.get("name") if location == "header" else None,
                query_name=security_scheme.get("name") if location == "query" else None
            )
        elif scheme_type == "oauth2":
            return cls(
                type=AuthType.OAUTH2,
                flows=security_scheme.get("flows", {})
            )
        else:
            return cls(type=AuthType.NONE)


@dataclass
class Param:
    """Parameter specification for API endpoint."""
    name: str
    location: ParamLocation
    required: bool = False
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None
    description: Optional[str] = None
    
    @classmethod
    def from_openapi(cls, param_data: Dict[str, Any]) -> "Param":
        """Create Param from OpenAPI parameter specification."""
        return cls(
            name=param_data["name"],
            location=ParamLocation(param_data["in"]),
            required=param_data.get("required", False),
            schema=param_data.get("schema"),
            example=param_data.get("example"),
            description=param_data.get("description")
        )


@dataclass
class Example:
    """Example request/response for an API endpoint."""
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Optional[Any] = None
    external_value: Optional[str] = None


@dataclass
class ToolDescriptor:
    """Complete description of an API endpoint as an MCP tool."""
    id: str
    name: str
    description: str
    method: str
    path: str
    parameters: List[Param] = field(default_factory=list)
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth: Optional[AuthSpec] = None
    examples: List[Example] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    operation_id: Optional[str] = None
    
    def get_path_params(self) -> List[Param]:
        """Get path parameters."""
        return [p for p in self.parameters if p.location == ParamLocation.PATH]
    
    def get_query_params(self) -> List[Param]:
        """Get query parameters."""
        return [p for p in self.parameters if p.location == ParamLocation.QUERY]
    
    def get_header_params(self) -> List[Param]:
        """Get header parameters."""
        return [p for p in self.parameters if p.location == ParamLocation.HEADER]
    
    def requires_auth(self) -> bool:
        """Check if endpoint requires authentication."""
        return self.auth is not None and self.auth.type != AuthType.NONE


class MCPToolRequest(BaseModel):
    """Request model for MCP tool invocation."""
    tool_id: str = Field(..., description="Unique identifier of the tool to invoke")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the tool")
    environment: Optional[str] = Field(None, description="Environment context (dev/staging/prod)")


class MCPToolResponse(BaseModel):
    """Response model for MCP tool invocation."""
    success: bool = Field(..., description="Whether the tool execution was successful")
    data: Optional[Any] = Field(None, description="Response data from the API call")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    headers: Optional[Dict[str, str]] = Field(None, description="Response headers")


class MCPToolDiscovery(BaseModel):
    """Model for tool discovery response."""
    tools: List[Dict[str, Any]] = Field(..., description="List of available tools")
    total: int = Field(..., description="Total number of tools")
    server_info: Dict[str, str] = Field(default_factory=dict, description="Server information")


class TestCase(BaseModel):
    """Test case specification."""
    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Test case description")
    tool_id: str = Field(..., description="Tool to test")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Test inputs")
    expected_status: int = Field(200, description="Expected HTTP status code")
    expected_schema: Optional[Dict[str, Any]] = Field(None, description="Expected response schema")
    test_type: str = Field("positive", description="Type of test (positive/negative/edge)")
    tags: List[str] = Field(default_factory=list, description="Test tags")


class TestResult(BaseModel):
    """Test execution result."""
    test_case: TestCase = Field(..., description="Executed test case")
    success: bool = Field(..., description="Whether test passed")
    actual_status: Optional[int] = Field(None, description="Actual HTTP status code")
    actual_response: Optional[Any] = Field(None, description="Actual response data")
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    execution_time: float = Field(..., description="Test execution time in seconds")
    timestamp: str = Field(..., description="Test execution timestamp")


class TestSuite(BaseModel):
    """Test suite results."""
    tool_id: str = Field(..., description="Tool that was tested")
    total_tests: int = Field(..., description="Total number of tests")
    passed: int = Field(..., description="Number of passed tests")
    failed: int = Field(..., description="Number of failed tests")
    results: List[TestResult] = Field(..., description="Individual test results")
    execution_time: float = Field(..., description="Total execution time")
    timestamp: str = Field(..., description="Suite execution timestamp")
