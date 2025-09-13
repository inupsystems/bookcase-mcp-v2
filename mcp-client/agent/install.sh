#!/bin/bash

# Agent System Installation Script
# Instala dependências para o sistema de agent com DeepSeek + MCP

set -e # Exit immediately if a command exits with a non-zero status.

echo "🚀 Instalando Agent System..."

# Check if python3-venv is installed
if ! dpkg -s python3-venv >/dev/null 2>&1; then
    echo "❌ Pacote python3-venv não encontrado."
    echo "   Por favor, instale-o com: sudo apt-get install python3-venv"
    exit 1
fi

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

# Remove existing virtual environment to ensure a clean start
if [ -d "venv" ]; then
    echo "�️ Removendo ambiente virtual existente..."
    rm -rf venv
fi

# Create virtual environment
echo "�🔧 Criando ambiente virtual..."
python3 -m venv venv

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
(cd .. && pip install -e .)

echo "✅ Instalação concluída!"
echo ""
echo "Para usar o Agent System:"
echo "1. source venv/bin/activate"
echo "2. python gradio_interface.py"
echo ""
echo "A interface estará disponível em: http://localhost:7862"

echo "2. python gradio_interface.py"
echo ""
echo "A interface estará disponível em: http://localhost:7862"
