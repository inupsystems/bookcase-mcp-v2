"""Tests for SwaggerParser module."""

import json
import pytest
from unittest.mock import patch, mock_open

from api_agent.swagger_parser import SwaggerParser, SwaggerParseError


class TestSwaggerParser:
    """Test cases for SwaggerParser."""
    
    def test_init(self):
        """Test parser initialization."""
        parser = SwaggerParser(base_url="https://api.example.com", timeout=60)
        assert parser.base_url == "https://api.example.com"
        assert parser.timeout == 60
        assert parser.spec is None
        assert parser.tools == []
    
    def test_load_from_file_json(self, swagger_parser, sample_openapi_spec):
        """Test loading OpenAPI spec from JSON file."""
        json_content = json.dumps(sample_openapi_spec)
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=json_content), \
             patch("pathlib.Path.suffix", ".json"):
            
            spec = swagger_parser.load_from_file("test.json")
            
            assert spec == sample_openapi_spec
            assert swagger_parser.spec == sample_openapi_spec
    
    def test_load_from_file_yaml(self, swagger_parser, sample_openapi_spec):
        """Test loading OpenAPI spec from YAML file."""
        import yaml
        yaml_content = yaml.dump(sample_openapi_spec)
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=yaml_content), \
             patch("pathlib.Path.suffix", ".yaml"):
            
            spec = swagger_parser.load_from_file("test.yaml")
            
            assert spec == sample_openapi_spec
            assert swagger_parser.spec == sample_openapi_spec
    
    def test_load_from_file_not_found(self, swagger_parser):
        """Test error when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(SwaggerParseError, match="File not found"):
                swagger_parser.load_from_file("nonexistent.json")
    
    def test_load_from_file_invalid_json(self, swagger_parser):
        """Test error with invalid JSON."""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="invalid json"), \
             patch("pathlib.Path.suffix", ".json"):
            
            with pytest.raises(SwaggerParseError, match="Failed to parse"):
                swagger_parser.load_from_file("invalid.json")
    
    @patch('httpx.Client')
    def test_load_from_url_json(self, mock_client, swagger_parser, sample_openapi_spec):
        """Test loading OpenAPI spec from URL (JSON)."""
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = sample_openapi_spec
        mock_response.raise_for_status.return_value = None
        
        spec = swagger_parser.load_from_url("https://api.example.com/openapi.json")
        
        assert spec == sample_openapi_spec
        assert swagger_parser.spec == sample_openapi_spec
    
    @patch('httpx.Client')
    def test_load_from_url_yaml(self, mock_client, swagger_parser, sample_openapi_spec):
        """Test loading OpenAPI spec from URL (YAML)."""
        import yaml
        yaml_content = yaml.dump(sample_openapi_spec)
        
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/yaml"}
        mock_response.text = yaml_content
        mock_response.raise_for_status.return_value = None
        
        spec = swagger_parser.load_from_url("https://api.example.com/openapi.yaml")
        
        assert spec == sample_openapi_spec
        assert swagger_parser.spec == sample_openapi_spec
    
    @patch('httpx.Client')
    def test_load_from_url_http_error(self, mock_client, swagger_parser):
        """Test HTTP error when loading from URL."""
        import httpx
        mock_client.return_value.__enter__.return_value.get.side_effect = httpx.RequestError("Connection failed")
        
        with pytest.raises(SwaggerParseError, match="Failed to fetch"):
            swagger_parser.load_from_url("https://api.example.com/openapi.json")
    
    def test_get_endpoints_no_spec(self, swagger_parser):
        """Test error when trying to get endpoints without loaded spec."""
        with pytest.raises(SwaggerParseError, match="No OpenAPI specification loaded"):
            swagger_parser.get_endpoints()
    
    def test_get_endpoints_success(self, swagger_parser, sample_openapi_spec):
        """Test successful extraction of endpoints."""
        swagger_parser.spec = sample_openapi_spec
        tools = swagger_parser.get_endpoints()
        
        assert len(tools) == 3  # GET /users, POST /users, GET /users/{id}
        
        # Check first tool (list_users)
        list_users = next((t for t in tools if t.id == "list_users"), None)
        assert list_users is not None
        assert list_users.method == "GET"
        assert list_users.path == "/users"
        assert list_users.name == "List users"
        assert len(list_users.parameters) == 1
        assert list_users.parameters[0].name == "limit"
        
        # Check second tool (create_user)
        create_user = next((t for t in tools if t.id == "create_user"), None)
        assert create_user is not None
        assert create_user.method == "POST"
        assert create_user.path == "/users"
        assert create_user.request_schema is not None
        
        # Check third tool (get_user)
        get_user = next((t for t in tools if t.id == "get_user"), None)
        assert get_user is not None
        assert get_user.method == "GET"
        assert get_user.path == "/users/{id}"
        assert len(get_user.parameters) == 1
        assert get_user.parameters[0].name == "id"
        assert get_user.parameters[0].required is True
    
    def test_get_tool_by_id(self, parsed_tools, swagger_parser):
        """Test getting tool by ID."""
        swagger_parser.tools = parsed_tools
        
        tool = swagger_parser.get_tool_by_id("create_user")
        assert tool is not None
        assert tool.id == "create_user"
        
        # Test non-existent tool
        tool = swagger_parser.get_tool_by_id("nonexistent")
        assert tool is None
    
    def test_get_server_urls(self, swagger_parser, sample_openapi_spec):
        """Test getting server URLs."""
        swagger_parser.spec = sample_openapi_spec
        urls = swagger_parser.get_server_urls()
        
        assert len(urls) == 1
        assert urls[0] == "https://api.example.com/v1"
    
    def test_get_info(self, swagger_parser, sample_openapi_spec):
        """Test getting API info."""
        swagger_parser.spec = sample_openapi_spec
        info = swagger_parser.get_info()
        
        assert info["title"] == "Sample API"
        assert info["version"] == "1.0.0"
        assert info["description"] == "A sample API for testing"
    
    def test_export_tools_json(self, swagger_parser, parsed_tools, tmp_path):
        """Test exporting tools to JSON file."""
        swagger_parser.tools = parsed_tools
        output_file = tmp_path / "tools.json"
        
        swagger_parser.export_tools_json(output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            exported_data = json.load(f)
        
        assert len(exported_data) == len(parsed_tools)
        assert all("id" in tool for tool in exported_data)
        assert all("name" in tool for tool in exported_data)
    
    def test_parse_operation_with_operation_id(self, swagger_parser):
        """Test parsing operation with explicit operation ID."""
        operation = {
            "operationId": "custom_operation",
            "summary": "Custom Operation",
            "description": "A custom operation",
            "responses": {"200": {"description": "Success"}}
        }
        
        tool = swagger_parser._parse_operation("/test", "GET", operation, {})
        
        assert tool is not None
        assert tool.id == "custom_operation"
        assert tool.operation_id == "custom_operation"
    
    def test_parse_operation_without_operation_id(self, swagger_parser):
        """Test parsing operation without operation ID (auto-generated)."""
        operation = {
            "summary": "Test Operation",
            "responses": {"200": {"description": "Success"}}
        }
        
        tool = swagger_parser._parse_operation("/test/{id}", "POST", operation, {})
        
        assert tool is not None
        assert tool.id == "post_test_id"  # Auto-generated from method and path
    
    def test_parse_operation_with_request_body(self, swagger_parser):
        """Test parsing operation with request body."""
        operation = {
            "operationId": "test_op",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}}
                        }
                    }
                }
            },
            "responses": {"200": {"description": "Success"}}
        }
        
        tool = swagger_parser._parse_operation("/test", "POST", operation, {})
        
        assert tool is not None
        assert tool.request_schema is not None
        assert tool.request_schema["type"] == "object"
    
    def test_parse_operation_with_parameters(self, swagger_parser):
        """Test parsing operation with parameters."""
        operation = {
            "operationId": "test_op",
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"}
                },
                {
                    "name": "limit",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer"},
                    "example": 10
                }
            ],
            "responses": {"200": {"description": "Success"}}
        }
        
        tool = swagger_parser._parse_operation("/test/{id}", "GET", operation, {})
        
        assert tool is not None
        assert len(tool.parameters) == 2
        
        path_params = tool.get_path_params()
        assert len(path_params) == 1
        assert path_params[0].name == "id"
        assert path_params[0].required is True
        
        query_params = tool.get_query_params()
        assert len(query_params) == 1
        assert query_params[0].name == "limit"
        assert query_params[0].required is False
        assert query_params[0].example == 10
