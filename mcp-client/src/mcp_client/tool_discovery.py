"""Tool discovery and management for MCP servers."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .connection_manager import ConnectionManager
from .models import Tool, ToolParameter, ToolsListRequest

logger = logging.getLogger(__name__)


class ToolDiscovery:
    """Manages discovery and caching of tools from MCP servers."""
    
    def __init__(self, connection_manager: ConnectionManager, cache_ttl: int = 300):
        self.connection_manager = connection_manager
        self.cache_ttl = cache_ttl
        self.tool_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
    async def discover_all_tools(self, force_refresh: bool = False) -> Dict[str, List[Tool]]:
        """Discover tools from all connected servers."""
        results = {}
        
        connected_servers = self.connection_manager.get_connected_servers()
        tasks = []
        
        for server_name in connected_servers:
            task = asyncio.create_task(
                self.discover_server_tools(server_name, force_refresh)
            )
            tasks.append((server_name, task))
        
        for server_name, task in tasks:
            try:
                tools = await task
                results[server_name] = tools
            except Exception as e:
                logger.error(f"Failed to discover tools for {server_name}: {e}")
                results[server_name] = []
        
        return results
    
    async def discover_server_tools(self, server_name: str, force_refresh: bool = False) -> List[Tool]:
        """Discover tools from a specific server."""
        # Check cache first
        if not force_refresh and self._is_cache_valid(server_name):
            cached_tools = self.tool_cache.get(server_name, {}).get('tools', [])
            return [Tool(**tool_data) for tool_data in cached_tools]
        
        connection = self.connection_manager.get_connection(server_name)
        if not connection or not connection.is_connected():
            logger.warning(f"Server {server_name} is not connected")
            return []
        
        try:
            # Send tools/list request
            tools_request = ToolsListRequest(id=int(time.time()))
            response = await connection.send_message(tools_request)
            
            if not response or 'result' not in response:
                logger.error(f"Invalid response from {server_name}: {response}")
                return []
            
            # Parse tools from response
            tools_data = response['result'].get('tools', [])
            tools = []
            
            for tool_data in tools_data:
                tool = self._parse_tool_data(tool_data, server_name)
                if tool:
                    tools.append(tool)
            
            # Update cache
            self._update_cache(server_name, tools)
            
            logger.info(f"Discovered {len(tools)} tools from {server_name}")
            return tools
            
        except Exception as e:
            logger.error(f"Error discovering tools from {server_name}: {e}")
            return []
    
    def _parse_tool_data(self, tool_data: Dict[str, Any], server_name: str) -> Optional[Tool]:
        """Parse tool data from MCP response."""
        try:
            name = tool_data.get('name')
            if not name:
                logger.warning(f"Tool missing name: {tool_data}")
                return None
            
            description = tool_data.get('description', '')
            input_schema = tool_data.get('inputSchema', {})
            
            # Parse parameters from input schema
            parameters = []
            if 'properties' in input_schema:
                required_fields = input_schema.get('required', [])
                
                for param_name, param_schema in input_schema['properties'].items():
                    parameter = ToolParameter(
                        name=param_name,
                        type=param_schema.get('type', 'string'),
                        description=param_schema.get('description'),
                        required=param_name in required_fields,
                        param_schema=param_schema
                    )
                    parameters.append(parameter)
            
            return Tool(
                name=name,
                description=description,
                parameters=parameters,
                input_schema=input_schema,
                server_name=server_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing tool data: {e}")
            return None
    
    def _is_cache_valid(self, server_name: str) -> bool:
        """Check if cached tools are still valid."""
        if server_name not in self.cache_timestamps:
            return False
        
        cache_age = time.time() - self.cache_timestamps[server_name]
        return cache_age < self.cache_ttl
    
    def _update_cache(self, server_name: str, tools: List[Tool]) -> None:
        """Update tool cache for a server."""
        self.tool_cache[server_name] = {
            'tools': [tool.dict() for tool in tools]
        }
        self.cache_timestamps[server_name] = time.time()
    
    def get_cached_tools(self, server_name: str) -> List[Tool]:
        """Get cached tools for a server."""
        if not self._is_cache_valid(server_name):
            return []
        
        cached_tools = self.tool_cache.get(server_name, {}).get('tools', [])
        return [Tool(**tool_data) for tool_data in cached_tools]
    
    def get_all_cached_tools(self) -> Dict[str, List[Tool]]:
        """Get all cached tools from all servers."""
        results = {}
        
        for server_name in self.tool_cache.keys():
            if self._is_cache_valid(server_name):
                results[server_name] = self.get_cached_tools(server_name)
        
        return results
    
    def find_tool(self, tool_name: str, server_name: Optional[str] = None) -> Optional[Tool]:
        """Find a specific tool by name."""
        if server_name:
            # Search in specific server
            tools = self.get_cached_tools(server_name)
            for tool in tools:
                if tool.name == tool_name:
                    return tool
        else:
            # Search in all servers
            all_tools = self.get_all_cached_tools()
            for server_tools in all_tools.values():
                for tool in server_tools:
                    if tool.name == tool_name:
                        return tool
        
        return None
    
    def search_tools(self, query: str) -> List[Tool]:
        """Search for tools by name or description."""
        results = []
        query_lower = query.lower()
        
        all_tools = self.get_all_cached_tools()
        for server_tools in all_tools.values():
            for tool in server_tools:
                # Search in name and description
                if (query_lower in tool.name.lower() or 
                    (tool.description and query_lower in tool.description.lower())):
                    results.append(tool)
        
        return results
    
    def get_tool_count_by_server(self) -> Dict[str, int]:
        """Get count of tools per server."""
        counts = {}
        
        all_tools = self.get_all_cached_tools()
        for server_name, tools in all_tools.items():
            counts[server_name] = len(tools)
        
        return counts
    
    def clear_cache(self, server_name: Optional[str] = None) -> None:
        """Clear tool cache."""
        if server_name:
            if server_name in self.tool_cache:
                del self.tool_cache[server_name]
            if server_name in self.cache_timestamps:
                del self.cache_timestamps[server_name]
        else:
            self.tool_cache.clear()
            self.cache_timestamps.clear()
        
        logger.info(f"Cleared tool cache for {server_name or 'all servers'}")
    
    async def refresh_tools(self, server_name: Optional[str] = None) -> Dict[str, List[Tool]]:
        """Refresh tools from servers."""
        if server_name:
            tools = await self.discover_server_tools(server_name, force_refresh=True)
            return {server_name: tools}
        else:
            return await self.discover_all_tools(force_refresh=True)
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get statistics about discovered tools."""
        all_tools = self.get_all_cached_tools()
        
        total_tools = sum(len(tools) for tools in all_tools.values())
        servers_with_tools = len([s for s, tools in all_tools.items() if tools])
        
        # Tool type distribution
        tool_types = {}
        for tools in all_tools.values():
            for tool in tools:
                # Count parameters
                param_count = len(tool.parameters)
                key = f"{param_count}_params"
                tool_types[key] = tool_types.get(key, 0) + 1
        
        return {
            'total_tools': total_tools,
            'total_servers': len(self.tool_cache),
            'servers_with_tools': servers_with_tools,
            'tool_distribution': tool_types,
            'cache_info': {
                server: {
                    'tool_count': len(tools),
                    'cache_age': time.time() - self.cache_timestamps.get(server, 0)
                }
                for server, tools in all_tools.items()
            }
        }
