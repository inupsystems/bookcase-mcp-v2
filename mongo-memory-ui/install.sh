#!/bin/bash

echo "🐍 Instalando Mongo Memory UI..."

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

# Tornar o script principal executável
chmod +x main.py

echo "✅ Instalação concluída!"
echo ""
echo "🚀 Para iniciar a interface, execute:"
echo "   source venv/bin/activate && python3 main.py"
echo ""
echo "📖 Veja instruções adicionais no README.md"
