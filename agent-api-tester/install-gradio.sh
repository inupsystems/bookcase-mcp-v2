#!/bin/bash

echo "🤖 Instalando Agent API Tester - Interface Gradio..."

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+ primeiro."
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🐍 Criando ambiente virtual Python..."
    python3 -m venv venv
fi

# Ativar ambiente virtual e instalar dependências
echo "📦 Instalando dependências Python..."
source venv/bin/activate

# Instalar dependências do projeto principal
if [ -f "pyproject.toml" ]; then
    pip install -e .
fi

# Instalar dependências específicas do Gradio
if [ -f "requirements-gradio.txt" ]; then
    pip install -r requirements-gradio.txt
fi

echo "✅ Instalação concluída!"
echo ""
echo "🚀 Para iniciar a interface Gradio, execute:"
echo "   source venv/bin/activate && python gradio_interface.py"
echo ""
echo "🌐 A interface estará disponível em: http://localhost:7860"
echo ""
echo "📖 Veja mais detalhes no README-GRADIO.md"
