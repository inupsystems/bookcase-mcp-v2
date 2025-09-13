#!/bin/bash

set -e

ROOT_DIR="$(dirname "$0")"

echo "🛠️ Iniciando instalação de todos os módulos..."

MODULES=(
    "docker-mcp"
    "mongo-dev-memory-mcp"
    "mongo-memory-ui"
)

for MODULE in "${MODULES[@]}"; do
    INSTALL_SCRIPT="$ROOT_DIR/$MODULE/install.sh"
    if [ -f "$INSTALL_SCRIPT" ]; then
        echo "\n🔹 Instalando módulo: $MODULE"
        bash "$INSTALL_SCRIPT" || echo "❌ Falha na instalação de $MODULE"
    else
        echo "⚠️ Script de instalação não encontrado para $MODULE"
    fi
done

echo "\n✅ Instalação orquestrada concluída!"
