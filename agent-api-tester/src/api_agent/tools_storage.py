import json
import os
import sys
from pathlib import Path
from typing import List, Optional
from .models import ToolDescriptor

class ToolsStorage:
    """Manages persistence of tools between CLI commands."""
    
    def __init__(self, storage_file: str = ".tools_state.json"):
        self.storage_file = Path(storage_file)
    
    def save_tools(self, tools: List[ToolDescriptor]) -> None:
        """Save tools to storage file."""
        tools_data = []
        for tool in tools:
            tool_dict = {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "method": tool.method,
                "path": tool.path,
                "parameters": [
                    {
                        "name": p.name,
                        "location": p.location,
                        "required": p.required,
                        "schema": p.schema,
                        "description": p.description,
                        "example": p.example
                    } for p in tool.parameters
                ],
                "request_schema": tool.request_schema,
                "response_schema": tool.response_schema,
                "auth": {
                    "type": tool.auth.type,
                    "scheme": tool.auth.scheme,
                    "bearer_format": tool.auth.bearer_format,
                    "header_name": tool.auth.header_name,
                    "query_name": tool.auth.query_name,
                    "flows": tool.auth.flows
                } if tool.auth else None,
                "examples": [
                    {
                        "name": e.name,
                        "description": e.description,
                        "request": e.request,
                        "response": e.response
                    } for e in tool.examples
                ],
                "tags": tool.tags,
                "summary": tool.summary
            }
            tools_data.append(tool_dict)
        
        with open(self.storage_file, 'w') as f:
            json.dump(tools_data, f, indent=2)
    
    def load_tools(self) -> List[ToolDescriptor]:
        """Load tools from storage file."""
        if not self.storage_file.exists():
            return []
        
        try:
            with open(self.storage_file, 'r') as f:
                tools_data = json.load(f)
            
            tools = []
            for tool_dict in tools_data:
                # Convert parameter dicts back to Param objects
                from .models import Param, ParamLocation, AuthSpec, AuthType, Example
                
                parameters = []
                for param_dict in tool_dict.get("parameters", []):
                    param = Param(
                        name=param_dict["name"],
                        location=ParamLocation(param_dict["location"]),
                        required=param_dict.get("required", False),
                        schema=param_dict.get("schema"),
                        description=param_dict.get("description"),
                        example=param_dict.get("example")
                    )
                    parameters.append(param)
                
                # Convert auth dict back to AuthSpec object
                auth = None
                if tool_dict.get("auth"):
                    auth_dict = tool_dict["auth"]
                    auth = AuthSpec(
                        type=AuthType(auth_dict["type"]),
                        scheme=auth_dict.get("scheme"),
                        bearer_format=auth_dict.get("bearer_format"),
                        header_name=auth_dict.get("header_name"),
                        query_name=auth_dict.get("query_name"),
                        flows=auth_dict.get("flows", {})
                    )
                
                # Convert example dicts back to Example objects
                examples = []
                for example_dict in tool_dict.get("examples", []):
                    example = Example(
                        name=example_dict["name"],
                        description=example_dict.get("description"),
                        value=example_dict.get("request")  # Map old format
                    )
                    examples.append(example)
                
                # Create ToolDescriptor with converted objects
                tool = ToolDescriptor(
                    id=tool_dict["id"],
                    name=tool_dict["name"],
                    description=tool_dict["description"],
                    method=tool_dict["method"],
                    path=tool_dict["path"],
                    parameters=parameters,
                    request_schema=tool_dict.get("request_schema"),
                    response_schema=tool_dict.get("response_schema"),
                    auth=auth,
                    examples=examples,
                    tags=tool_dict.get("tags", []),
                    summary=tool_dict.get("summary"),
                    operation_id=tool_dict.get("id")  # Use id as operation_id
                )
                tools.append(tool)
            
            return tools
        except Exception as e:
            print(f"Error loading tools from storage: {e}", file=sys.stderr)
            return []
    
    def clear_tools(self) -> None:
        """Clear stored tools."""
        if self.storage_file.exists():
            self.storage_file.unlink()
