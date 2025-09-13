"""OpenAPI/Swagger specification parser."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
import yaml

from .models import AuthSpec, Example, Param, ToolDescriptor

logger = logging.getLogger(__name__)


class SwaggerParseError(Exception):
    """Exception raised when parsing OpenAPI/Swagger specification fails."""
    pass


class SwaggerParser:
    """Parser for OpenAPI/Swagger specifications."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """Initialize parser.
        
        Args:
            base_url: Base URL for resolving relative paths
            timeout: Timeout for HTTP requests in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.spec: Optional[Dict[str, Any]] = None
        self.tools: List[ToolDescriptor] = []
        self._resolved_refs: Dict[str, Dict[str, Any]] = {}  # Cache for resolved references
    
    def load_from_url(self, url: str) -> Dict[str, Any]:
        """Load OpenAPI specification from URL.
        
        Args:
            url: URL to OpenAPI specification
            
        Returns:
            Parsed OpenAPI specification
            
        Raises:
            SwaggerParseError: If loading or parsing fails
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "")
                
                if "application/json" in content_type:
                    self.spec = response.json()
                elif "application/yaml" in content_type or "text/yaml" in content_type:
                    self.spec = yaml.safe_load(response.text)
                else:
                    # Try JSON first, then YAML
                    try:
                        self.spec = response.json()
                    except json.JSONDecodeError:
                        try:
                            self.spec = yaml.safe_load(response.text)
                        except yaml.YAMLError as e:
                            raise SwaggerParseError(f"Failed to parse as JSON or YAML: {e}")
                
                logger.info(f"Successfully loaded OpenAPI spec from {url}")
                return self.spec
                
        except httpx.RequestError as e:
            raise SwaggerParseError(f"Failed to fetch specification from {url}: {e}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise SwaggerParseError(f"Failed to parse specification: {e}")
    
    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load OpenAPI specification from file.
        
        Args:
            file_path: Path to OpenAPI specification file
            
        Returns:
            Parsed OpenAPI specification
            
        Raises:
            SwaggerParseError: If loading or parsing fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise SwaggerParseError(f"File not found: {file_path}")
            
            content = path.read_text(encoding="utf-8")
            
            if path.suffix.lower() in [".json"]:
                self.spec = json.loads(content)
            elif path.suffix.lower() in [".yaml", ".yml"]:
                self.spec = yaml.safe_load(content)
            else:
                # Try JSON first, then YAML
                try:
                    self.spec = json.loads(content)
                except json.JSONDecodeError:
                    try:
                        self.spec = yaml.safe_load(content)
                    except yaml.YAMLError as e:
                        raise SwaggerParseError(f"Failed to parse as JSON or YAML: {e}")
            
            logger.info(f"Successfully loaded OpenAPI spec from {file_path}")
            return self.spec
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise SwaggerParseError(f"Failed to parse specification: {e}")
        except Exception as e:
            raise SwaggerParseError(f"Failed to load file {file_path}: {e}")
    
    def _ensure_array_items(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all array schemas have items property defined.
        
        Args:
            schema: Schema to validate
            
        Returns:
            Schema with items property added to arrays if missing
        """
        if not isinstance(schema, dict):
            return schema
            
        # Make a copy to avoid modifying original
        result = schema.copy()
        
        # If this is an array without items, add default
        if result.get("type") == "array" and "items" not in result:
            result["items"] = {"type": "string"}
        
        # Recursively check nested schemas
        if "properties" in result:
            result["properties"] = {
                key: self._ensure_array_items(value) 
                for key, value in result["properties"].items()
            }
        
        if "items" in result and isinstance(result["items"], dict):
            result["items"] = self._ensure_array_items(result["items"])
        
        if "additionalProperties" in result and isinstance(result["additionalProperties"], dict):
            result["additionalProperties"] = self._ensure_array_items(result["additionalProperties"])
        
        # Handle allOf, anyOf, oneOf
        for key in ["allOf", "anyOf", "oneOf"]:
            if key in result and isinstance(result[key], list):
                result[key] = [self._ensure_array_items(item) for item in result[key]]
        
        return result

    def _resolve_ref(self, ref_path: str) -> Dict[str, Any]:
        """Resolve a $ref reference to its actual schema.
        
        Args:
            ref_path: Reference path like "#/components/schemas/User"
            
        Returns:
            Resolved schema object
            
        Raises:
            SwaggerParseError: If reference cannot be resolved
        """
        if ref_path in self._resolved_refs:
            return self._resolved_refs[ref_path]
        
        if not ref_path.startswith("#/"):
            raise SwaggerParseError(f"External references not supported: {ref_path}")
        
        # Parse reference path
        path_parts = ref_path[2:].split("/")  # Remove "#/" prefix
        
        # Navigate through the spec to find the referenced object
        current = self.spec
        for part in path_parts:
            if not isinstance(current, dict) or part not in current:
                raise SwaggerParseError(f"Reference not found: {ref_path}")
            current = current[part]
        
        # Recursively resolve any nested references
        resolved = self._resolve_schema(current)
        self._resolved_refs[ref_path] = resolved
        return resolved
    
    def _resolve_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve all $ref references in a schema.
        
        Args:
            schema: Schema object that may contain references
            
        Returns:
            Schema with all references resolved
        """
        if not isinstance(schema, dict):
            return schema
        
        # If this is a reference, resolve it
        if "$ref" in schema:
            return self._resolve_ref(schema["$ref"])
        
        # Recursively resolve references in nested objects
        resolved = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_schema(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_schema(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                resolved[key] = value
        
        # Special handling for array schemas with item references
        if resolved.get("type") == "array" and "items" in resolved:
            if isinstance(resolved["items"], dict):
                resolved["items"] = self._resolve_schema(resolved["items"])
        
        # Ensure all arrays have items property
        resolved = self._ensure_array_items(resolved)
        
        return resolved
    
    def get_endpoints(self) -> List[ToolDescriptor]:
        """Extract endpoints from loaded OpenAPI specification.
        
        Returns:
            List of tool descriptors for each endpoint
            
        Raises:
            SwaggerParseError: If no specification is loaded or parsing fails
        """
        if not self.spec:
            raise SwaggerParseError("No OpenAPI specification loaded")
        
        try:
            self.tools = []
            paths = self.spec.get("paths", {})
            servers = self.spec.get("servers", [])
            security_schemes = self.spec.get("components", {}).get("securitySchemes", {})
            
            # Set base URL from spec if not provided
            if not self.base_url and servers:
                self.base_url = servers[0].get("url", "")
            
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.lower() in ["get", "post", "put", "patch", "delete", "head", "options"]:
                        tool = self._parse_operation(
                            path, method.upper(), operation, security_schemes
                        )
                        if tool:
                            self.tools.append(tool)
            
            logger.info(f"Parsed {len(self.tools)} endpoints from OpenAPI specification")
            return self.tools
            
        except Exception as e:
            raise SwaggerParseError(f"Failed to parse endpoints: {e}")
    
    def _parse_operation(
        self, 
        path: str, 
        method: str, 
        operation: Dict[str, Any],
        security_schemes: Dict[str, Any]
    ) -> Optional[ToolDescriptor]:
        """Parse a single OpenAPI operation into a ToolDescriptor.
        
        Args:
            path: API path
            method: HTTP method
            operation: OpenAPI operation object
            security_schemes: Security schemes from OpenAPI spec
            
        Returns:
            ToolDescriptor or None if parsing fails
        """
        try:
            operation_id = operation.get("operationId")
            if not operation_id:
                # Generate operation ID from method and path
                operation_id = f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"
            
            # Parse parameters
            parameters = []
            for param_data in operation.get("parameters", []):
                # Resolve schema references in parameter
                resolved_param_data = param_data.copy()
                if "schema" in resolved_param_data:
                    resolved_param_data["schema"] = self._resolve_schema(resolved_param_data["schema"])
                
                param = Param.from_openapi(resolved_param_data)
                parameters.append(param)
            
            # Parse request body schema
            request_schema = None
            request_body = operation.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                if "application/json" in content:
                    raw_schema = content["application/json"].get("schema")
                    if raw_schema:
                        request_schema = self._resolve_schema(raw_schema)
            
            # Parse response schema (use 200 response as default)
            response_schema = None
            responses = operation.get("responses", {})
            success_response = responses.get("200") or responses.get("201") or responses.get("204")
            if success_response:
                content = success_response.get("content", {})
                if "application/json" in content:
                    raw_schema = content["application/json"].get("schema")
                    if raw_schema:
                        response_schema = self._resolve_schema(raw_schema)
            
            # Parse authentication
            auth = None
            security = operation.get("security", [])
            if security and security_schemes:
                # Use first security requirement
                for security_req in security:
                    for scheme_name in security_req:
                        if scheme_name in security_schemes:
                            auth = AuthSpec.from_openapi(security_schemes[scheme_name])
                            break
                    if auth:
                        break
            
            # Parse examples
            examples = []
            if request_body:
                content = request_body.get("content", {})
                for media_type, media_content in content.items():
                    for example_name, example_data in media_content.get("examples", {}).items():
                        example = Example(
                            name=example_name,
                            summary=example_data.get("summary"),
                            description=example_data.get("description"),
                            value=example_data.get("value"),
                            external_value=example_data.get("externalValue")
                        )
                        examples.append(example)
            
            tool = ToolDescriptor(
                id=operation_id,
                name=operation.get("summary", operation_id),
                description=operation.get("description", f"{method} {path}"),
                method=method,
                path=path,
                parameters=parameters,
                request_schema=request_schema,
                response_schema=response_schema,
                auth=auth,
                examples=examples,
                tags=operation.get("tags", []),
                summary=operation.get("summary"),
                operation_id=operation_id
            )
            
            return tool
            
        except Exception as e:
            logger.warning(f"Failed to parse operation {method} {path}: {e}")
            return None
    
    def get_tool_by_id(self, tool_id: str) -> Optional[ToolDescriptor]:
        """Get tool descriptor by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            ToolDescriptor or None if not found
        """
        return next((tool for tool in self.tools if tool.id == tool_id), None)
    
    def get_tools_by_tag(self, tag: str) -> List[ToolDescriptor]:
        """Get tools by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of matching tools
        """
        return [tool for tool in self.tools if tag in tool.tags]
    
    def get_server_urls(self) -> List[str]:
        """Get server URLs from OpenAPI specification.
        
        Returns:
            List of server URLs
        """
        if not self.spec:
            return []
        
        servers = self.spec.get("servers", [])
        return [server.get("url", "") for server in servers]
    
    def get_info(self) -> Dict[str, Any]:
        """Get API information from OpenAPI specification.
        
        Returns:
            API info object
        """
        if not self.spec:
            return {}
        
        return self.spec.get("info", {})
    
    def export_tools_json(self, file_path: Union[str, Path]) -> None:
        """Export parsed tools to JSON file.
        
        Args:
            file_path: Output file path
        """
        tools_data = []
        for tool in self.tools:
            tool_dict = {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "method": tool.method,
                "path": tool.path,
                "parameters": [
                    {
                        "name": p.name,
                        "location": p.location.value,
                        "required": p.required,
                        "schema": p.schema,
                        "example": p.example,
                        "description": p.description
                    }
                    for p in tool.parameters
                ],
                "request_schema": tool.request_schema,
                "response_schema": tool.response_schema,
                "auth": {
                    "type": tool.auth.type.value,
                    "scheme": tool.auth.scheme,
                    "bearer_format": tool.auth.bearer_format,
                    "header_name": tool.auth.header_name,
                    "query_name": tool.auth.query_name
                } if tool.auth else None,
                "tags": tool.tags,
                "summary": tool.summary
            }
            tools_data.append(tool_dict)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tools_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(tools_data)} tools to {file_path}")
