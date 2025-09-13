"""MCP stdio server implementation."""

import json
import sys
import asyncio
import re
import os
import time
from typing import Any, Dict, List, Optional

from .models import ToolDescriptor
from .swagger_parser import SwaggerParser
from .http_executor import HTTPExecutor
from .tools_storage import ToolsStorage


def normalize_tool_name(name: str) -> str:
    """Normalize tool name to MCP format [a-z0-9_-]."""
    # Convert to lowercase
    name = name.lower()
    # Replace spaces and special chars with underscores
    name = re.sub(r'[^a-z0-9_-]', '_', name)
    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name


class MCPStdioServer:
    """MCP stdio server implementation."""
    
    def __init__(self):
        """Initialize the MCP stdio server."""
        self.parser = SwaggerParser()
        
        # Configure base_url from environment variable or default
        base_url = os.getenv("API_BASE_URL", "http://localhost:8080")
        self.executor = HTTPExecutor(base_url=base_url)
        
        # Storage file is in parent directory 
        self.storage = ToolsStorage("../.tools_state.json")
        self.tools: List[ToolDescriptor] = []
        self.initialized = False
        
        # Initialize monitor for real-time tracking (disabled for stability)
        self.monitor = None
        # Note: Monitor will be initialized only when actually needed
        # to avoid any potential deadlocks during server startup
    
    def _ensure_monitor(self):
        """Initialize monitor if not already done."""
        if self.monitor is None:
            try:
                from .test_monitor import TestResultsMonitor
                self.monitor = TestResultsMonitor.get_global_instance()
                self.monitor.start_monitoring()
                print("Monitor initialized on-demand", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Failed to initialize monitor on-demand: {e}", file=sys.stderr)
                self.monitor = False  # Mark as failed to avoid retrying
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP message."""
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")
        
        if method == "initialize":
            return await self.handle_initialize(request_id, params)
        elif method == "tools/list":
            return await self.handle_tools_list(request_id)
        elif method == "tools/call":
            return await self.handle_tools_call(request_id, params)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def handle_initialize(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        self.initialized = True
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "api-agent-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_tools_list(self, request_id: int) -> Dict[str, Any]:
        """Handle tools/list request."""
        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }
        
        tools = []
        for tool in self.tools:
            # Use operation_id if available, otherwise normalize the name
            tool_name = tool.operation_id if tool.operation_id else normalize_tool_name(tool.name)
            
            # Build input schema from parameters and request body
            properties = {}
            required = []
            
            # Add path and query parameters
            for param in tool.parameters:
                # Use full parameter schema or create default
                if param.schema and isinstance(param.schema, dict):
                    param_schema = param.schema.copy()
                    # Ensure arrays have items property
                    if param_schema.get("type") == "array" and "items" not in param_schema:
                        param_schema["items"] = {"type": "string"}
                else:
                    param_schema = {"type": "string"}
                
                # Add description if not present
                if "description" not in param_schema:
                    param_schema["description"] = param.description or f"{param.name} parameter ({param.location.value})"
                
                properties[param.name] = param_schema
                
                if param.required:
                    required.append(param.name)
            
            # Add request body properties if present
            if tool.request_schema:
                # For POST/PUT methods, treat the entire request body as a single property
                if tool.method in ["POST", "PUT", "PATCH"]:
                    if tool.request_schema.get("$ref"):
                        # For schema references, create a generic object input
                        schema_name = tool.request_schema.get("$ref", "").split("/")[-1]
                        properties["body"] = {
                            "type": "object",
                            "description": f"Request body data ({schema_name})",
                            "additionalProperties": True
                        }
                        required.append("body")
                    elif tool.request_schema.get("type") == "object":
                        # Direct object schema
                        schema_props = tool.request_schema.get("properties", {})
                        for prop_name, prop_schema in schema_props.items():
                            # Use full property schema and ensure arrays have items
                            if isinstance(prop_schema, dict):
                                full_prop_schema = prop_schema.copy()
                                # Ensure arrays have items property
                                if full_prop_schema.get("type") == "array" and "items" not in full_prop_schema:
                                    full_prop_schema["items"] = {"type": "string"}
                                # Add description if missing
                                if "description" not in full_prop_schema:
                                    full_prop_schema["description"] = f"{prop_name} property"
                                properties[prop_name] = full_prop_schema
                            else:
                                properties[prop_name] = {
                                    "type": "string",
                                    "description": f"{prop_name} property"
                                }
                        
                        # Add required fields from request schema
                        schema_required = tool.request_schema.get("required", [])
                        required.extend(schema_required)
            
            # Create comprehensive description
            description = tool.description
            if tool.method and tool.path:
                description += f"\n\nEndpoint: {tool.method} {tool.path}"
            if tool.request_schema:
                description += f"\n\nRequires request body data."
            if tool.parameters:
                param_desc = ", ".join([f"{p.name} ({p.location.value})" for p in tool.parameters])
                description += f"\n\nParameters: {param_desc}"
            
            tools.append({
                "name": tool_name,
                "description": description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            })
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
    
    async def handle_tools_call(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Find the tool by operation_id or normalized name
        tool = None
        for t in self.tools:
            tool_identifier = t.operation_id if t.operation_id else normalize_tool_name(t.name)
            if tool_identifier == tool_name:
                tool = t
                break
        
        if not tool:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        try:
            # Get start time for monitoring
            start_time = time.time()
            
            # Execute the tool
            # Separate path params, query params, and request body
            path_params = {}
            query_params = {}
            request_body = None
            
            # Process arguments based on tool parameters
            for param in tool.parameters:
                if param.name in arguments:
                    if param.location.value == "path":
                        path_params[param.name] = arguments[param.name]
                    elif param.location.value == "query":
                        query_params[param.name] = arguments[param.name]
            
            # Handle request body for POST/PUT/PATCH methods
            if tool.method in ["POST", "PUT", "PATCH"] and tool.request_schema:
                if "body" in arguments:
                    # Body was sent as a single object
                    request_body = arguments["body"]
                else:
                    # Collect all non-parameter arguments as body
                    body_data = {}
                    param_names = {p.name for p in tool.parameters}
                    for key, value in arguments.items():
                        if key not in param_names:
                            body_data[key] = value
                    if body_data:
                        request_body = body_data
            
            # Prepare the complete arguments for execution
            execution_args = {
                **path_params,
                **query_params
            }
            
            # Add request body if present
            if request_body:
                execution_args["__request_body__"] = request_body
            
            print(f"Executing {tool.name} with args: {execution_args}", file=sys.stderr)
            
            result = await self.executor.execute_tool(tool, execution_args)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log successful execution to monitor (if available)
            if self.monitor is None:
                self._ensure_monitor()
            
            if self.monitor and self.monitor is not False:
                try:
                    self.monitor.log_tool_invocation(
                        tool_name=tool_name,
                        arguments=arguments,
                        success=result.success,
                        response_time=execution_time,
                        result=result.data if result.success else None,
                        error=result.error if not result.success else None,
                        http_status=getattr(result, 'status_code', None),
                        endpoint=f"{tool.method} {tool.path}"
                    )
                except Exception as e:
                    print(f"Warning: Failed to log to monitor: {e}", file=sys.stderr)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.data, indent=2) if result.success else f"Error: {result.error}"
                        }
                    ]
                }
            }
        except Exception as e:
            # Calculate execution time for error case
            execution_time = time.time() - start_time if 'start_time' in locals() else 0
            
            # Log failed execution to monitor (if available)
            if self.monitor is None:
                self._ensure_monitor()
                
            if self.monitor and self.monitor is not False:
                try:
                    self.monitor.log_tool_invocation(
                        tool_name=tool_name,
                        arguments=arguments,
                        success=False,
                        response_time=execution_time,
                        error=str(e),
                        endpoint=f"{tool.method} {tool.path}" if tool else "unknown"
                    )
                except Exception as monitor_error:
                    print(f"Warning: Failed to log error to monitor: {monitor_error}", file=sys.stderr)
            
            print(f"Tool execution error: {e}", file=sys.stderr)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }
    
    def load_spec_from_file(self, file_path: str):
        """Load OpenAPI spec from file."""
        self.parser.load_from_file(file_path)
        self.tools = self.parser.get_endpoints()
    
    def load_spec_from_url(self, url: str):
        """Load OpenAPI spec from URL."""
        self.parser.load_from_url(url)
        self.tools = self.parser.get_endpoints()
    
    async def run(self):
        """Run the MCP stdio server."""
        while True:
            try:
                # Read message from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Parse JSON message
                message = json.loads(line.strip())
                
                # Handle message
                response = await self.handle_message(message)
                
                # Send response to stdout
                if response:
                    print(json.dumps(response), flush=True)
                    
            except json.JSONDecodeError:
                # Invalid JSON, ignore
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


async def main():
    """Main entry point for MCP stdio server."""
    server = MCPStdioServer()
    
    # Try to load tools from storage first (contains real tools)
    stored_tools = server.storage.load_tools()
    if stored_tools:
        print(f"Loaded {len(stored_tools)} tools from storage", file=sys.stderr)
        server.tools = stored_tools
    else:
        # Fallback to loading from spec file
        try:
            import os
            spec_file = os.environ.get("API_SPEC_FILE")
            spec_url = os.environ.get("API_SPEC_URL")
            
            if spec_file:
                print(f"Loading spec from file: {spec_file}", file=sys.stderr)
                server.load_spec_from_file(spec_file)
                print(f"Loaded {len(server.tools)} tools from spec", file=sys.stderr)
            elif spec_url:
                print(f"Loading spec from URL: {spec_url}", file=sys.stderr)
                server.load_spec_from_url(spec_url)
                print(f"Loaded {len(server.tools)} tools from spec", file=sys.stderr)
            else:
                # Load default example if available
                from pathlib import Path
                default_spec = Path("examples/jsonplaceholder-api.json")
                if default_spec.exists():
                    print(f"Loading default spec: {default_spec}", file=sys.stderr)
                    server.load_spec_from_file(str(default_spec))
                    print(f"Loaded {len(server.tools)} tools from default spec", file=sys.stderr)
                else:
                    print("No spec file found, starting with empty tools", file=sys.stderr)
        except Exception as e:
            print(f"Error loading spec: {e}", file=sys.stderr)
    
    # Debug: print tool names
    for tool in server.tools:
        tool_name = tool.operation_id if tool.operation_id else normalize_tool_name(tool.name)
        print(f"Tool: {tool_name} - {tool.description}", file=sys.stderr)
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
