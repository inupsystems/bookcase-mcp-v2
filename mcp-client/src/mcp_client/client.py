"""Main MCP Client class that orchestrates all components."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import MCPConfig
from .connection_manager import ConnectionManager
from .models import ServerInfo, Tool, ToolInvocation, ToolResult
from .tool_discovery import ToolDiscovery
from .tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class MCPClient:
    """Main MCP Client that manages connections, tools, and execution."""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        self.config = config
        self.connection_manager = ConnectionManager()
        self.tool_discovery: Optional[ToolDiscovery] = None
        self.tool_executor: Optional[ToolExecutor] = None
        self._initialized = False
        
    @classmethod
    def from_config_file(cls, config_path: Union[str, Path]) -> "MCPClient":
        """Create client from configuration file."""
        config = MCPConfig.from_file(config_path)
        return cls(config)
    
    async def initialize(self, config: Optional[MCPConfig] = None) -> bool:
        """Initialize the client with configuration."""
        if config:
            self.config = config
        
        if not self.config:
            raise ValueError("No configuration provided")
        
        # Validate configuration
        issues = self.config.validate_server_configs()
        if issues:
            logger.error(f"Configuration validation failed: {issues}")
            return False
        
        # Add servers to connection manager
        for name, server_config in self.config.servers.items():
            self.connection_manager.add_server(name, server_config)
        
        # Initialize components
        self.tool_discovery = ToolDiscovery(
            self.connection_manager,
            cache_ttl=self.config.tool_cache_ttl
        )
        self.tool_executor = ToolExecutor(
            self.connection_manager,
            self.tool_discovery
        )
        
        self._initialized = True
        logger.info(f"MCP Client initialized with {len(self.config.servers)} servers")
        return True
    
    async def connect(self) -> Dict[str, bool]:
        """Connect to all configured servers."""
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        logger.info("Connecting to MCP servers...")
        results = await self.connection_manager.connect_all()
        
        connected_count = sum(1 for success in results.values() if success)
        logger.info(f"Connected to {connected_count}/{len(results)} servers")
        
        # Discover tools from connected servers
        if connected_count > 0:
            await self.discover_tools()
        
        return results
    
    async def disconnect(self) -> None:
        """Disconnect from all servers."""
        if self.connection_manager:
            await self.connection_manager.disconnect_all()
        logger.info("Disconnected from all servers")
    
    async def discover_tools(self, force_refresh: bool = False) -> Dict[str, List[Tool]]:
        """Discover tools from all connected servers."""
        if not self.tool_discovery:
            raise RuntimeError("Client not initialized")
        
        logger.info("Discovering tools from connected servers...")
        tools = await self.tool_discovery.discover_all_tools(force_refresh)
        
        total_tools = sum(len(server_tools) for server_tools in tools.values())
        logger.info(f"Discovered {total_tools} tools from {len(tools)} servers")
        
        return tools
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        server_name: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> ToolResult:
        """Execute a tool."""
        if not self.tool_executor:
            raise RuntimeError("Client not initialized")
        
        return await self.tool_executor.execute_tool_by_name(
            tool_name=tool_name,
            parameters=parameters,
            server_name=server_name,
            timeout=timeout
        )
    
    async def batch_execute(self, invocations: List[ToolInvocation]) -> List[ToolResult]:
        """Execute multiple tools in parallel."""
        if not self.tool_executor:
            raise RuntimeError("Client not initialized")
        
        return await self.tool_executor.batch_execute(invocations)
    
    def get_servers(self) -> List[ServerInfo]:
        """Get information about all configured servers."""
        if not self.connection_manager:
            return []
        
        return self.connection_manager.get_all_server_info()
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected server names."""
        if not self.connection_manager:
            return []
        
        return self.connection_manager.get_connected_servers()
    
    def get_tools(self, server_name: Optional[str] = None) -> List[Tool]:
        """Get tools from all servers or a specific server."""
        if not self.tool_discovery:
            return []
        
        if server_name:
            return self.tool_discovery.get_cached_tools(server_name)
        else:
            all_tools = self.tool_discovery.get_all_cached_tools()
            tools = []
            for server_tools in all_tools.values():
                tools.extend(server_tools)
            return tools
    
    def find_tool(self, tool_name: str, server_name: Optional[str] = None) -> Optional[Tool]:
        """Find a specific tool."""
        if not self.tool_discovery:
            return None
        
        return self.tool_discovery.find_tool(tool_name, server_name)
    
    def search_tools(self, query: str) -> List[Tool]:
        """Search for tools by name or description."""
        if not self.tool_discovery:
            return []
        
        return self.tool_discovery.search_tools(query)
    
    async def test_tool(self, tool_name: str, server_name: Optional[str] = None) -> ToolResult:
        """Test a tool with default parameters."""
        if not self.tool_executor:
            raise RuntimeError("Client not initialized")
        
        return await self.tool_executor.test_tool(tool_name, server_name)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        if not self._initialized:
            return {
                'initialized': False,
                'servers': {},
                'tools': {},
                'error': 'Client not initialized'
            }
        
        # Check server connections
        server_health = await self.connection_manager.health_check()
        
        # Get tool statistics
        tool_stats = {}
        if self.tool_discovery:
            tool_stats = self.tool_discovery.get_tool_statistics()
        
        # Get execution statistics
        execution_stats = {}
        if self.tool_executor:
            execution_stats = self.tool_executor.get_execution_statistics()
        
        return {
            'initialized': True,
            'servers': server_health,
            'tools': tool_stats,
            'execution': execution_stats,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[ToolResult]:
        """Get tool execution history."""
        if not self.tool_executor:
            return []
        
        return self.tool_executor.get_execution_history(limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive client statistics."""
        stats = {
            'initialized': self._initialized,
            'config': {
                'servers': len(self.config.servers) if self.config else 0,
                'default_timeout': self.config.default_timeout if self.config else 0,
                'retry_attempts': self.config.retry_attempts if self.config else 0,
            },
            'servers': {},
            'tools': {},
            'execution': {}
        }
        
        if self._initialized:
            # Server statistics
            servers = self.get_servers()
            connected = sum(1 for s in servers if s.status.value == 'connected')
            stats['servers'] = {
                'total': len(servers),
                'connected': connected,
                'disconnected': len(servers) - connected,
                'details': [
                    {
                        'name': s.name,
                        'status': s.status.value,
                        'connection_type': s.connection_type,
                        'tool_count': len(s.tools),
                        'error_count': s.error_count
                    }
                    for s in servers
                ]
            }
            
            # Tool statistics
            if self.tool_discovery:
                stats['tools'] = self.tool_discovery.get_tool_statistics()
            
            # Execution statistics
            if self.tool_executor:
                stats['execution'] = self.tool_executor.get_execution_statistics()
        
        return stats
    
    async def refresh_tools(self, server_name: Optional[str] = None) -> Dict[str, List[Tool]]:
        """Refresh tool discovery."""
        if not self.tool_discovery:
            raise RuntimeError("Client not initialized")
        
        return await self.tool_discovery.refresh_tools(server_name)
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        if self.tool_discovery:
            self.tool_discovery.clear_cache()
        
        if self.tool_executor:
            self.tool_executor.clear_history()
        
        logger.info("Cleared all caches")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
