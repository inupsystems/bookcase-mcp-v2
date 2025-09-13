#!/bin/bash

# MCP stdio wrapper script for agent-api-tester
# This script helps debug MCP server initialization

set -e

# Set environment variables
export PYTHONPATH="/home/john/workspace/bookcase-mcp-v2/agent-api-tester/src"
# Remove API_SPEC_FILE to prioritize tools storage
# export API_SPEC_FILE="/home/john/workspace/bookcase-mcp-v2/agent-api-tester/examples/jsonplaceholder-api.json"

# Configure API base URL - update this to match your API server
export API_BASE_URL="http://localhost:8881"

# Log to stderr for debugging (won't interfere with stdio protocol)
echo "Starting agent-api-tester MCP server..." >&2
echo "PYTHONPATH: $PYTHONPATH" >&2
echo "API_BASE_URL: $API_BASE_URL" >&2
echo "Using tools storage (.tools_state.json) if available" >&2

# Change to the correct directory
cd /home/john/workspace/bookcase-mcp-v2/agent-api-tester/src

# Run the MCP stdio server
exec /home/john/workspace/bookcase-mcp-v2/agent-api-tester/venv/bin/python -m api_agent.cli mcp-stdio
