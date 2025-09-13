"""Test configuration and utilities."""

import asyncio
import logging
from pathlib import Path

import pytest

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)

# Test configuration
TEST_CONFIG_PATH = Path(__file__).parent / "test_config.json"


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config_data():
    """Sample configuration data for testing."""
    return {
        "servers": {
            "memory": {
                "command": "echo",
                "args": ["memory_server"],
                "env": {"MEMORY_FILE": "test.txt"},
                "type": "stdio",
                "timeout": 5000
            },
            "http_server": {
                "command": "python",
                "args": ["-m", "http.server"],
                "type": "http",
                "host": "localhost",
                "port": 8000,
                "timeout": 10000
            }
        },
        "default_timeout": 15000,
        "retry_attempts": 2,
        "tool_cache_ttl": 60
    }
