"""Integration tests for MCP Client."""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_client import MCPClient, MCPConfig


@pytest.mark.asyncio
class TestMCPClientIntegration:
    """Integration tests for MCP Client."""
    
    async def test_full_workflow(self, test_config_data):
        """Test complete client workflow."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config_data, f)
            config_path = f.name
        
        try:
            # Initialize client from config file
            client = MCPClient.from_config_file(config_path)
            
            # Initialize the client
            success = await client.initialize()
            assert success
            
            # Try to connect (may fail for test servers, but should not crash)
            connection_results = await client.connect()
            assert isinstance(connection_results, dict)
            
            # Get server information
            servers = client.get_servers()
            assert len(servers) == 2
            
            # Check client statistics
            stats = client.get_statistics()
            assert stats['initialized'] is True
            assert stats['config']['servers'] == 2
            
            # Perform health check
            health = await client.health_check()
            assert health['initialized'] is True
            assert 'servers' in health
            
            # Clean up
            await client.disconnect()
        
        finally:
            Path(config_path).unlink()
    
    async def test_client_context_manager(self, test_config_data):
        """Test client as async context manager."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config_data, f)
            config_path = f.name
        
        try:
            async with MCPClient.from_config_file(config_path) as client:
                await client.initialize()
                # Client should automatically disconnect when exiting context
                pass
        finally:
            Path(config_path).unlink()
    
    async def test_tool_operations_without_servers(self, test_config_data):
        """Test tool operations when no servers are connected."""
        config = MCPConfig(**test_config_data)
        client = MCPClient(config)
        
        await client.initialize()
        
        # These operations should work even without connected servers
        tools = client.get_tools()
        assert tools == []
        
        tool = client.find_tool("nonexistent")
        assert tool is None
        
        search_results = client.search_tools("test")
        assert search_results == []
        
        history = client.get_execution_history()
        assert history == []
        
        await client.disconnect()
    
    async def test_error_handling(self):
        """Test error handling scenarios."""
        client = MCPClient()
        
        # Should raise error when not initialized
        with pytest.raises(RuntimeError, match="not initialized"):
            await client.connect()
        
        # Should raise error with invalid config
        with pytest.raises(ValueError, match="No configuration"):
            await client.initialize()
        
        # Test with invalid config file
        with pytest.raises(FileNotFoundError):
            MCPClient.from_config_file("nonexistent.json")
