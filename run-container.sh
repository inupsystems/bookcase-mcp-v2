#!/bin/bash

set -e

ROOT_DIR="$(dirname "$0")"
MONGO_DEV_DIR="$(realpath "$ROOT_DIR/mongo-dev-memory-mcp")"

# 1. Sobe os containers

echo "🛳️ Subindo containers com docker-compose..."
docker compose up -d --build --force-recreate --remove-orphans


# 2. Executa o install do mongo-dev-memory-mcp

echo "🔧 Instalando dependências do mongo-dev-memory-mcp..."
(cd "$MONGO_DEV_DIR" && bash ./install.sh)

echo "🚀 Executando init_database.py..."
source "$MONGO_DEV_DIR/venv/bin/activate"
python3 "$MONGO_DEV_DIR/init_database.py"

echo "🏁 Ambiente pronto!"
