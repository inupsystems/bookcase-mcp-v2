#!/bin/bash

echo "🐍 Instalando Mongo Dev Memory MCP..."

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+ primeiro."
    exit 1
fi

# Criar ambiente virtual
echo "🐍 Criando ambiente virtual Python..."
python3 -m venv venv

# Instalar dependências
echo "📦 Instalando dependências Python..."
source venv/bin/activate && pip install -r requirements.txt

# Tornar scripts principais executáveis
chmod +x server.py
chmod +x init_database.py

echo "✅ Instalação concluída!"
echo ""
echo "🚀 Para iniciar o servidor, execute:"
echo "   source venv/bin/activate && python3 server.py"
echo ""
echo "📖 Veja instruções adicionais no README.md"
