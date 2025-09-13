#!/usr/bin/env python3
"""
Ponto de entrada principal para o Docker MCP Server
"""

import sys
import os

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

