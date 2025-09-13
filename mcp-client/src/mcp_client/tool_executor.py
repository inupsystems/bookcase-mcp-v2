"""Tool execution engine for MCP servers."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .connection_manager import ConnectionManager
from .models import Tool, ToolCallRequest, ToolInvocation, ToolResult
from .tool_discovery import ToolDiscovery

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools on MCP servers."""
    
    def __init__(self, connection_manager: ConnectionManager, tool_discovery: ToolDiscovery):
        self.connection_manager = connection_manager
        self.tool_discovery = tool_discovery
        self.execution_history: List[ToolResult] = []
        
    async def execute_tool(self, invocation: ToolInvocation) -> ToolResult:
        """Execute a tool on the specified server."""
        start_time = time.time()
        
        try:
            # Find the tool
            tool = self.tool_discovery.find_tool(invocation.tool_name, invocation.server_name)
            if not tool:
                return ToolResult(
                    success=False,
                    error=f"Tool '{invocation.tool_name}' not found on server '{invocation.server_name}'",
                    execution_time=time.time() - start_time,
                    server_name=invocation.server_name,
                    tool_name=invocation.tool_name
                )
            
            # Validate parameters
            validation_errors = tool.validate_parameters(invocation.parameters)
            if validation_errors:
                error_msg = self._format_validation_errors(validation_errors)
                return ToolResult(
                    success=False,
                    error=f"Parameter validation failed: {error_msg}",
                    execution_time=time.time() - start_time,
                    server_name=invocation.server_name,
                    tool_name=invocation.tool_name
                )
            
            # Get connection
            connection = self.connection_manager.get_connection(invocation.server_name)
            if not connection or not connection.is_connected():
                return ToolResult(
                    success=False,
                    error=f"Server '{invocation.server_name}' is not connected",
                    execution_time=time.time() - start_time,
                    server_name=invocation.server_name,
                    tool_name=invocation.tool_name
                )
            
            # Execute the tool
            call_request = ToolCallRequest(
                tool_name=invocation.tool_name,
                arguments=invocation.parameters,
                id=int(time.time() * 1000)
            )
            
            # Apply timeout if specified
            timeout = invocation.timeout or connection.config.get_timeout_seconds()
            
            response = await asyncio.wait_for(
                connection.send_message(call_request),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            if not response:
                result = ToolResult(
                    success=False,
                    error="No response from server",
                    execution_time=execution_time,
                    server_name=invocation.server_name,
                    tool_name=invocation.tool_name
                )
            elif 'error' in response:
                result = ToolResult(
                    success=False,
                    error=f"Server error: {response['error'].get('message', 'Unknown error')}",
                    execution_time=execution_time,
                    server_name=invocation.server_name,
                    tool_name=invocation.tool_name
                )
            else:
                # Extract result from response
                tool_result = response.get('result', {})
                
                # Handle different response formats
                if 'content' in tool_result:
                    # MCP stdio format
                    content = tool_result['content']
                    if isinstance(content, list) and content:
                        result_data = content[0].get('text', content[0])
                    else:
                        result_data = content
                else:
                    # Direct result or HTTP format
                    result_data = tool_result
                
                result = ToolResult(
                    success=True,
                    result=result_data,
                    execution_time=execution_time,
                    server_name=invocation.server_name,
                    tool_name=invocation.tool_name
                )
            
            # Store in history
            self.execution_history.append(result)
            
            # Log execution
            if result.success:
                logger.info(f"Successfully executed {invocation.tool_name} on {invocation.server_name} in {execution_time:.2f}s")
            else:
                logger.error(f"Failed to execute {invocation.tool_name} on {invocation.server_name}: {result.error}")
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            result = ToolResult(
                success=False,
                error=f"Tool execution timed out after {execution_time:.2f}s",
                execution_time=execution_time,
                server_name=invocation.server_name,
                tool_name=invocation.tool_name
            )
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = ToolResult(
                success=False,
                error=f"Execution failed: {str(e)}",
                execution_time=execution_time,
                server_name=invocation.server_name,
                tool_name=invocation.tool_name
            )
            self.execution_history.append(result)
            logger.error(f"Exception during tool execution: {e}")
            return result
    
    async def execute_tool_by_name(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        server_name: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> ToolResult:
        """Execute a tool by name, optionally specifying server."""
        # If no server specified, find the tool in available servers
        if not server_name:
            tool = self.tool_discovery.find_tool(tool_name)
            if tool:
                server_name = tool.server_name
            else:
                return ToolResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found in any connected server",
                    tool_name=tool_name
                )
        
        invocation = ToolInvocation(
            tool_name=tool_name,
            server_name=server_name,
            parameters=parameters,
            timeout=timeout
        )
        
        return await self.execute_tool(invocation)
    
    async def batch_execute(self, invocations: List[ToolInvocation]) -> List[ToolResult]:
        """Execute multiple tools in parallel."""
        tasks = []
        
        for invocation in invocations:
            task = asyncio.create_task(self.execute_tool(invocation))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to ToolResult
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                invocation = invocations[i]
                final_results.append(ToolResult(
                    success=False,
                    error=f"Execution exception: {str(result)}",
                    server_name=invocation.server_name,
                    tool_name=invocation.tool_name
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def _format_validation_errors(self, errors: Dict[str, Any]) -> str:
        """Format validation errors into a readable string."""
        messages = []
        
        if 'missing' in errors:
            missing = errors['missing']
            messages.append(f"Missing required parameters: {', '.join(missing)}")
        
        if 'type_errors' in errors:
            type_errors = errors['type_errors']
            messages.append(f"Type errors: {'; '.join(type_errors)}")
        
        return "; ".join(messages)
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[ToolResult]:
        """Get execution history."""
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'by_server': {},
                'by_tool': {}
            }
        
        total = len(self.execution_history)
        successful = sum(1 for result in self.execution_history if result.success)
        
        # Calculate average execution time
        execution_times = [r.execution_time for r in self.execution_history if r.execution_time]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        # Group by server
        by_server = {}
        for result in self.execution_history:
            if result.server_name:
                if result.server_name not in by_server:
                    by_server[result.server_name] = {'total': 0, 'successful': 0}
                by_server[result.server_name]['total'] += 1
                if result.success:
                    by_server[result.server_name]['successful'] += 1
        
        # Group by tool
        by_tool = {}
        for result in self.execution_history:
            if result.tool_name:
                if result.tool_name not in by_tool:
                    by_tool[result.tool_name] = {'total': 0, 'successful': 0}
                by_tool[result.tool_name]['total'] += 1
                if result.success:
                    by_tool[result.tool_name]['successful'] += 1
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'failed_executions': total - successful,
            'success_rate': successful / total * 100,
            'average_execution_time': avg_time,
            'by_server': by_server,
            'by_tool': by_tool
        }
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()
        logger.info("Cleared execution history")
    
    async def test_tool(self, tool_name: str, server_name: Optional[str] = None) -> ToolResult:
        """Test a tool with minimal/default parameters."""
        tool = self.tool_discovery.find_tool(tool_name, server_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                tool_name=tool_name
            )
        
        # Build minimal parameters
        test_parameters = {}
        for param in tool.parameters:
            if param.required:
                # Use default value if available, otherwise use type-appropriate default
                if param.default is not None:
                    test_parameters[param.name] = param.default
                elif param.type == "string":
                    test_parameters[param.name] = "test"
                elif param.type == "integer":
                    test_parameters[param.name] = 1
                elif param.type == "number":
                    test_parameters[param.name] = 1.0
                elif param.type == "boolean":
                    test_parameters[param.name] = True
                else:
                    test_parameters[param.name] = None
        
        return await self.execute_tool_by_name(
            tool_name=tool_name,
            parameters=test_parameters,
            server_name=tool.server_name
        )
