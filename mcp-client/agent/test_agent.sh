#!/bin/bash

# Quick test script for Agent System
# Tests basic functionality without full UI

echo "🧪 Testando Agent System..."

# Check if we're in the right directory
if [ ! -f "deepseek_mcp_agent.py" ]; then
    echo "❌ Execute este script do diretório agent/"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "⚠️  Ambiente virtual não encontrado, usando Python global"
fi

# Test basic imports
echo "📦 Testando imports..."

python3 -c "
try:
    import sys
    import os
    sys.path.insert(0, '../src')
    
    # Test basic imports
    print('✅ Imports básicos OK')
    
    # Test OpenAI import
    try:
        import openai
        print('✅ OpenAI SDK OK')
    except ImportError as e:
        print(f'❌ OpenAI SDK: {e}')
    
    # Test Gradio import
    try:
        import gradio
        print('✅ Gradio OK')
    except ImportError as e:
        print(f'❌ Gradio: {e}')
    
    # Test MCP client import (conditional)
    try:
        from mcp_client import MCPClient, MCPConfig
        print('✅ MCP Client OK')
    except ImportError as e:
        print(f'⚠️  MCP Client: {e} (pode ser normal se não instalado)')
    
    print('✅ Teste de imports concluído')
    
except Exception as e:
    print(f'❌ Erro geral: {e}')
"

echo ""
echo "🔍 Verificando arquivos criados..."
for file in "deepseek_mcp_agent.py" "gradio_interface.py" "requirements.txt" "README.md"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file não encontrado"
    fi
done

echo ""
echo "📋 Próximos passos:"
echo "1. Complete a instalação: ./install.sh"
echo "2. Configure API key do DeepSeek"
echo "3. Execute: python gradio_interface.py"
echo "4. Acesse: http://localhost:7862"
