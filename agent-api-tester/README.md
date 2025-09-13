# API-Agent

Transform OpenAPI/Swagger specifications into MCP (Model Context Protocol) tools for LLM agents.

## Overview

API-Agent is an engineering product that automatically:
- Reads OpenAPI/Swagger specifications 
- Transforms endpoints into tools compatible with the MCP protocol
- Allows LLM agents to discover and invoke these tools
- Manages HTTP call execution including chaining
- Validates responses against schemas
- Generates E2E test cases automatically
- Integrates with CI/CD pipelines

## Features

- **OpenAPI Parser**: Ingests specs via URL or local file
- **MCP Adapter**: Exposes tools for agent discovery and invocation
- **HTTP Executor**: Handles authentication, retries, timeouts, and call chaining
- **Response Validator**: Validates payloads against JSON schemas
- **Test Generator**: Creates comprehensive test suites automatically
- **CLI Interface**: Simple commands for management and execution
- **Observability**: Structured logging and metrics

## Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

```bash
# Ingest an OpenAPI specification from URL
api-agent ingest --url http://api.example.com/v3/api-docs --env staging

# Ingest and save the spec locally for future reference
api-agent ingest --url http://api.example.com/v3/api-docs --save-as ./specs/example-api.json

# Ingest from local file
api-agent ingest --file ./specs/openapi.json --env production

# List available tools
api-agent list-tools

# Call a specific tool
api-agent call --tool create_user --data '{"name":"João","email":"joao@example.com"}'

# Run automated tests
api-agent run-tests --tool create_user --output reports/create_user.json
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenAPI       │    │    MCP Adapter   │    │   LLM Agent     │
│   Specification │────▶│   (Discovery &   │◀───│   (Tool User)   │
│                 │    │    Invocation)   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│ Swagger Parser  │    │  HTTP Executor   │
│                 │    │  (Auth, Retry,   │
│                 │    │   Validation)    │
└─────────────────┘    └──────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│ Tool Descriptor │    │ Test Generator   │
│   Repository    │    │   & Runner       │
└─────────────────┘    └──────────────────┘
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd agent-api-tester

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

### Running with Docker

```bash
# Build image
docker build -t api-agent .

# Run container
docker run -p 8000:8000 api-agent
```

## Configuration

Environment variables:
- `API_AGENT_LOG_LEVEL`: Logging level (default: INFO)
- `API_AGENT_BASE_URL`: Default base URL for API calls
- `API_AGENT_TIMEOUT`: Default timeout in seconds (default: 30)
- `API_AGENT_MAX_RETRIES`: Maximum retry attempts (default: 3)

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write tests for new features (80%+ coverage required)
4. Update documentation for API changes

## License

MIT License - see LICENSE file for details.
