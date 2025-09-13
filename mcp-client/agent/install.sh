#!/bin/bash

# Agent System Installation Script
# Instala dependências para o sistema de agent com DeepSeek + MCP

echo "🚀 Instalando Agent System..."

# Check if we're in the right directory
if [ ! -f "deepseek_mcp_agent.py" ]; then
    echo "❌ Execute este script do diretório agent/"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "📋 Python version: $python_version"

if [ "$(python3 -c "import sys; print(int(sys.version_info[0] >= 3 and sys.version_info[1] >= 8))")" -eq 0 ]; then
    echo "❌ Python 3.8+ required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Upgrade pip
echo "📦 Atualizando pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Instalando dependências do agent..."
pip install -r requirements.txt

# Install parent MCP client in development mode
echo "📦 Instalando MCP client..."
cd ..
pip install -e .
cd agent

echo "✅ Instalação concluída!"
echo ""
echo "Para usar o Agent System:"
echo "1. source venv/bin/activate"
echo "2. python gradio_interface.py"
echo ""
echo "A interface estará disponível em: http://localhost:7862"
