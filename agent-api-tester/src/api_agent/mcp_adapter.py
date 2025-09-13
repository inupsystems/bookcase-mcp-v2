"""MCP (Model Context Protocol) adapter for exposing API tools."""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .http_executor import HTTPExecutor
from .models import MCPToolDiscovery, MCPToolRequest, MCPToolResponse, ToolDescriptor
from .test_monitor import TestResultsMonitor

logger = logging.getLogger(__name__)


class MCPAdapter:
    """Adapter that exposes API tools via MCP-compatible interface."""
    
    def __init__(self, 
                 tools: Optional[List[ToolDescriptor]] = None,
                 base_url: Optional[str] = None,
                 executor: Optional[HTTPExecutor] = None):
        """Initialize MCP adapter.
        
        Args:
            tools: List of available tools
            base_url: Base URL for API calls
            executor: HTTP executor instance
        """
        self.tools: Dict[str, ToolDescriptor] = {}
        if tools:
            for tool in tools:
                self.tools[tool.id] = tool
        
        self.base_url = base_url
        self.executor = executor or HTTPExecutor(base_url=base_url)
        self.test_monitor = TestResultsMonitor.get_global_instance()
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application with MCP endpoints."""
        app = FastAPI(
            title="API-Agent MCP Server",
            description="MCP-compatible server for API tool discovery and invocation",
            version="0.1.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # MCP discovery endpoint
        @app.get("/mcp/tools", response_model=MCPToolDiscovery)
        async def discover_tools():
            """Discover available tools."""
            tools_list = []
            for tool in self.tools.values():
                tool_info = {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "method": tool.method,
                    "path": tool.path,
                    "parameters": self._format_parameters_for_mcp(tool),
                    "request_schema": tool.request_schema,
                    "response_schema": tool.response_schema,
                    "requires_auth": tool.requires_auth(),
                    "tags": tool.tags,
                    "summary": tool.summary
                }
                tools_list.append(tool_info)
            
            return MCPToolDiscovery(
                tools=tools_list,
                total=len(tools_list),
                server_info={
                    "name": "API-Agent MCP Server",
                    "version": "0.1.0",
                    "description": "Transform OpenAPI specs into MCP tools"
                }
            )
        
        # MCP invocation endpoint
        @app.post("/mcp/invoke", response_model=MCPToolResponse)
        async def invoke_tool(request: MCPToolRequest):
            """Invoke a specific tool."""
            start_time = time.time()
            
            try:
                if request.tool_id not in self.tools:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Tool '{request.tool_id}' not found"
                    )
                
                tool = self.tools[request.tool_id]
                
                # Execute the HTTP request
                result = await self.executor.execute_tool(
                    tool=tool,
                    inputs=request.inputs,
                    environment=request.environment
                )
                
                # Log test result
                execution_time = (time.time() - start_time) * 1000  # ms
                self.test_monitor.log_tool_invocation(
                    tool_id=request.tool_id,
                    inputs=request.inputs,
                    outputs=result.data if result.success else {},
                    success=result.success,
                    error=result.error,
                    execution_time=execution_time
                )
                
                return MCPToolResponse(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata=result.metadata,
                    status_code=result.status_code,
                    headers=result.headers
                )
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000  # ms
                logger.error(f"Failed to invoke tool {request.tool_id}: {e}")
                
                # Log failed test result
                self.test_monitor.log_tool_invocation(
                    tool_id=request.tool_id,
                    inputs=request.inputs,
                    outputs={},
                    success=False,
                    error=str(e),
                    execution_time=execution_time
                )
                
                return MCPToolResponse(
                    success=False,
                    error=str(e),
                    metadata={"timestamp": datetime.utcnow().isoformat()}
                )
        
        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "tools_count": len(self.tools),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Tool details endpoint
        @app.get("/mcp/tools/{tool_id}")
        async def get_tool_details(tool_id: str):
            """Get detailed information about a specific tool."""
            if tool_id not in self.tools:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tool '{tool_id}' not found"
                )
            
            tool = self.tools[tool_id]
            return {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "method": tool.method,
                "path": tool.path,
                "parameters": self._format_parameters_for_mcp(tool),
                "request_schema": tool.request_schema,
                "response_schema": tool.response_schema,
                "auth": self._format_auth_for_mcp(tool),
                "examples": [
                    {
                        "name": ex.name,
                        "summary": ex.summary,
                        "description": ex.description,
                        "value": ex.value
                    }
                    for ex in tool.examples
                ],
                "tags": tool.tags,
                "summary": tool.summary,
                "operation_id": tool.operation_id
            }
        
        return app
    
    def _format_parameters_for_mcp(self, tool: ToolDescriptor) -> Dict[str, List[Dict[str, Any]]]:
        """Format tool parameters for MCP response."""
        params_by_location = {
            "path": [],
            "query": [],
            "header": [],
            "cookie": []
        }
        
        for param in tool.parameters:
            param_info = {
                "name": param.name,
                "required": param.required,
                "schema": param.schema,
                "example": param.example,
                "description": param.description
            }
            params_by_location[param.location.value].append(param_info)
        
        return params_by_location
    
    def _format_auth_for_mcp(self, tool: ToolDescriptor) -> Optional[Dict[str, Any]]:
        """Format authentication info for MCP response."""
        if not tool.auth:
            return None
        
        return {
            "type": tool.auth.type.value,
            "scheme": tool.auth.scheme,
            "bearer_format": tool.auth.bearer_format,
            "header_name": tool.auth.header_name,
            "query_name": tool.auth.query_name
        }
    
    def add_tool(self, tool: ToolDescriptor) -> None:
        """Add a new tool to the adapter.
        
        Args:
            tool: Tool descriptor to add
        """
        self.tools[tool.id] = tool
        logger.info(f"Added tool: {tool.id}")
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from the adapter.
        
        Args:
            tool_id: ID of tool to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if tool_id in self.tools:
            del self.tools[tool_id]
            logger.info(f"Removed tool: {tool_id}")
            return True
        return False
    
    def list_tools(self) -> List[str]:
        """List all available tool IDs.
        
        Returns:
            List of tool IDs
        """
        return list(self.tools.keys())
    
    def get_tool(self, tool_id: str) -> Optional[ToolDescriptor]:
        """Get tool by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            ToolDescriptor or None if not found
        """
        return self.tools.get(tool_id)
    
    def update_tools(self, tools: List[ToolDescriptor]) -> None:
        """Update the complete list of tools.
        
        Args:
            tools: New list of tools
        """
        self.tools.clear()
        for tool in tools:
            self.tools[tool.id] = tool
        logger.info(f"Updated tools list with {len(tools)} tools")
    
    def get_tools(self) -> List[ToolDescriptor]:
        """Get the list of available tools.
        
        Returns:
            List of ToolDescriptor objects
        """
        return list(self.tools.values())
    
    def start_test_monitoring(self):
        """Inicia o monitoramento de testes."""
        self.test_monitor.start_monitoring()
    
    def get_test_status(self) -> Dict:
        """Obtém o status atual dos testes."""
        return self.test_monitor.get_current_status()
    
    def get_test_results(self) -> str:
        """Obtém os resultados formatados dos testes."""
        return self.test_monitor.get_formatted_results()
    
    def finish_test_monitoring(self):
        """Finaliza o monitoramento de testes."""
        self.test_monitor.finish_monitoring()
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance.
        
        Returns:
            FastAPI application
        """
        return self.app
    
    async def invoke_tool_direct(self, 
                                tool_id: str, 
                                inputs: Dict[str, Any],
                                environment: Optional[str] = None) -> MCPToolResponse:
        """Directly invoke a tool without HTTP endpoint.
        
        Args:
            tool_id: Tool to invoke
            inputs: Input parameters
            environment: Environment context
            
        Returns:
            Tool execution response
        """
        try:
            if tool_id not in self.tools:
                return MCPToolResponse(
                    success=False,
                    error=f"Tool '{tool_id}' not found"
                )
            
            tool = self.tools[tool_id]
            result = await self.executor.execute_tool(
                tool=tool,
                inputs=inputs,
                environment=environment
            )
            
            return MCPToolResponse(
                success=result.success,
                data=result.data,
                error=result.error,
                metadata=result.metadata,
                status_code=result.status_code,
                headers=result.headers
            )
            
        except Exception as e:
            logger.error(f"Failed to invoke tool {tool_id}: {e}")
            return MCPToolResponse(
                success=False,
                error=str(e),
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
    
    def _ensure_array_items(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all array schemas have items property for MCP compatibility.
        
        Args:
            schema: JSON schema to validate
            
        Returns:
            Validated schema with array items
        """
        import copy
        
        if not isinstance(schema, dict):
            return schema
            
        result = copy.deepcopy(schema)
        
        # Process nested objects recursively
        for key, value in result.items():
            if isinstance(value, dict):
                result[key] = self._ensure_array_items(value)
            elif isinstance(value, list):
                result[key] = [self._ensure_array_items(item) if isinstance(item, dict) else item for item in value]
        
        # Ensure array types have items property
        if result.get("type") == "array" and "items" not in result:
            result["items"] = {"type": "string"}
            
        # Process items if present
        if "items" in result and isinstance(result["items"], dict):
            result["items"] = self._ensure_array_items(result["items"])
            
        # Process additionalProperties if present
        if "additionalProperties" in result and isinstance(result["additionalProperties"], dict):
            result["additionalProperties"] = self._ensure_array_items(result["additionalProperties"])
            
        # Process schema combinations (allOf, anyOf, oneOf)
        for key in ["allOf", "anyOf", "oneOf"]:
            if key in result and isinstance(result[key], list):
                result[key] = [self._ensure_array_items(item) for item in result[key]]
        
        return result

    def export_mcp_schema(self) -> Dict[str, Any]:
        """Export MCP-compatible schema for all tools.
        
        Returns:
            MCP schema dictionary
        """
        tools_schema = []
        for tool in self.tools.values():
            tool_schema = {
                "name": tool.id,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Add parameters to input schema with array validation
            for param in tool.parameters:
                param_schema = param.schema or {"type": "string"}
                # Ensure all array schemas have items property
                validated_schema = self._ensure_array_items(param_schema)
                tool_schema["inputSchema"]["properties"][param.name] = validated_schema
                if param.required:
                    tool_schema["inputSchema"]["required"].append(param.name)
            
            # Add request body schema if present with array validation
            if tool.request_schema:
                validated_request_schema = self._ensure_array_items(tool.request_schema)
                if "properties" in validated_request_schema:
                    tool_schema["inputSchema"]["properties"].update(validated_request_schema["properties"])
                if "required" in validated_request_schema:
                    tool_schema["inputSchema"]["required"].extend(validated_request_schema["required"])
            
            tools_schema.append(tool_schema)
        
        return {
            "tools": tools_schema,
            "version": "0.1.0",
            "protocol": "mcp"
        }


if __name__ == "__main__":
    import uvicorn
    from .tools_storage import ToolsStorage
    
    # Initialize with stored tools
    storage = ToolsStorage()
    tools = storage.load_tools()
    
    adapter = MCPAdapter(tools=tools)
    app = adapter.get_app()
    
    print("🚀 Starting MCP Server...")
    print("📋 Available endpoints:")
    print("   - Discovery: http://localhost:8000/mcp/tools")
    print("   - Invocation: http://localhost:8000/mcp/invoke")
    print("   - Health: http://localhost:8000/health")
    print("   - Docs: http://localhost:8000/docs")
    print(f"🔧 Loaded {len(tools)} tools")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
