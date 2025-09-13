"""Test generator for creating comprehensive test suites from API tools."""

import json
import logging
import random
import string
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .models import ToolDescriptor, TestCase, TestResult, TestSuite, ParamLocation
from .http_executor import HTTPExecutor

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generate and execute comprehensive test suites for API tools."""
    
    def __init__(self, executor: Optional[HTTPExecutor] = None):
        """Initialize test generator.
        
        Args:
            executor: HTTP executor for running tests
        """
        self.executor = executor or HTTPExecutor()
        self.test_cases: List[TestCase] = []
    
    def generate_test_cases(self, tool: ToolDescriptor) -> List[TestCase]:
        """Generate comprehensive test cases for a tool.
        
        Args:
            tool: Tool descriptor
            
        Returns:
            List of generated test cases
        """
        test_cases = []
        
        # Generate positive test cases
        test_cases.extend(self._generate_positive_tests(tool))
        
        # Generate negative test cases
        test_cases.extend(self._generate_negative_tests(tool))
        
        # Generate edge case tests
        test_cases.extend(self._generate_edge_tests(tool))
        
        # Generate security tests
        test_cases.extend(self._generate_security_tests(tool))
        
        # Generate boundary tests
        test_cases.extend(self._generate_boundary_tests(tool))
        
        logger.info(f"Generated {len(test_cases)} test cases for tool {tool.id}")
        return test_cases
    
    def _generate_positive_tests(self, tool: ToolDescriptor) -> List[TestCase]:
        """Generate positive test cases (happy path).
        
        Args:
            tool: Tool descriptor
            
        Returns:
            List of positive test cases
        """
        tests = []
        
        # Use examples from OpenAPI spec if available
        if tool.examples:
            for i, example in enumerate(tool.examples):
                test_case = TestCase(
                    name=f"{tool.id}_positive_example_{i+1}",
                    description=f"Positive test using example: {example.name}",
                    tool_id=tool.id,
                    inputs=example.value if isinstance(example.value, dict) else {},
                    expected_status=200,
                    test_type="positive",
                    tags=["positive", "example"]
                )
                tests.append(test_case)
        
        # Generate test with valid data
        valid_inputs = self._generate_valid_inputs(tool)
        if valid_inputs:
            test_case = TestCase(
                name=f"{tool.id}_positive_valid_data",
                description="Positive test with valid generated data",
                tool_id=tool.id,
                inputs=valid_inputs,
                expected_status=200 if tool.method.upper() == "GET" else 201,
                test_type="positive",
                tags=["positive", "generated"]
            )
            tests.append(test_case)
        
        # Generate minimal valid request
        minimal_inputs = self._generate_minimal_inputs(tool)
        if minimal_inputs:
            test_case = TestCase(
                name=f"{tool.id}_positive_minimal",
                description="Positive test with minimal required data",
                tool_id=tool.id,
                inputs=minimal_inputs,
                expected_status=200 if tool.method.upper() == "GET" else 201,
                test_type="positive",
                tags=["positive", "minimal"]
            )
            tests.append(test_case)
        
        return tests
    
    def _generate_negative_tests(self, tool: ToolDescriptor) -> List[TestCase]:
        """Generate negative test cases.
        
        Args:
            tool: Tool descriptor
            
        Returns:
            List of negative test cases
        """
        tests = []
        
        # Missing required parameters
        for param in tool.parameters:
            if param.required:
                inputs = self._generate_valid_inputs(tool)
                if param.name in inputs:
                    del inputs[param.name]
                
                test_case = TestCase(
                    name=f"{tool.id}_negative_missing_{param.name}",
                    description=f"Negative test missing required parameter: {param.name}",
                    tool_id=tool.id,
                    inputs=inputs,
                    expected_status=400,
                    test_type="negative",
                    tags=["negative", "missing_param"]
                )
                tests.append(test_case)
        
        # Invalid data types
        valid_inputs = self._generate_valid_inputs(tool)
        for param in tool.parameters:
            if param.schema and param.name in valid_inputs:
                invalid_inputs = valid_inputs.copy()
                invalid_inputs[param.name] = self._generate_invalid_type_value(param.schema)
                
                test_case = TestCase(
                    name=f"{tool.id}_negative_invalid_type_{param.name}",
                    description=f"Negative test with invalid type for: {param.name}",
                    tool_id=tool.id,
                    inputs=invalid_inputs,
                    expected_status=400,
                    test_type="negative",
                    tags=["negative", "invalid_type"]
                )
                tests.append(test_case)
        
        # Invalid request body structure
        if tool.request_schema and tool.method.upper() in ["POST", "PUT", "PATCH"]:
            test_case = TestCase(
                name=f"{tool.id}_negative_invalid_body",
                description="Negative test with invalid request body structure",
                tool_id=tool.id,
                inputs={"invalid": "structure", "not": "expected"},
                expected_status=400,
                test_type="negative",
                tags=["negative", "invalid_body"]
            )
            tests.append(test_case)
        
        return tests
    
    def _generate_edge_tests(self, tool: ToolDescriptor) -> List[TestCase]:
        """Generate edge case tests.
        
        Args:
            tool: Tool descriptor
            
        Returns:
            List of edge case tests
        """
        tests = []
        
        # Very long strings
        valid_inputs = self._generate_valid_inputs(tool)
        for param in tool.parameters:
            if param.schema and param.schema.get("type") == "string":
                edge_inputs = valid_inputs.copy()
                edge_inputs[param.name] = "x" * 10000  # Very long string
                
                test_case = TestCase(
                    name=f"{tool.id}_edge_long_string_{param.name}",
                    description=f"Edge test with very long string for: {param.name}",
                    tool_id=tool.id,
                    inputs=edge_inputs,
                    expected_status=400,
                    test_type="edge",
                    tags=["edge", "long_string"]
                )
                tests.append(test_case)
        
        # Empty strings where not expected
        for param in tool.parameters:
            if param.schema and param.schema.get("type") == "string" and param.required:
                edge_inputs = valid_inputs.copy()
                edge_inputs[param.name] = ""
                
                test_case = TestCase(
                    name=f"{tool.id}_edge_empty_string_{param.name}",
                    description=f"Edge test with empty string for required: {param.name}",
                    tool_id=tool.id,
                    inputs=edge_inputs,
                    expected_status=400,
                    test_type="edge",
                    tags=["edge", "empty_string"]
                )
                tests.append(test_case)
        
        # Special characters
        for param in tool.parameters:
            if param.schema and param.schema.get("type") == "string":
                edge_inputs = valid_inputs.copy()
                edge_inputs[param.name] = "!@#$%^&*()[]{}|;':\",./<>?"
                
                test_case = TestCase(
                    name=f"{tool.id}_edge_special_chars_{param.name}",
                    description=f"Edge test with special characters for: {param.name}",
                    tool_id=tool.id,
                    inputs=edge_inputs,
                    expected_status=400,
                    test_type="edge",
                    tags=["edge", "special_chars"]
                )
                tests.append(test_case)
        
        return tests
    
    def _generate_security_tests(self, tool: ToolDescriptor) -> List[TestCase]:
        """Generate security-focused test cases.
        
        Args:
            tool: Tool descriptor
            
        Returns:
            List of security test cases
        """
        tests = []
        
        # SQL injection attempts
        valid_inputs = self._generate_valid_inputs(tool)
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for param in tool.parameters:
            if param.schema and param.schema.get("type") == "string":
                for i, payload in enumerate(sql_payloads):
                    security_inputs = valid_inputs.copy()
                    security_inputs[param.name] = payload
                    
                    test_case = TestCase(
                        name=f"{tool.id}_security_sql_injection_{param.name}_{i+1}",
                        description=f"Security test for SQL injection in: {param.name}",
                        tool_id=tool.id,
                        inputs=security_inputs,
                        expected_status=400,
                        test_type="security",
                        tags=["security", "sql_injection"]
                    )
                    tests.append(test_case)
        
        # XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'><script>alert('xss')</script>"
        ]
        
        for param in tool.parameters:
            if param.schema and param.schema.get("type") == "string":
                for i, payload in enumerate(xss_payloads):
                    security_inputs = valid_inputs.copy()
                    security_inputs[param.name] = payload
                    
                    test_case = TestCase(
                        name=f"{tool.id}_security_xss_{param.name}_{i+1}",
                        description=f"Security test for XSS in: {param.name}",
                        tool_id=tool.id,
                        inputs=security_inputs,
                        expected_status=400,
                        test_type="security",
                        tags=["security", "xss"]
                    )
                    tests.append(test_case)
        
        return tests
    
    def _generate_boundary_tests(self, tool: ToolDescriptor) -> List[TestCase]:
        """Generate boundary value tests.
        
        Args:
            tool: Tool descriptor
            
        Returns:
            List of boundary test cases
        """
        tests = []
        
        valid_inputs = self._generate_valid_inputs(tool)
        
        for param in tool.parameters:
            if not param.schema:
                continue
            
            schema_type = param.schema.get("type")
            
            # Integer boundaries
            if schema_type == "integer":
                minimum = param.schema.get("minimum", 0)
                maximum = param.schema.get("maximum", 1000)
                
                boundary_values = [
                    minimum - 1,  # Below minimum
                    minimum,      # At minimum
                    maximum,      # At maximum
                    maximum + 1   # Above maximum
                ]
                
                for i, value in enumerate(boundary_values):
                    boundary_inputs = valid_inputs.copy()
                    boundary_inputs[param.name] = value
                    
                    expected_status = 400 if value < minimum or value > maximum else 200
                    
                    test_case = TestCase(
                        name=f"{tool.id}_boundary_integer_{param.name}_{i+1}",
                        description=f"Boundary test for integer {param.name}: {value}",
                        tool_id=tool.id,
                        inputs=boundary_inputs,
                        expected_status=expected_status,
                        test_type="boundary",
                        tags=["boundary", "integer"]
                    )
                    tests.append(test_case)
            
            # String length boundaries
            elif schema_type == "string":
                min_length = param.schema.get("minLength", 0)
                max_length = param.schema.get("maxLength", 100)
                
                boundary_strings = [
                    "x" * (min_length - 1) if min_length > 0 else "",  # Below minimum
                    "x" * min_length,                                   # At minimum
                    "x" * max_length,                                   # At maximum
                    "x" * (max_length + 1)                             # Above maximum
                ]
                
                for i, value in enumerate(boundary_strings):
                    boundary_inputs = valid_inputs.copy()
                    boundary_inputs[param.name] = value
                    
                    valid_length = min_length <= len(value) <= max_length
                    expected_status = 200 if valid_length else 400
                    
                    test_case = TestCase(
                        name=f"{tool.id}_boundary_string_{param.name}_{i+1}",
                        description=f"Boundary test for string {param.name}: length {len(value)}",
                        tool_id=tool.id,
                        inputs=boundary_inputs,
                        expected_status=expected_status,
                        test_type="boundary",
                        tags=["boundary", "string"]
                    )
                    tests.append(test_case)
        
        return tests
    
    def _generate_valid_inputs(self, tool: ToolDescriptor) -> Dict[str, Any]:
        """Generate valid input data for a tool.
        
        Args:
            tool: Tool descriptor
            
        Returns:
            Dictionary of valid inputs
        """
        inputs = {}
        
        for param in tool.parameters:
            if param.example is not None:
                inputs[param.name] = param.example
            elif param.schema:
                inputs[param.name] = self._generate_value_from_schema(param.schema)
            else:
                # Default values based on parameter name
                inputs[param.name] = self._generate_default_value(param.name)
        
        # Add request body data if schema is available
        if tool.request_schema:
            body_data = self._generate_value_from_schema(tool.request_schema)
            if isinstance(body_data, dict):
                inputs.update(body_data)
        
        return inputs
    
    def _generate_minimal_inputs(self, tool: ToolDescriptor) -> Dict[str, Any]:
        """Generate minimal valid inputs (only required parameters).
        
        Args:
            tool: Tool descriptor
            
        Returns:
            Dictionary of minimal valid inputs
        """
        inputs = {}
        
        for param in tool.parameters:
            if param.required:
                if param.example is not None:
                    inputs[param.name] = param.example
                elif param.schema:
                    inputs[param.name] = self._generate_value_from_schema(param.schema)
                else:
                    inputs[param.name] = self._generate_default_value(param.name)
        
        return inputs
    
    def _generate_value_from_schema(self, schema: Dict[str, Any]) -> Any:
        """Generate a value that conforms to a JSON schema.
        
        Args:
            schema: JSON schema
            
        Returns:
            Generated value
        """
        schema_type = schema.get("type", "string")
        
        if schema_type == "string":
            if schema.get("format") == "email":
                return "test@example.com"
            elif schema.get("format") == "date":
                return "2024-01-01"
            elif schema.get("format") == "date-time":
                return "2024-01-01T00:00:00Z"
            elif schema.get("format") == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"
            else:
                min_length = schema.get("minLength", 1)
                max_length = schema.get("maxLength", 20)
                length = min(max_length, max(min_length, 10))
                return "".join(random.choices(string.ascii_letters, k=length))
        
        elif schema_type == "integer":
            minimum = schema.get("minimum", 1)
            maximum = schema.get("maximum", 100)
            return random.randint(minimum, maximum)
        
        elif schema_type == "number":
            minimum = schema.get("minimum", 1.0)
            maximum = schema.get("maximum", 100.0)
            return round(random.uniform(minimum, maximum), 2)
        
        elif schema_type == "boolean":
            return random.choice([True, False])
        
        elif schema_type == "array":
            items_schema = schema.get("items", {"type": "string"})
            min_items = schema.get("minItems", 1)
            max_items = schema.get("maxItems", 3)
            count = random.randint(min_items, max_items)
            return [self._generate_value_from_schema(items_schema) for _ in range(count)]
        
        elif schema_type == "object":
            obj = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for prop_name, prop_schema in properties.items():
                if prop_name in required or random.choice([True, False]):
                    obj[prop_name] = self._generate_value_from_schema(prop_schema)
            
            return obj
        
        else:
            return "test_value"
    
    def _generate_invalid_type_value(self, schema: Dict[str, Any]) -> Any:
        """Generate a value that doesn't match the schema type.
        
        Args:
            schema: JSON schema
            
        Returns:
            Invalid value
        """
        schema_type = schema.get("type", "string")
        
        if schema_type == "string":
            return 12345  # Number instead of string
        elif schema_type == "integer":
            return "not_a_number"  # String instead of integer
        elif schema_type == "number":
            return "not_a_number"  # String instead of number
        elif schema_type == "boolean":
            return "maybe"  # String instead of boolean
        elif schema_type == "array":
            return "not_an_array"  # String instead of array
        elif schema_type == "object":
            return "not_an_object"  # String instead of object
        else:
            return None
    
    def _generate_default_value(self, param_name: str) -> Any:
        """Generate default value based on parameter name.
        
        Args:
            param_name: Parameter name
            
        Returns:
            Default value
        """
        param_lower = param_name.lower()
        
        if "id" in param_lower:
            return random.randint(1, 1000)
        elif "email" in param_lower:
            return "test@example.com"
        elif "name" in param_lower:
            return "Test Name"
        elif "age" in param_lower:
            return random.randint(18, 65)
        elif "count" in param_lower or "limit" in param_lower:
            return random.randint(1, 100)
        elif "offset" in param_lower or "skip" in param_lower:
            return 0
        else:
            return "test_value"
    
    async def run_test_suite(self, tool: ToolDescriptor) -> TestSuite:
        """Generate and run a complete test suite for a tool.
        
        Args:
            tool: Tool to test
            
        Returns:
            Test suite results
        """
        start_time = datetime.utcnow()
        
        # Generate test cases
        test_cases = self.generate_test_cases(tool)
        
        # Run tests
        results = []
        for test_case in test_cases:
            result = await self._run_single_test(test_case)
            results.append(result)
        
        # Calculate results
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return TestSuite(
            tool_id=tool.id,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results,
            execution_time=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def _run_single_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case.
        
        Args:
            test_case: Test case to run
            
        Returns:
            Test result
        """
        start_time = datetime.utcnow()
        
        try:
            # Get tool descriptor (would need to be passed in or retrieved)
            # For now, create a minimal tool descriptor
            tool = ToolDescriptor(
                id=test_case.tool_id,
                name=test_case.tool_id,
                description=f"Test tool for {test_case.tool_id}",
                method="POST",  # Default method
                path=f"/{test_case.tool_id}"  # Default path
            )
            
            # Execute the tool
            response = await self.executor.execute_tool(
                tool=tool,
                inputs=test_case.inputs
            )
            
            # Check if test passed
            success = (
                response.status_code == test_case.expected_status and
                (not test_case.expected_schema or 
                 self._validate_response_schema(response.data, test_case.expected_schema))
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TestResult(
                test_case=test_case,
                success=success,
                actual_status=response.status_code,
                actual_response=response.data,
                error_message=response.error if not success else None,
                execution_time=execution_time,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TestResult(
                test_case=test_case,
                success=False,
                actual_status=None,
                actual_response=None,
                error_message=str(e),
                execution_time=execution_time,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def _validate_response_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Validate response data against schema.
        
        Args:
            data: Response data
            schema: Expected schema
            
        Returns:
            True if valid, False otherwise
        """
        try:
            from jsonschema import validate
            validate(instance=data, schema=schema)
            return True
        except Exception:
            return False
    
    def export_test_results(self, test_suite: TestSuite, file_path: str) -> None:
        """Export test results to JSON file.
        
        Args:
            test_suite: Test suite results
            file_path: Output file path
        """
        results_data = {
            "tool_id": test_suite.tool_id,
            "summary": {
                "total_tests": test_suite.total_tests,
                "passed": test_suite.passed,
                "failed": test_suite.failed,
                "success_rate": test_suite.passed / test_suite.total_tests if test_suite.total_tests > 0 else 0,
                "execution_time": test_suite.execution_time,
                "timestamp": test_suite.timestamp
            },
            "results": [
                {
                    "name": result.test_case.name,
                    "description": result.test_case.description,
                    "test_type": result.test_case.test_type,
                    "tags": result.test_case.tags,
                    "success": result.success,
                    "expected_status": result.test_case.expected_status,
                    "actual_status": result.actual_status,
                    "error_message": result.error_message,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp
                }
                for result in test_suite.results
            ]
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported test results to {file_path}")
