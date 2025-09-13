# Architecture Overview

## API-Agent Architecture

API-Agent follows a modular, layered architecture designed for extensibility, testability, and maintainability.

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLI Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   ingest    │ │ list-tools  │ │    call     │ │ run-tests  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  SwaggerParser   │  │   MCPAdapter     │  │ TestGenerator  │ │
│  │                  │  │                  │  │                │ │
│  │ • load_from_url  │  │ • discover_tools │  │ • generate_    │ │
│  │ • load_from_file │  │ • invoke_tool    │  │   test_cases   │ │
│  │ • get_endpoints  │  │ • FastAPI app    │  │ • run_suite    │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Core Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  HTTPExecutor    │  │     Models       │  │   Validation   │ │
│  │                  │  │                  │  │                │ │
│  │ • execute_tool   │  │ • ToolDescriptor │  │ • JSON Schema  │ │
│  │ • auth handling  │  │ • MCPRequest     │  │ • Response     │ │
│  │ • retries        │  │ • TestCase       │  │   validation   │ │
│  │ • validation     │  │ • TestResult     │  │ • Type safety  │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │      HTTP        │  │    Observability │  │     Config     │ │
│  │                  │  │                  │  │                │ │
│  │ • httpx client   │  │ • structured     │  │ • Environment  │ │
│  │ • timeout/retry  │  │   logging        │  │   variables    │ │
│  │ • circuit breaker│  │ • metrics        │  │ • Auth config  │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. CLI Layer (`cli.py`)
- **Purpose**: User interface and command orchestration
- **Key Features**:
  - Command routing and argument parsing
  - Rich console output with tables and colors
  - Context management for CLI state
  - Error handling and user feedback

### 2. Service Layer

#### SwaggerParser (`swagger_parser.py`)
- **Purpose**: OpenAPI/Swagger specification processing
- **Key Features**:
  - Multi-format support (JSON/YAML, URL/file)
  - Robust error handling and validation
  - Tool descriptor generation
  - Metadata extraction (servers, info, schemas)

#### MCPAdapter (`mcp_adapter.py`)
- **Purpose**: Model Context Protocol implementation
- **Key Features**:
  - FastAPI-based REST endpoints
  - Tool discovery and invocation
  - CORS support for web integration
  - Direct tool execution interface

#### TestGenerator (`test_generator.py`)
- **Purpose**: Automated test case generation and execution
- **Key Features**:
  - Multiple test types (positive, negative, edge, security, boundary)
  - Smart data generation from schemas
  - Comprehensive reporting
  - Parallel test execution support

### 3. Core Layer

#### HTTPExecutor (`http_executor.py`)
- **Purpose**: HTTP request execution with enterprise features
- **Key Features**:
  - Authentication handling (Bearer, Basic, API Key)
  - Exponential backoff retry logic
  - Request/response validation
  - Session management for chained calls
  - Circuit breaker pattern

#### Models (`models.py`)
- **Purpose**: Type-safe data structures
- **Key Features**:
  - Pydantic models for validation
  - OpenAPI-compliant schemas
  - Enum-based type safety
  - Rich metadata support

### 4. Infrastructure Layer
- **HTTP Client**: httpx with async support
- **Logging**: Structured JSON logging with contextual information
- **Configuration**: Environment-based config with sensible defaults
- **Validation**: JSON Schema validation for requests/responses

## Data Flow

### Tool Discovery Flow
```
OpenAPI Spec → SwaggerParser → ToolDescriptor[] → MCPAdapter → MCP Discovery Response
```

### Tool Invocation Flow
```
MCP Request → MCPAdapter → HTTPExecutor → External API → Response Validation → MCP Response
```

### Test Generation Flow
```
ToolDescriptor → TestGenerator → TestCase[] → HTTPExecutor → TestResult[] → TestSuite
```

## Design Principles

### 1. Separation of Concerns
- Each module has a single, well-defined responsibility
- Clear interfaces between layers
- Minimal coupling between components

### 2. Type Safety
- Comprehensive type hints throughout
- Pydantic models for runtime validation
- MyPy static type checking

### 3. Error Handling
- Structured error types with context
- Graceful degradation where possible
- Clear error messages for users

### 4. Testability
- Dependency injection for external services
- Mock-friendly interfaces
- Comprehensive test coverage

### 5. Observability
- Structured logging at all levels
- Request tracing and timing
- Error context preservation

### 6. Security
- No secrets in logs
- Input validation and sanitization
- Authentication abstraction

## Extension Points

### 1. Authentication Strategies
Extend `AuthSpec` and `HTTPExecutor._build_auth()` for new auth types:
```python
class CustomAuthSpec(AuthSpec):
    custom_field: str

# Implement in HTTPExecutor
elif auth_spec.type == AuthType.CUSTOM:
    headers["Authorization"] = f"Custom {auth_spec.custom_field}"
```

### 2. Test Generators
Add new test types by extending `TestGenerator`:
```python
def _generate_performance_tests(self, tool: ToolDescriptor) -> List[TestCase]:
    # Custom performance test logic
    pass
```

### 3. Output Formats
Extend CLI with new output formats:
```python
@click.option("--format", type=click.Choice(["table", "json", "yaml", "xml"]))
def list_tools(format):
    # Handle new formats
```

### 4. Protocol Adapters
Implement additional protocol adapters alongside MCP:
```python
class GraphQLAdapter:
    def __init__(self, tools: List[ToolDescriptor]):
        # GraphQL schema generation
        pass
```

## Deployment Patterns

### 1. Standalone CLI
```bash
api-agent ingest --url https://api.example.com/spec
api-agent serve --port 8000
```

### 2. Docker Container
```bash
docker run -p 8000:8000 -e API_BASE_URL=https://api.example.com api-agent
```

### 3. CI/CD Integration
```yaml
- name: API Testing
  run: |
    api-agent ingest --file openapi.json
    api-agent run-tests --output results.json
```

### 4. Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-agent
spec:
  template:
    spec:
      containers:
      - name: api-agent
        image: api-agent:latest
        ports:
        - containerPort: 8000
```

## Performance Considerations

### 1. Concurrency
- Async/await throughout for I/O operations
- Concurrent test execution
- Connection pooling for HTTP clients

### 2. Caching
- Parsed OpenAPI specs cached in memory
- HTTP response caching for immutable data
- Tool descriptor caching

### 3. Resource Management
- Configurable timeouts and limits
- Circuit breaker to prevent cascade failures
- Graceful shutdown handling

### 4. Scalability
- Stateless design for horizontal scaling
- External configuration for multi-environment support
- Health checks for load balancer integration
