"""API-Agent: Transform OpenAPI specs into MCP tools for LLM agents."""

__version__ = "0.1.0"
__author__ = "API-Agent Team"
__email__ = "team@api-agent.dev"

# Lazy imports to avoid circular dependencies and module loading issues
__all__ = [
    "ToolDescriptor",
    "Param",
    "AuthSpec",
    "Example",
    "SwaggerParser",
    "MCPAdapter",
    "HTTPExecutor",
    "TestGenerator",
]
