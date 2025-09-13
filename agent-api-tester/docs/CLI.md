# CLI Reference Guide

The `api-agent` command-line interface provides comprehensive tools for working with OpenAPI specifications and executing API operations through the MCP protocol.

## Commands Overview

### `ingest` - Import OpenAPI Specification

Import and process OpenAPI/Swagger specifications from URLs or local files.

**Syntax:**
```bash
api-agent ingest [OPTIONS]
```

**Options:**
- `--url TEXT`: Load specification from URL
- `--file PATH`: Load specification from local file
- `--env TEXT`: Environment name for configuration (default: "default")
- `--save-as PATH`: Save downloaded spec to local file (only with --url)

**Examples:**

```bash
# Load from URL
api-agent ingest --url https://petstore.swagger.io/v2/swagger.json

# Load from URL and save locally
api-agent ingest --url https://petstore.swagger.io/v2/swagger.json --save-as ./petstore-api.json

# Load from local file
api-agent ingest --file ./openapi.yaml --env production

# Load with specific environment
api-agent ingest --url https://api.example.com/v3/api-docs --env staging
```

**Notes:**
- The `--save-as` option is only available when using `--url`
- Saved files are formatted as JSON with proper indentation
- Environment settings are stored for subsequent commands

### `list-tools` - Display Available Tools

Show all extracted API endpoints as MCP tools.

**Syntax:**
```bash
api-agent list-tools [OPTIONS]
```

**Options:**
- `--format [table|json]`: Output format (default: table)

**Examples:**

```bash
# Display as formatted table
api-agent list-tools

# Output as JSON
api-agent list-tools --format json
```

### `call` - Execute API Tool

Execute a specific API endpoint with provided data.

**Syntax:**
```bash
api-agent call [OPTIONS]
```

**Options:**
- `--tool TEXT`: Tool name to execute (required)
- `--data TEXT`: JSON data for the request (required)

**Examples:**

```bash
# Simple API call
api-agent call --tool get_user --data '{"id": 123}'

# Complex data structure
api-agent call --tool create_order --data '{
  "user_id": 456,
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 3, "quantity": 1}
  ],
  "shipping_address": {
    "street": "123 Main St",
    "city": "São Paulo",
    "country": "Brazil"
  }
}'
```

### `run-tests` - Execute Automated Tests

Generate and run automated test cases for API endpoints.

**Syntax:**
```bash
api-agent run-tests [OPTIONS]
```

**Options:**
- `--tool TEXT`: Specific tool to test (optional, tests all if not provided)
- `--output PATH`: Save test results to file

**Examples:**

```bash
# Test all tools
api-agent run-tests

# Test specific tool
api-agent run-tests --tool create_user

# Save results to file
api-agent run-tests --tool payment_process --output ./test-results.json

# Test all and save comprehensive report
api-agent run-tests --output ./full-test-report.json
```

### `serve` - Start MCP Server

Start the MCP protocol server for integration with LLM agents.

**Syntax:**
```bash
api-agent serve [OPTIONS]
```

**Options:**
- `--host TEXT`: Host address (default: localhost)
- `--port INTEGER`: Port number (default: 8000)

**Examples:**

```bash
# Start on default port
api-agent serve

# Start on custom port
api-agent serve --port 9000

# Start on all interfaces
api-agent serve --host 0.0.0.0 --port 8080
```

## Workflow Examples

### Complete API Testing Workflow

```bash
# 1. Ingest API specification and save locally
api-agent ingest --url https://api.example.com/v3/api-docs --save-as ./api-spec.json

# 2. Review available endpoints
api-agent list-tools

# 3. Test specific functionality
api-agent call --tool get_status --data '{}'

# 4. Run comprehensive tests
api-agent run-tests --output ./test-results.json

# 5. Start MCP server for agent integration
api-agent serve --port 8000
```

### Development and Debugging

```bash
# Load local spec during development
api-agent ingest --file ./dev-api.yaml --env development

# Test specific endpoint during debugging
api-agent call --tool debug_endpoint --data '{"debug": true, "level": "verbose"}'

# Generate test cases for new endpoint
api-agent run-tests --tool new_feature --output ./new-feature-tests.json
```

### Production Integration

```bash
# Load production API spec
api-agent ingest --url https://prod-api.company.com/v1/openapi.json --env production

# Validate all endpoints
api-agent run-tests --output ./production-validation.json

# Start production MCP server
api-agent serve --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Settings

Environments are stored in the CLI context and persist across commands in the same session:

- `default`: Standard configuration
- `development`: Development settings with verbose logging
- `staging`: Staging environment configuration
- `production`: Production settings with optimized performance

### Authentication

Configure authentication in your environment:

```bash
# Set API key for current session
export API_KEY="your-api-key-here"

# Set Bearer token
export BEARER_TOKEN="your-bearer-token"

# Set basic auth credentials
export BASIC_AUTH_USER="username"
export BASIC_AUTH_PASS="password"
```

## Error Handling

The CLI provides detailed error messages and suggestions:

- **Specification Loading Errors**: Check URL accessibility and file formats
- **Authentication Errors**: Verify credentials and API key configuration
- **Tool Execution Errors**: Review request data format and required parameters
- **Server Errors**: Check network connectivity and API endpoint availability

## Output Formats

### Table Format (Default)
```
┌──────────────┬─────────────┬────────────────────────┐
│ Tool Name    │ Method      │ Description            │
├──────────────┼─────────────┼────────────────────────┤
│ get_users    │ GET         │ Retrieve all users     │
│ create_user  │ POST        │ Create a new user      │
└──────────────┴─────────────┴────────────────────────┘
```

### JSON Format
```json
{
  "tools": [
    {
      "name": "get_users",
      "method": "GET",
      "path": "/users",
      "description": "Retrieve all users"
    }
  ]
}
```

## Integration with MCP Protocol

The CLI seamlessly integrates with the Model Context Protocol:

1. **Discovery**: Tools are automatically discoverable by MCP clients
2. **Invocation**: Direct tool execution through standardized protocol
3. **Validation**: Input/output validation with comprehensive error reporting
4. **Documentation**: Automatic generation of tool documentation from OpenAPI specs

For more information about MCP integration, see the [Architecture Guide](./architecture.md).
