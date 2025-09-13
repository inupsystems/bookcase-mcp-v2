#!/usr/bin/env python3

import asyncio
from pymongo import MongoClient

# Configuração do MongoDB
MONGO_URI = "mongodb://admin:admin123@localhost:27018"
DATABASE_NAME = "dev_memory_db"

async def init_database():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    print("Preparando banco de dados (sem inserção de dados)...")

    try:
        existing_collections = set(db.list_collection_names())

        required_collections = [
            "historico",           # Histórico de desenvolvimento
            "rules",              # Regras de desenvolvimento
            "patterns",           # Padrões de desenvolvimento
            "project_context",    # Contexto específico de projetos
            "protocols",          # Protocolos e processos
            "backups"            # Backups das coleções
        ]

        for collection_name in required_collections:
            if collection_name not in existing_collections:
                try:
                    db.create_collection(collection_name)
                    print(f"Coleção criada: {collection_name}")
                    # Adiciona índice de texto para project_context
                    if collection_name == "project_context":
                        db[collection_name].create_index(
                            [("context_content", "text")],
                            name="context_content_text_index",
                            weights={"context_content": 100},
                            default_language="portuguese"
                        )
                        print("Índice de texto criado para 'context_content' em 'project_context'.")
                except Exception as create_error:
                    print(f"Falha ao criar coleção '{collection_name}': {create_error}")
            else:
                print(f"Coleção já existe: {collection_name}")
                # Garante que o índice de texto existe mesmo se a coleção já existir
                if collection_name == "project_context":
                    try:
                        db[collection_name].create_index(
                            [("context_content", "text")],
                            name="context_content_text_index",
                            weights={"context_content": 100},
                            default_language="portuguese"
                        )
                        print("Índice de texto criado para 'context_content' em 'project_context'.")
                    except Exception as idx_error:
                        print(f"Falha ao criar índice de texto em 'project_context': {idx_error}")

        print("Preparação concluída.")

    except Exception as e:
        print(f"Erro ao preparar banco: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_database())
