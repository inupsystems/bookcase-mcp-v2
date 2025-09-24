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
            "documentacao",      # Documentação de desenvolvimento
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
                    
                    # Adiciona índices para documentacao
                    if collection_name == "documentacao":
                        # 1. Índice de Texto para buscas por palavras-chave
                        db[collection_name].create_index(
                            [("chunk_content", "text")],
                            name="chunk_content_text_index",
                            weights={"chunk_content": 100},
                            default_language="portuguese"
                        )
                        print("Índice de texto criado para 'chunk_content' em 'documentacao'.")
                        
                        # 1.1. Índice de Texto para chunk_content, doc_title e tags
                        db[collection_name].create_index(
                            [("chunk_content", "text"), ("doc_title", "text"), ("tags", 1)],
                            name="chunk_content_doc_title_tags_text_index"
                        )
                        print("Índice de texto criado para 'chunk_content', 'doc_title' e 'tags' em 'documentacao'.")

                        # 2. Índice de Vetor para busca por similaridade semântica
                        try:
                            db[collection_name].create_index(
                                [("chunk_embedding", "vector")],
                                name="chunk_embedding_vector_index",
                                vectorOptions={"dimensions": 1536, "similarity": "cosine"}
                            )
                            print("Índice de vetor criado para 'chunk_embedding' em 'documentacao'.")
                            # 2.1. Índice de Vetor para chunk_embedding com 384 dimensões
                            db[collection_name].create_index(
                                [("chunk_embedding", "vector")],
                                name="chunk_embedding_vector_index_384",
                                vectorOptions={"dimensions": 384, "similarity": "cosine"}
                            )
                            print("Índice de vetor (384) criado para 'chunk_embedding' em 'documentacao'.")
                        except Exception as vector_error:
                            print(f"Falha ao criar índice de vetor em 'documentacao': {vector_error}. Verifique se está usando MongoDB 7.0 ou superior.")
                        
                        # 3. Índice Composto para otimizar busca por software e categoria
                        db[collection_name].create_index(
                            [("software.id", 1), ("category", 1)],
                            name="software_category_index"
                        )
                        print("Índice composto criado para 'software.id' e 'category' em 'documentacao'.")

                        # 3.1. Índice Composto para software.id e doc_slug
                        db[collection_name].create_index(
                            [("software.id", 1), ("doc_slug", 1)],
                            name="software_docslug_index"
                        )
                        print("Índice composto criado para 'software.id' e 'doc_slug' em 'documentacao'.")
                    
                    # Adiciona índice de texto para project_context
                    elif collection_name == "project_context":
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
                
                # Garante que os índices existam mesmo se a coleção já existir
                if collection_name == "documentacao":
                    try:
                        # 1. Índice de Texto para buscas por palavras-chave
                        db[collection_name].create_index(
                            [("chunk_content", "text")],
                            name="chunk_content_text_index",
                            weights={"chunk_content": 100},
                            default_language="portuguese"
                        )
                        print("Índice de texto criado para 'chunk_content' em 'documentacao'.")
                        # 1.1. Índice de Texto para chunk_content, doc_title e tags
                        db[collection_name].create_index(
                            [("chunk_content", "text"), ("doc_title", "text"), ("tags", 1)],
                            name="chunk_content_doc_title_tags_text_index"
                        )
                        print("Índice de texto criado para 'chunk_content', 'doc_title' e 'tags' em 'documentacao'.")
                    except Exception as idx_error:
                        print(f"Falha ao criar índice de texto em 'documentacao': {idx_error}")
                    
                    try:
                        # 2. Índice de Vetor para busca por similaridade semântica
                        db[collection_name].create_index(
                            [("chunk_embedding", "vector")],
                            name="chunk_embedding_vector_index",
                            vectorOptions={"dimensions": 1536, "similarity": "cosine"}
                        )
                        print("Índice de vetor criado para 'chunk_embedding' em 'documentacao'.")
                        # 2.1. Índice de Vetor para chunk_embedding com 384 dimensões
                        db[collection_name].create_index(
                            [("chunk_embedding", "vector")],
                            name="chunk_embedding_vector_index_384",
                            vectorOptions={"dimensions": 384, "similarity": "cosine"}
                        )
                        print("Índice de vetor (384) criado para 'chunk_embedding' em 'documentacao'.")
                    except Exception as vector_error:
                        print(f"Falha ao criar índice de vetor em 'documentacao': {vector_error}. Verifique se está usando MongoDB 7.0 ou superior.")
                    
                    try:
                        # 3. Índice Composto para otimizar busca por software e categoria
                        db[collection_name].create_index(
                            [("software.id", 1), ("category", 1)],
                            name="software_category_index"
                        )
                        print("Índice composto criado para 'software.id' e 'category' em 'documentacao'.")
                        # 3.1. Índice Composto para software.id e doc_slug
                        db[collection_name].create_index(
                            [("software.id", 1), ("doc_slug", 1)],
                            name="software_docslug_index"
                        )
                        print("Índice composto criado para 'software.id' e 'doc_slug' em 'documentacao'.")
                    except Exception as compound_error:
                        print(f"Falha ao criar índice composto em 'documentacao': {compound_error}")
                
                # Garante que o índice de texto existe para project_context
                elif collection_name == "project_context":
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
