#!/bin/bash

echo "🐳 Iniciando Docker MCP Server..."

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Execute ./install.sh primeiro."
    exit 1
fi

# Verificar se Docker está rodando
if ! docker ps &> /dev/null; then
    echo "❌ Docker não está rodando ou não está acessível."
    echo "   Por favor, inicie o Docker e verifique as permissões."
    exit 1
fi

# Ativar ambiente virtual e executar servidor
echo "🚀 Executando servidor MCP..."
source venv/bin/activate && python main.py

