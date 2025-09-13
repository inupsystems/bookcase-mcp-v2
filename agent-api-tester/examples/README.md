# API-Agent Examples

This directory contains examples demonstrating API-Agent functionality.

## Quick Start

1. **Install API-Agent**:
   ```bash
   pip install -e .
   ```

2. **Run the demo**:
   ```bash
   python demo.py
   ```

3. **Try CLI commands**:
   ```bash
   # Ingest OpenAPI spec
   api-agent ingest --file examples/jsonplaceholder-api.json
   
   # List available tools
   api-agent list-tools
   
   # Call a specific tool
   api-agent call --tool list_posts --data '{"_limit": 5}'
   
   # Start MCP server
   api-agent serve --port 8000
   ```

## Files

- `jsonplaceholder-api.json` - JSONPlaceholder API specification
- `demo.py` - Functional demonstration script

## Real API Testing

The JSONPlaceholder API is a real, publicly available REST API perfect for testing:

```bash
# Test real API calls
api-agent ingest --file examples/jsonplaceholder-api.json
api-agent call --tool list_posts --data '{"_limit": 3}'
api-agent call --tool get_user --data '{"id": 1}'
```

## Advanced Usage

### Environment Configuration
```bash
export API_BEARER_TOKEN="your-token-here"
export API_BASE_URL="https://your-api.com"
api-agent ingest --url https://your-api.com/openapi.json
```

### Test Generation
```bash
# Generate and run comprehensive tests
api-agent run-tests --tool list_posts --output test-results.json

# Run specific test types
api-agent run-tests --types positive,negative --parallel
```

### MCP Server Integration
```bash
# Start server
api-agent serve --port 8000

# Test endpoints
curl http://localhost:8000/mcp/tools
curl -X POST http://localhost:8000/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"tool_id": "list_posts", "inputs": {"_limit": 5}}'
```
