"""Connection management for MCP servers."""

import asyncio
import json
import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

import aiohttp

from .config import ConnectionType, ServerConfig
from .models import (
    InitializeRequest,
    MCPMessage,
    ServerInfo,
    ServerStatus,
    ToolsListRequest,
)

logger = logging.getLogger(__name__)


class MCPConnection:
    """Base class for MCP server connections."""
    
    def __init__(self, name: str, config: ServerConfig):
        self.name = name
        self.config = config
        self.status = ServerStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.error_count = 0
        
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        raise NotImplementedError
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        raise NotImplementedError
    
    async def send_message(self, message: MCPMessage) -> Optional[Dict[str, Any]]:
        """Send a message to the MCP server."""
        raise NotImplementedError
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.status == ServerStatus.CONNECTED
    
    def mark_error(self, error: str) -> None:
        """Mark connection as having an error."""
        self.status = ServerStatus.ERROR
        self.last_error = error
        self.error_count += 1
        logger.error(f"Connection {self.name} error: {error}")


class StdioConnection(MCPConnection):
    """STDIO-based MCP connection."""
    
    def __init__(self, name: str, config: ServerConfig):
        super().__init__(name, config)
        self.process: Optional[subprocess.Popen] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        
    async def connect(self) -> bool:
        """Connect to STDIO MCP server."""
        try:
            self.status = ServerStatus.CONNECTING
            
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.env)
            
            # Start the server process
            self.process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.config.cwd,
            )
            
            if self.process.stdin and self.process.stdout:
                self.writer = self.process.stdin
                self.reader = self.process.stdout
                
                # Send initialize message
                init_msg = InitializeRequest(id=1)
                response = await self.send_message(init_msg)
                
                if response and 'result' in response:
                    self.status = ServerStatus.CONNECTED
                    logger.info(f"Connected to STDIO server: {self.name}")
                    return True
                else:
                    self.mark_error("Failed to initialize connection")
                    return False
            else:
                self.mark_error("Failed to get process pipes")
                return False
                
        except Exception as e:
            self.mark_error(f"Connection failed: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from STDIO server."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
        
        self.status = ServerStatus.DISCONNECTED
        logger.info(f"Disconnected from STDIO server: {self.name}")
    
    async def send_message(self, message: MCPMessage) -> Optional[Dict[str, Any]]:
        """Send message to STDIO server."""
        if not self.writer or not self.reader:
            return None
        
        try:
            # Send message
            message_data = message.json() + '\n'
            self.writer.write(message_data.encode('utf-8'))
            await self.writer.drain()
            
            # Read response
            response_line = await asyncio.wait_for(
                self.reader.readline(),
                timeout=self.config.get_timeout_seconds()
            )
            
            if response_line:
                response_data = response_line.decode('utf-8').strip()
                return json.loads(response_data)
            
            return None
            
        except asyncio.TimeoutError:
            self.mark_error("Message timeout")
            return None
        except Exception as e:
            self.mark_error(f"Message send failed: {str(e)}")
            return None


class HTTPConnection(MCPConnection):
    """HTTP-based MCP connection."""
    
    def __init__(self, name: str, config: ServerConfig):
        super().__init__(name, config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = f"http://{config.host}:{config.port}"
        
    async def connect(self) -> bool:
        """Connect to HTTP MCP server."""
        try:
            self.status = ServerStatus.CONNECTING
            
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.get_timeout_seconds())
            )
            
            # Test connection with health check
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    self.status = ServerStatus.CONNECTED
                    logger.info(f"Connected to HTTP server: {self.name}")
                    return True
                else:
                    self.mark_error(f"Health check failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.mark_error(f"HTTP connection failed: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from HTTP server."""
        if self.session:
            await self.session.close()
        
        self.status = ServerStatus.DISCONNECTED
        logger.info(f"Disconnected from HTTP server: {self.name}")
    
    async def send_message(self, message: MCPMessage) -> Optional[Dict[str, Any]]:
        """Send message to HTTP server."""
        if not self.session:
            return None
        
        try:
            # Map MCP methods to HTTP endpoints
            if message.method == "tools/list":
                endpoint = "/mcp/tools"
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        return await response.json()
            
            elif message.method == "tools/call":
                endpoint = "/mcp/invoke"
                payload = {
                    "tool_id": message.params["name"],
                    "inputs": message.params["arguments"]
                }
                async with self.session.post(f"{self.base_url}{endpoint}", json=payload) as response:
                    if response.status == 200:
                        return await response.json()
            
            return None
            
        except Exception as e:
            self.mark_error(f"HTTP message failed: {str(e)}")
            return None


class ConnectionManager:
    """Manages connections to multiple MCP servers."""
    
    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        
    def add_server(self, name: str, config: ServerConfig) -> None:
        """Add a server configuration."""
        if config.type == ConnectionType.STDIO:
            connection = StdioConnection(name, config)
        elif config.type == ConnectionType.HTTP:
            connection = HTTPConnection(name, config)
        else:
            raise ValueError(f"Unsupported connection type: {config.type}")
        
        self.connections[name] = connection
        logger.info(f"Added server configuration: {name} ({config.type})")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all configured servers."""
        results = {}
        tasks = []
        
        for name, connection in self.connections.items():
            task = asyncio.create_task(self._connect_server(name, connection))
            tasks.append(task)
        
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (name, _) in enumerate(self.connections.items()):
            result = completed_tasks[i]
            if isinstance(result, Exception):
                results[name] = False
                logger.error(f"Failed to connect to {name}: {result}")
            else:
                results[name] = result
        
        return results
    
    async def _connect_server(self, name: str, connection: MCPConnection) -> bool:
        """Connect to a single server."""
        try:
            success = await connection.connect()
            if success:
                logger.info(f"Successfully connected to {name}")
            else:
                logger.warning(f"Failed to connect to {name}")
            return success
        except Exception as e:
            connection.mark_error(f"Connection error: {str(e)}")
            return False
    
    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        tasks = []
        
        for connection in self.connections.values():
            if connection.is_connected():
                task = asyncio.create_task(connection.disconnect())
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Disconnected from all servers")
    
    def get_connection(self, server_name: str) -> Optional[MCPConnection]:
        """Get connection by server name."""
        return self.connections.get(server_name)
    
    def get_server_info(self, server_name: str) -> Optional[ServerInfo]:
        """Get server information."""
        connection = self.connections.get(server_name)
        if not connection:
            return None
        
        return ServerInfo(
            name=server_name,
            status=connection.status,
            connection_type=connection.config.type.value,
            last_error=connection.last_error,
            error_count=connection.error_count,
        )
    
    def get_all_server_info(self) -> List[ServerInfo]:
        """Get information for all servers."""
        return [
            self.get_server_info(name)
            for name in self.connections.keys()
            if self.get_server_info(name) is not None
        ]
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected server names."""
        return [
            name for name, connection in self.connections.items()
            if connection.is_connected()
        ]
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all connections."""
        results = {}
        
        for name, connection in self.connections.items():
            if connection.is_connected():
                # Send a simple tools/list request as health check
                tools_request = ToolsListRequest(id=int(time.time()))
                response = await connection.send_message(tools_request)
                results[name] = response is not None
            else:
                results[name] = False
        
        return results
