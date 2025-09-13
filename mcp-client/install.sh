#!/bin/bash

# Instalação e configuração do MCP Client
# Este script instala as dependências e configura o ambiente

set -e

echo "🚀 Instalando MCP Client..."

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    exit 1
fi

# Verificar versão do Python
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📍 Python version: $python_version"

# Entrar no diretório do projeto
cd "$(dirname "$0")"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔌 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Instalar o pacote em modo desenvolvimento
echo "⚙️  Instalando MCP Client em modo desenvolvimento..."
pip install -e .

# Verificar instalação
echo "✅ Verificando instalação..."
if command -v mcp-client &> /dev/null; then
    echo "✅ MCP Client instalado com sucesso!"
    echo "📋 Versão:"
    mcp-client --help | head -n 2
else
    echo "❌ Falha na instalação do MCP Client"
    exit 1
fi

# Verificar arquivo de configuração
if [ ! -f "config.json" ]; then
    echo "📝 Criando arquivo de configuração padrão..."
    cp examples/config.json config.json
    echo "📁 Arquivo de configuração criado: config.json"
fi

echo ""
echo "🎉 Instalação concluída!"
echo ""
echo "📚 Próximos passos:"
echo "1. Editar configuração: nano config.json"
echo "2. Testar conexões: mcp-client servers test"
echo "3. Listar tools: mcp-client tools list"
echo "4. Executar demonstração: python demo.py"
echo ""
echo "💡 Comandos úteis:"
echo "- mcp-client --help           # Ajuda geral"
echo "- mcp-client status           # Status do cliente"
echo "- mcp-client servers list     # Listar servidores"
echo "- mcp-client tools list       # Listar tools"
echo "- python demo.py              # Executar demonstração"
echo ""
echo "🔧 Para desenvolvimento:"
echo "- source venv/bin/activate    # Ativar ambiente"
echo "- pytest                      # Executar testes"
echo "- black src/ tests/           # Formatar código"
echo ""
