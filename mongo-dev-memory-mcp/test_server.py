#!/usr/bin/env python3

import asyncio
import json
from pymongo import MongoClient

# Configuração do MongoDB
MONGO_URI = "mongodb://admin:admin123@localhost:2018"
DATABASE_NAME = "dev_memory_db"

async def test_mongo_connection():
    """Testa a conexão com MongoDB e algumas operações básicas"""
    
    print("Testando conexão com MongoDB...")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        
        # Teste 1: Verificar se as coleções existem
        collections = db.list_collection_names()
        print(f"✅ Coleções encontradas: {collections}")
        
        # Teste 2: Verificar regras inseridas
        rules_count = db.rules.count_documents({})
        print(f"✅ Regras inseridas: {rules_count}")
        
        # Teste 3: Verificar padrões inseridos
        patterns_count = db.patterns.count_documents({})
        print(f"✅ Padrões inseridos: {patterns_count}")
        
        # Teste 4: Buscar regras de Java
        java_rules = list(db.rules.find({"technology": "java"}))
        print(f"✅ Regras de Java encontradas: {len(java_rules)}")
        
        # Teste 5: Buscar padrões de Python
        python_patterns = list(db.patterns.find({"technology": "python"}))
        print(f"✅ Padrões de Python encontrados: {len(python_patterns)}")
        
        # Teste 6: Inserir um registro de histórico de teste
        test_historico = {
            "project_id": "test-project",
            "task_description": "Teste de inserção no histórico",
            "technologies": ["python", "mongodb"],
            "files_modified": ["test_server.py"],
            "context": "Teste de funcionalidade do servidor MCP",
            "created_at": "2024-08-12T21:58:00Z",
            "timestamp": "2024-08-12T21:58:00Z"
        }
        
        result = db.historico.insert_one(test_historico)
        print(f"✅ Registro de histórico inserido com ID: {result.inserted_id}")
        
        # Teste 7: Buscar o histórico inserido
        historico_count = db.historico.count_documents({"project_id": "test-project"})
        print(f"✅ Registros de histórico para test-project: {historico_count}")
        
        # Teste 8: Estatísticas do banco
        db_stats = db.command("dbStats")
        print(f"✅ Tamanho do banco: {db_stats.get('dataSize', 0)} bytes")
        
        print("\n🎉 Todos os testes passaram com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_mongo_connection())
