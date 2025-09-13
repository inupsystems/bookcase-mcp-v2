#!/bin/bash

echo "🐳 Instalando Docker MCP Server..."

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+ primeiro."
    exit 1
fi

# Verificar se Docker está rodando
if ! docker ps &> /dev/null; then
    echo "❌ Docker não está rodando ou não está acessível."
    echo "   Por favor, inicie o Docker e verifique as permissões."
    exit 1
fi

# Criar ambiente virtual
echo "🐍 Criando ambiente virtual Python..."
python3 -m venv venv

# Instalar dependências
echo "📦 Instalando dependências Python..."
source venv/bin/activate && pip install -r requirements.txt

# Tornar o script executável
chmod +x main.py

echo "✅ Instalação concluída!"
echo ""
echo "🚀 Para testar o servidor, execute:"
echo "   source venv/bin/activate && python3 main.py"
echo ""
echo "📖 Para configurar no Claude Desktop, veja o README.md"
