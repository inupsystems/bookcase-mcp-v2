"""Pytest configuration and fixtures."""

import pytest
import httpx
from typing import Dict, Any

from api_agent.swagger_parser import SwaggerParser
from api_agent.mcp_adapter import MCPAdapter
from api_agent.http_executor import HTTPExecutor
from api_agent.test_generator import TestGenerator
from api_agent.models import ToolDescriptor, Param, ParamLocation


@pytest.fixture
def sample_openapi_spec() -> Dict[str, Any]:
    """Sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API for testing"
        },
        "servers": [
            {"url": "https://api.example.com/v1"}
        ],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "list_users",
                    "summary": "List users",
                    "description": "Get a list of all users",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "minimum": 1, "maximum": 100},
                            "example": 10
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "email": {"type": "string", "format": "email"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "operationId": "create_user",
                    "summary": "Create user",
                    "description": "Create a new user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "email"],
                                    "properties": {
                                        "name": {"type": "string", "minLength": 1},
                                        "email": {"type": "string", "format": "email"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "operationId": "get_user",
                    "summary": "Get user",
                    "description": "Get a specific user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "minimum": 1},
                            "example": 123
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "User not found"
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
    }


@pytest.fixture
def swagger_parser() -> SwaggerParser:
    """Create a SwaggerParser instance."""
    return SwaggerParser()


@pytest.fixture
def parsed_tools(swagger_parser: SwaggerParser, sample_openapi_spec: Dict[str, Any]) -> list:
    """Parse tools from sample OpenAPI spec."""
    swagger_parser.spec = sample_openapi_spec
    return swagger_parser.get_endpoints()


@pytest.fixture
def mcp_adapter(parsed_tools) -> MCPAdapter:
    """Create an MCPAdapter with parsed tools."""
    return MCPAdapter(tools=parsed_tools)


@pytest.fixture
def http_executor() -> HTTPExecutor:
    """Create an HTTPExecutor instance."""
    return HTTPExecutor(base_url="https://api.example.com/v1")


@pytest.fixture
def test_generator(http_executor) -> TestGenerator:
    """Create a TestGenerator instance."""
    return TestGenerator(executor=http_executor)


@pytest.fixture
def sample_tool() -> ToolDescriptor:
    """Create a sample tool descriptor."""
    return ToolDescriptor(
        id="create_user",
        name="Create User",
        description="Create a new user",
        method="POST",
        path="/users",
        parameters=[
            Param(
                name="name",
                location=ParamLocation.QUERY,
                required=True,
                schema={"type": "string", "minLength": 1},
                example="John Doe"
            ),
            Param(
                name="email",
                location=ParamLocation.QUERY,
                required=True,
                schema={"type": "string", "format": "email"},
                example="john@example.com"
            )
        ],
        request_schema={
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "email": {"type": "string", "format": "email"}
            }
        },
        response_schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string"}
            }
        }
    )


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response."""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None, headers=None):
            self.status_code = status_code
            self._json_data = json_data or {}
            self.headers = headers or {}
            self.content = b'{"test": "data"}' if json_data else b''
        
        def json(self):
            return self._json_data
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"HTTP {self.status_code}",
                    request=None,
                    response=self
                )
    
    return MockResponse
