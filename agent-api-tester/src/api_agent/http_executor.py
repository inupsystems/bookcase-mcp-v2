"""HTTP executor for making API calls with authentication, retries, and validation."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from jsonpath_ng import parse as jsonpath_parse
from jsonschema import validate, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .models import AuthSpec, AuthType, ParamLocation, ToolDescriptor, MCPToolResponse

logger = logging.getLogger(__name__)


class HTTPExecutionError(Exception):
    """Exception raised during HTTP execution."""
    pass


class HTTPExecutor:
    """HTTP executor with authentication, retries, and validation."""
    
    def __init__(self,
                 base_url: Optional[str] = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 auth_config: Optional[Dict[str, str]] = None):
        """Initialize HTTP executor.
        
        Args:
            base_url: Base URL for API calls
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            auth_config: Authentication configuration
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.auth_config = auth_config or {}
        
        # Load auth config from environment if not provided
        if not self.auth_config:
            self.auth_config = {
                "bearer_token": os.getenv("API_BEARER_TOKEN"),
                "api_key": os.getenv("API_KEY"),
                "username": os.getenv("API_USERNAME"),
                "password": os.getenv("API_PASSWORD")
            }
        
        self.session_data: Dict[str, Any] = {}
    
    async def execute_tool(self,
                          tool: ToolDescriptor,
                          inputs: Dict[str, Any],
                          environment: Optional[str] = None) -> MCPToolResponse:
        """Execute a tool by making an HTTP request.
        
        Args:
            tool: Tool descriptor
            inputs: Input parameters
            environment: Environment context (dev/staging/prod)
            
        Returns:
            Tool execution response
        """
        try:
            # Build the request
            url = self._build_url(tool.path, inputs)
            headers = self._build_headers(tool, inputs)
            params = self._build_query_params(tool, inputs)
            body = self._build_request_body(tool, inputs)
            
            # Add authentication
            auth_headers, auth_params = self._build_auth(tool.auth)
            headers.update(auth_headers)
            params.update(auth_params)
            
            # Make the HTTP request with retries
            response = await self._make_request(
                method=tool.method,
                url=url,
                headers=headers,
                params=params,
                json=body
            )
            
            # Validate response
            validation_error = self._validate_response(response, tool.response_schema)
            
            # Extract data for potential chaining
            try:
                response_data = response.json() if response.content else None
                extracted_data = self._extract_chain_data(response_data or {})
            except Exception:
                response_data = response.text if response.content else None
                extracted_data = {}
            
            # Determine error message for non-success responses
            error_message = None
            if not (200 <= response.status_code < 300):
                if response_data and isinstance(response_data, dict):
                    # Try to extract error from API response
                    error_message = (
                        response_data.get('message') or 
                        response_data.get('error') or 
                        response_data.get('detail') or
                        f"HTTP {response.status_code}: {response.reason_phrase}"
                    )
                else:
                    error_message = f"HTTP {response.status_code}: {response.reason_phrase}"
            
            # Use validation error if available, otherwise HTTP error
            final_error = validation_error or error_message
            
            metadata = {
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time": getattr(response, "_execution_time", 0),
                "validation_error": validation_error,
                "extracted_data": extracted_data,
                "environment": environment
            }
            
            return MCPToolResponse(
                success=200 <= response.status_code < 300,
                data=response_data,
                error=final_error,
                metadata=metadata,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            logger.error(f"Failed to execute tool {tool.id}: {e}")
            return MCPToolResponse(
                success=False,
                error=str(e),
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "environment": environment
                }
            )
    
    def _build_url(self, path: str, inputs: Dict[str, Any]) -> str:
        """Build the complete URL with path parameters.
        
        Args:
            path: API path template
            inputs: Input parameters
            
        Returns:
            Complete URL
        """
        # Filter out special MCP parameters
        filtered_inputs = {k: v for k, v in inputs.items() if not k.startswith("__")}
        
        # Replace path parameters
        final_path = path
        for key, value in filtered_inputs.items():
            placeholder = f"{{{key}}}"
            if placeholder in final_path:
                final_path = final_path.replace(placeholder, str(value))
        
        # Combine with base URL
        if self.base_url:
            return urljoin(self.base_url.rstrip("/") + "/", final_path.lstrip("/"))
        else:
            return final_path
    
    def _build_headers(self, tool: ToolDescriptor, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers.
        
        Args:
            tool: Tool descriptor
            inputs: Input parameters
            
        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "api-agent/0.1.0"
        }
        
        # Filter out special MCP parameters
        filtered_inputs = {k: v for k, v in inputs.items() if not k.startswith("__")}
        
        # Add header parameters
        for param in tool.get_header_params():
            if param.name in filtered_inputs:
                headers[param.name] = str(filtered_inputs[param.name])
        
        return headers
    
    def _build_query_params(self, tool: ToolDescriptor, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters.
        
        Args:
            tool: Tool descriptor
            inputs: Input parameters
            
        Returns:
            Query parameters dictionary
        """
        params = {}
        
        # Filter out special MCP parameters
        filtered_inputs = {k: v for k, v in inputs.items() if not k.startswith("__")}
        
        # Add query parameters
        for param in tool.get_query_params():
            if param.name in filtered_inputs:
                params[param.name] = filtered_inputs[param.name]
        
        return params
    
    def _build_request_body(self, tool: ToolDescriptor, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build request body from inputs.
        
        Args:
            tool: Tool descriptor
            inputs: Input parameters
            
        Returns:
            Request body or None
        """
        if tool.method.upper() in ["GET", "DELETE", "HEAD"]:
            return None
        
        # Check for special __request_body__ parameter from MCP
        if "__request_body__" in inputs:
            return inputs["__request_body__"]
        
        # Filter out path and query parameters
        path_param_names = {p.name for p in tool.get_path_params()}
        query_param_names = {p.name for p in tool.get_query_params()}
        header_param_names = {p.name for p in tool.get_header_params()}
        
        body_params = {
            key: value for key, value in inputs.items()
            if key not in path_param_names and 
               key not in query_param_names and
               key not in header_param_names
        }
        
        return body_params if body_params else None
    
    def _build_auth(self, auth_spec: Optional[AuthSpec]) -> tuple[Dict[str, str], Dict[str, str]]:
        """Build authentication headers and parameters.
        
        Args:
            auth_spec: Authentication specification
            
        Returns:
            Tuple of (headers, params)
        """
        headers = {}
        params = {}
        
        if not auth_spec or auth_spec.type == AuthType.NONE:
            return headers, params
        
        if auth_spec.type == AuthType.BEARER:
            token = self.auth_config.get("bearer_token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif auth_spec.type == AuthType.BASIC:
            username = self.auth_config.get("username")
            password = self.auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        elif auth_spec.type == AuthType.API_KEY:
            api_key = self.auth_config.get("api_key")
            if api_key:
                if auth_spec.header_name:
                    headers[auth_spec.header_name] = api_key
                elif auth_spec.query_name:
                    params[auth_spec.query_name] = api_key
        
        return headers, params
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def _make_request(self,
                           method: str,
                           url: str,
                           headers: Dict[str, str],
                           params: Dict[str, Any],
                           json: Optional[Dict[str, Any]]) -> httpx.Response:
        """Make HTTP request with retries.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            json: Request body
            
        Returns:
            HTTP response
        """
        start_time = datetime.utcnow()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json
            )
            
            # Add execution time to response
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            response._execution_time = execution_time
            
            # Log request details
            logger.info(f"{method} {url} -> {response.status_code} ({execution_time:.3f}s)")
            
            # Don't raise for HTTP status codes - let the caller handle them
            # Only retry on network/connection errors (httpx.RequestError)
            
            return response
    
    def _validate_response(self, 
                          response: httpx.Response, 
                          schema: Optional[Dict[str, Any]]) -> Optional[str]:
        """Validate response against JSON schema.
        
        Args:
            response: HTTP response
            schema: JSON schema for validation
            
        Returns:
            Error message if validation fails, None otherwise
        """
        if not schema or not response.content:
            return None
        
        try:
            response_data = response.json()
            validate(instance=response_data, schema=schema)
            return None
        except json.JSONDecodeError as e:
            return f"Invalid JSON response: {e}"
        except ValidationError as e:
            return f"Response validation failed: {e.message}"
        except Exception as e:
            return f"Validation error: {e}"
    
    def _extract_chain_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from response for potential use in chained calls.
        
        Args:
            response_data: Response data
            
        Returns:
            Extracted data for chaining
        """
        extracted = {}
        
        # Common patterns for extracting useful data
        extraction_patterns = {
            "id": ["$.id", "$.data.id", "$._id", "$.result.id"],
            "token": ["$.token", "$.access_token", "$.data.token"],
            "status": ["$.status", "$.state", "$.data.status"],
            "result": ["$.result", "$.data", "$.response"]
        }
        
        for key, patterns in extraction_patterns.items():
            for pattern in patterns:
                try:
                    jsonpath_expr = jsonpath_parse(pattern)
                    matches = jsonpath_expr.find(response_data)
                    if matches:
                        extracted[key] = matches[0].value
                        break
                except Exception:
                    continue
        
        return extracted
    
    def set_session_data(self, key: str, value: Any) -> None:
        """Set session data for use in subsequent requests.
        
        Args:
            key: Data key
            value: Data value
        """
        self.session_data[key] = value
    
    def get_session_data(self, key: str) -> Any:
        """Get session data.
        
        Args:
            key: Data key
            
        Returns:
            Data value or None if not found
        """
        return self.session_data.get(key)
    
    def clear_session_data(self) -> None:
        """Clear all session data."""
        self.session_data.clear()
    
    async def execute_chain(self,
                           tools: List[ToolDescriptor],
                           inputs_list: List[Dict[str, Any]],
                           chain_config: Optional[Dict[str, Any]] = None) -> List[MCPToolResponse]:
        """Execute a chain of tool calls.
        
        Args:
            tools: List of tools to execute in order
            inputs_list: List of inputs for each tool
            chain_config: Configuration for chaining behavior
            
        Returns:
            List of execution responses
        """
        results = []
        
        for i, (tool, inputs) in enumerate(zip(tools, inputs_list)):
            # Use data from previous responses if configured
            if i > 0 and chain_config:
                # Extract data from previous response
                prev_response = results[-1]
                if prev_response.success and prev_response.metadata:
                    extracted_data = prev_response.metadata.get("extracted_data", {})
                    
                    # Apply chaining rules
                    for source_key, target_key in chain_config.get("mappings", {}).items():
                        if source_key in extracted_data:
                            inputs[target_key] = extracted_data[source_key]
            
            # Execute the tool
            result = await self.execute_tool(tool, inputs)
            results.append(result)
            
            # Stop chain on failure if configured
            if not result.success and chain_config.get("stop_on_failure", True):
                break
        
        return results
