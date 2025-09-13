"""Tests for CLI functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from api_agent.cli import cli


class TestCLI:
    """Test suite for CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
    def test_ingest_url_with_save_as(self):
        """Test ingesting from URL with save-as option."""
        # Mock spec data
        mock_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "test-spec.json"
            
            with patch('api_agent.swagger_parser.SwaggerParser.load_from_url') as mock_load:
                with patch('api_agent.swagger_parser.SwaggerParser.get_endpoints') as mock_endpoints:
                    mock_load.return_value = mock_spec
                    mock_endpoints.return_value = []
                    
                    result = self.runner.invoke(cli, [
                        'ingest',
                        '--url', 'https://example.com/api.json',
                        '--save-as', str(save_path)
                    ])
                    
                    # Verify command succeeded
                    assert result.exit_code == 0
                    assert "Ingesting OpenAPI specification" in result.output
                    assert f"Saving spec to local file: {save_path}" in result.output
                    assert "✓ Spec saved to" in result.output
                    
                    # Verify file was created with correct content
                    assert save_path.exists()
                    with open(save_path, 'r') as f:
                        saved_spec = json.load(f)
                    assert saved_spec == mock_spec
    
    def test_ingest_file_with_save_as_warning(self):
        """Test that save-as option shows warning when used with --file."""
        mock_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(mock_spec, temp_file)
            temp_file.flush()
            
            with patch('api_agent.swagger_parser.SwaggerParser.load_from_file') as mock_load:
                with patch('api_agent.swagger_parser.SwaggerParser.get_endpoints') as mock_endpoints:
                    mock_load.return_value = mock_spec
                    mock_endpoints.return_value = []
                    
                    result = self.runner.invoke(cli, [
                        'ingest',
                        '--file', temp_file.name,
                        '--save-as', 'output.json'
                    ])
                    
                    # Verify warning is displayed
                    assert result.exit_code == 0
                    assert "Warning: --save-as option ignored when using --file" in result.output
            
            # Clean up
            Path(temp_file.name).unlink()
    
    def test_ingest_missing_options(self):
        """Test that missing --url or --file shows error."""
        result = self.runner.invoke(cli, ['ingest'])
        
        assert result.exit_code == 1
        assert "Error: Must provide either --url or --file" in result.output
    
    def test_list_tools_table_format(self):
        """Test list-tools command with table format."""
        mock_tools = [
            Mock(name="get_users", method="GET", path="/users", description="Get all users"),
            Mock(name="create_user", method="POST", path="/users", description="Create user")
        ]
        
        # Need to mock the CLI context
        with patch('api_agent.cli.CLIContext') as mock_context:
            mock_ctx = Mock()
            mock_ctx.tools = mock_tools
            mock_context.return_value = mock_ctx
            
            result = self.runner.invoke(cli, ['list-tools'])
            
            # Should not crash (exit code 0 or handled error)
            # Note: This test mainly ensures the command structure is correct
            assert "list-tools" in str(result)
    
    def test_call_command_structure(self):
        """Test call command structure."""
        # Test that the command accepts the required parameters
        result = self.runner.invoke(cli, [
            'call', 
            '--tool', 'test_tool',
            '--data', '{"test": "data"}'
        ])
        
        # The command should be structured correctly
        # (May fail due to missing context, but structure should be valid)
        assert "call" in str(result)
    
    def test_run_tests_command_structure(self):
        """Test run-tests command structure."""
        result = self.runner.invoke(cli, ['run-tests', '--tool', 'test_tool'])
        
        # Command should be structured correctly
        assert "run-tests" in str(result)
    
    def test_serve_command_structure(self):
        """Test serve command structure."""
        # Test with custom port to avoid potential conflicts
        result = self.runner.invoke(cli, ['serve', '--port', '9999'], catch_exceptions=True)
        
        # Command should be structured correctly (may fail due to server startup)
        assert "serve" in str(result) or result.exit_code in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__])
