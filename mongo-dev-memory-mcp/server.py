#!/usr/bin/env python3

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import sys
import os

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do MongoDB - Conexão com permissões root
MONGO_URI = "mongodb://admin:admin123@localhost:27018"
DATABASE_NAME = "dev_memory_db"

class MongoDevMemoryServer:
    def __init__(self):
        self.client = None
        self.db = None
        self.server = Server("mongo-dev-memory-mcp")
        self._setup_tools()
    
    def _setup_tools(self):
        """Configura todas as ferramentas disponíveis no servidor MCP"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                # Ferramentas de conexão e administração
                Tool(
                    name="mongo_connect",
                    description="Conecta ao MongoDB com permissões administrativas e inicializa o banco de dados",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="mongo_create_collection",
                    description="Cria uma nova coleção no MongoDB",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection_name": {
                                "type": "string",
                                "description": "Nome da coleção a ser criada"
                            }
                        },
                        "required": ["collection_name"]
                    }
                ),
                Tool(
                    name="mongo_drop_collection",
                    description="Remove uma coleção do MongoDB",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection_name": {
                                "type": "string",
                                "description": "Nome da coleção a ser removida"
                            }
                        },
                        "required": ["collection_name"]
                    }
                ),
                Tool(
                    name="mongo_list_collections",
                    description="Lista todas as coleções do banco de dados",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                
                # Ferramentas para histórico de desenvolvimento
                Tool(
                    name="mongo_insert_historico",
                    description="Insere um registro no histórico de desenvolvimento do projeto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID único do projeto"
                            },
                            "task_description": {
                                "type": "string",
                                "description": "Descrição detalhada da tarefa realizada"
                            },
                            "technologies": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tecnologias utilizadas na tarefa"
                            },
                            "files_modified": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de arquivos modificados"
                            },
                            "context": {
                                "type": "string",
                                "description": "Contexto adicional da tarefa"
                            },
                            "status": {
                                "type": "string",
                                "description": "Status da tarefa (completed, in_progress, failed)",
                                "default": "completed"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Duração da tarefa em minutos"
                            }
                        },
                        "required": ["project_id", "task_description"]
                    }
                ),
                Tool(
                    name="mongo_get_historico",
                    description="Obtém o histórico de desenvolvimento de um projeto específico",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID do projeto"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de registros",
                                "default": 50
                            },
                            "status": {
                                "type": "string",
                                "description": "Filtrar por status específico"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="mongo_get_all_projects_history",
                    description="Obtém histórico de todos os projetos",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de registros por projeto",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                ),
                
                # Ferramentas para regras de desenvolvimento
                Tool(
                    name="mongo_insert_rule",
                    description="Insere um documento de regras de desenvolvimento completo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "_id": {
                                "type": "string",
                                "description": "ID único do documento (ex: nestJs-rule-1)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Título do documento de regras"
                            },
                            "description": {
                                "type": "string",
                                "description": "Descrição geral do documento"
                            },
                            "category": {
                                "type": "string",
                                "description": "Categoria principal (ex: Arquitetura, Desenvolvimento, etc.)"
                            },
                            "scope": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Escopo de aplicação (domain, application, infrastructure, presentation)"
                            },
                            "rules": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "details": {"type": "string"}
                                    }
                                },
                                "description": "Lista de regras específicas"
                            },
                            "examples": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "language": {"type": "string"},
                                        "code": {"type": "string"},
                                        "description": {"type": "string"}
                                    }
                                },
                                "description": "Exemplos de código"
                            },
                            "related_documents": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Documentos relacionados"
                            },
                            "createdBy": {
                                "type": "string",
                                "description": "Criador do documento"
                            },
                            "version": {
                                "type": "string",
                                "description": "Versão do documento",
                                "default": "1.0.0"
                            }
                        },
                        "required": ["_id", "title", "description", "category", "rules"]
                    }
                ),
                Tool(
                    name="mongo_get_rules",
                    description="Obtém documentos de regras por ID específico ou filtros",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "_id": {
                                "type": "string",
                                "description": "ID específico do documento (opcional)"
                            },
                            "category": {
                                "type": "string",
                                "description": "Categoria específica (opcional)"
                            },
                            "title_contains": {
                                "type": "string",
                                "description": "Buscar por título que contenha o texto (opcional)"
                            },
                            "scope": {
                                "type": "string",
                                "description": "Filtrar por escopo específico (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="mongo_update_rule",
                    description="Atualiza um documento de regras existente",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "_id": {
                                "type": "string",
                                "description": "ID do documento a ser atualizado"
                            },
                            "title": {
                                "type": "string",
                                "description": "Novo título (opcional)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Nova descrição (opcional)"
                            },
                            "category": {
                                "type": "string",
                                "description": "Nova categoria (opcional)"
                            },
                            "scope": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Novo escopo (opcional)"
                            },
                            "rules": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "details": {"type": "string"}
                                    }
                                },
                                "description": "Nova lista de regras (opcional)"
                            },
                            "examples": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "language": {"type": "string"},
                                        "code": {"type": "string"},
                                        "description": {"type": "string"}
                                    }
                                },
                                "description": "Novos exemplos (opcional)"
                            },
                            "related_documents": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Novos documentos relacionados (opcional)"
                            },
                            "version": {
                                "type": "string",
                                "description": "Nova versão (opcional)"
                            }
                        },
                        "required": ["_id"]
                    }
                ),
                
                # Ferramentas para padrões de desenvolvimento
                Tool(
                    name="mongo_insert_pattern",
                    description="Insere um padrão de desenvolvimento para uma tecnologia",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "technology": {
                                "type": "string",
                                "description": "Tecnologia"
                            },
                            "pattern_name": {
                                "type": "string",
                                "description": "Nome do padrão"
                            },
                            "pattern_description": {
                                "type": "string",
                                "description": "Descrição do padrão"
                            },
                            "pattern_example": {
                                "type": "string",
                                "description": "Exemplo de implementação do padrão"
                            },
                            "category": {
                                "type": "string",
                                "description": "Categoria do padrão (architectural, design, code, etc.)",
                                "default": "general"
                            },
                            "use_cases": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Casos de uso onde o padrão se aplica"
                            },
                            "benefits": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Benefícios do padrão"
                            },
                            "complexity": {
                                "type": "string",
                                "description": "Nível de complexidade (low, medium, high)"
                            }
                        },
                        "required": ["technology", "pattern_name", "pattern_description"]
                    }
                ),
                Tool(
                    name="mongo_get_patterns",
                    description="Obtém padrões de desenvolvimento por tecnologia",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "technology": {
                                "type": "string",
                                "description": "Tecnologia específica"
                            },
                            "category": {
                                "type": "string",
                                "description": "Categoria específica (opcional)"
                            },
                            "complexity": {
                                "type": "string",
                                "description": "Nível de complexidade específico"
                            }
                        },
                        "required": ["technology"]
                    }
                ),
                
                # Ferramentas para contexto de projetos
                Tool(
                    name="mongo_insert_project_context",
                    description="Insere contexto específico de um projeto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID do projeto"
                            },
                            "context_type": {
                                "type": "string",
                                "description": "Tipo de contexto (architecture, requirements, constraints, etc.)"
                            },
                            "context_content": {
                                "type": "string",
                                "description": "Conteúdo do contexto"
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Prioridade do contexto (1-10)",
                                "default": 5
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags para categorização"
                            }
                        },
                        "required": ["project_id", "context_type", "context_content"]
                    }
                ),
                Tool(
                    name="mongo_get_project_context",
                    description="Obtém contexto específico de um projeto",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID do projeto"
                            },
                            "context_type": {
                                "type": "string",
                                "description": "Tipo de contexto específico (opcional)"
                            },
                            "priority_min": {
                                "type": "integer",
                                "description": "Prioridade mínima"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="mongo_search_project_context",
                    description="Busca contexto de projeto usando texto no campo context_content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Termo de busca textual para context_content"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "ID do projeto (opcional)"
                            },
                            "context_type": {
                                "type": "string",
                                "description": "Tipo de contexto (opcional)"
                            },
                            "priority_min": {
                                "type": "integer",
                                "description": "Prioridade mínima (opcional)"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags para filtrar (opcional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de resultados",
                                "default": 20
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                
                # Ferramentas para protocolos e processos
                Tool(
                    name="mongo_insert_protocol",
                    description="Insere um protocolo de desenvolvimento",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "protocol_name": {
                                "type": "string",
                                "description": "Nome do protocolo"
                            },
                            "protocol_description": {
                                "type": "string",
                                "description": "Descrição do protocolo"
                            },
                            "steps": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Passos do protocolo"
                            },
                            "applies_to": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tecnologias/contextos onde se aplica"
                            },
                            "category": {
                                "type": "string",
                                "description": "Categoria do protocolo (deployment, testing, code-review, etc.)"
                            }
                        },
                        "required": ["protocol_name", "protocol_description", "steps"]
                    }
                ),
                Tool(
                    name="mongo_get_protocols",
                    description="Obtém protocolos de desenvolvimento",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Categoria específica"
                            },
                            "applies_to": {
                                "type": "string",
                                "description": "Tecnologia específica"
                            }
                        },
                        "required": []
                    }
                ),
                
                # Ferramentas de busca e análise
                Tool(
                    name="mongo_search_historico",
                    description="Busca no histórico por termos específicos",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Termo de busca"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "ID do projeto (opcional)"
                            },
                            "technology": {
                                "type": "string",
                                "description": "Tecnologia específica (opcional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de resultados",
                                "default": 20
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                Tool(
                    name="mongo_search_global",
                    description="Busca global em todas as coleções",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Termo de busca"
                            },
                            "collections": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Coleções específicas para buscar"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de resultados por coleção",
                                "default": 10
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                
                # Ferramentas de estatísticas e análise
                Tool(
                    name="mongo_get_database_stats",
                    description="Obtém estatísticas completas do banco de dados",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="mongo_get_project_stats",
                    description="Obtém estatísticas de um projeto específico",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID do projeto"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="mongo_get_technology_usage",
                    description="Obtém estatísticas de uso de tecnologias",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                
                # Ferramentas administrativas
                Tool(
                    name="mongo_backup_collection",
                    description="Cria backup de uma coleção",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection_name": {
                                "type": "string",
                                "description": "Nome da coleção para backup"
                            }
                        },
                        "required": ["collection_name"]
                    }
                ),
                Tool(
                    name="mongo_restore_collection",
                    description="Restaura uma coleção do backup",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection_name": {
                                "type": "string",
                                "description": "Nome da coleção para restaurar"
                            },
                            "backup_data": {
                                "type": "string",
                                "description": "Dados do backup em JSON"
                            }
                        },
                        "required": ["collection_name", "backup_data"]
                    }
                )
            ]
    
    async def connect_mongo(self):
        """Conecta ao MongoDB com permissões administrativas e inicializa o banco"""
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DATABASE_NAME]
            
            # Testar conexão
            self.client.admin.command('ping')
            
            # Criar coleções principais se não existirem
            collections = [
                'historico',           # Histórico de desenvolvimento
                'rules',              # Regras de desenvolvimento
                'patterns',           # Padrões de desenvolvimento
                'project_context',    # Contexto específico de projetos
                'protocols',          # Protocolos e processos
                'backups'            # Backups das coleções
            ]
            
            existing_collections = list(self.db.list_collection_names())
            for collection_name in collections:
                if collection_name not in existing_collections:
                    self.db.create_collection(collection_name)
            
            # Criar índices otimizados para performance
            await self._create_indexes()
            
            return {
                "success": True, 
                "message": "Conectado ao MongoDB com permissões administrativas",
                "database": DATABASE_NAME,
                "collections": collections
            }
        except PyMongoError as e:
            logger.error(f"Erro ao conectar MongoDB: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_indexes(self):
        """Cria índices otimizados para todas as coleções"""
        try:
            # Índices para histórico (com verificação de existência)
            try:
                self.db.historico.create_index([("project_id", 1), ("created_at", -1)])
            except PyMongoError:
                pass
            
            try:
                self.db.historico.create_index([("technologies", 1)])
            except PyMongoError:
                pass
                
            try:
                self.db.historico.create_index([("status", 1)])
            except PyMongoError:
                pass
                
            try:
                # Verificar se já existe índice de texto
                existing_indexes = list(self.db.historico.list_indexes())
                text_index_exists = any(idx.get('key', {}).get('_fts') == 'text' for idx in existing_indexes)
                if not text_index_exists:
                    self.db.historico.create_index([("task_description", "text"), ("context", "text")])
            except PyMongoError:
                pass
            
            # Índices para regras
            try:
                self.db.rules.create_index([("technology", 1), ("category", 1)])
                self.db.rules.create_index([("priority", -1)])
                # Verificar índice de texto para rules
                existing_indexes = list(self.db.rules.list_indexes())
                text_index_exists = any(idx.get('key', {}).get('_fts') == 'text' for idx in existing_indexes)
                if not text_index_exists:
                    self.db.rules.create_index([("rule_name", "text"), ("rule_content", "text")])
            except PyMongoError:
                pass
            
            # Índices para padrões
            try:
                self.db.patterns.create_index([("technology", 1), ("category", 1)])
                self.db.patterns.create_index([("complexity", 1)])
                # Verificar índice de texto para patterns
                existing_indexes = list(self.db.patterns.list_indexes())
                text_index_exists = any(idx.get('key', {}).get('_fts') == 'text' for idx in existing_indexes)
                if not text_index_exists:
                    self.db.patterns.create_index([("pattern_name", "text"), ("pattern_description", "text")])
            except PyMongoError:
                pass
            
            # Índices para contexto de projetos
            try:
                self.db.project_context.create_index([("project_id", 1), ("context_type", 1)])
                self.db.project_context.create_index([("priority", -1)])
                self.db.project_context.create_index([("tags", 1)])
            except PyMongoError:
                pass
            
            # Índices para protocolos
            try:
                self.db.protocols.create_index([("category", 1)])
                self.db.protocols.create_index([("applies_to", 1)])
                # Verificar índice de texto para protocols
                existing_indexes = list(self.db.protocols.list_indexes())
                text_index_exists = any(idx.get('key', {}).get('_fts') == 'text' for idx in existing_indexes)
                if not text_index_exists:
                    self.db.protocols.create_index([("protocol_name", "text"), ("protocol_description", "text")])
            except PyMongoError:
                pass
            
            logger.info("Índices verificados/criados com sucesso")
        except PyMongoError as e:
            logger.warning(f"Alguns índices podem não ter sido criados: {e}")
    
    # Métodos para coleções
    async def create_collection(self, collection_name: str):
        """Cria uma nova coleção"""
        try:
            existing_collections = list(self.db.list_collection_names())
            if collection_name not in existing_collections:
                self.db.create_collection(collection_name)
                return {"success": True, "message": f"Coleção '{collection_name}' criada com sucesso"}
            else:
                return {"success": True, "message": f"Coleção '{collection_name}' já existe"}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def drop_collection(self, collection_name: str):
        """Remove uma coleção"""
        try:
            existing_collections = list(self.db.list_collection_names())
            if collection_name in existing_collections:
                self.db[collection_name].drop()
                return {"success": True, "message": f"Coleção '{collection_name}' removida com sucesso"}
            else:
                return {"success": False, "message": f"Coleção '{collection_name}' não existe"}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def list_collections(self):
        """Lista todas as coleções"""
        try:
            collections = list(self.db.list_collection_names())
            return {"success": True, "collections": collections, "count": len(collections)}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos para histórico de desenvolvimento
    async def insert_historico(self, project_id: str, task_description: str, 
                             technologies: List[str] = None, files_modified: List[str] = None, 
                             context: str = None, status: str = "completed", 
                             duration_minutes: int = None):
        """Insere um registro no histórico de desenvolvimento"""
        try:
            document = {
                "project_id": project_id,
                "task_description": task_description,
                "technologies": technologies or [],
                "files_modified": files_modified or [],
                "context": context,
                "status": status,
                "duration_minutes": duration_minutes,
                "created_at": datetime.utcnow(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = self.db.historico.insert_one(document)
            return {
                "success": True,
                "message": "Registro inserido no histórico",
                "id": str(result.inserted_id),
                "project_id": project_id
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_historico(self, project_id: str, limit: int = 50, status: str = None):
        """Obtém o histórico de desenvolvimento de um projeto"""
        try:
            query = {"project_id": project_id}
            if status:
                query["status"] = status
            
            cursor = self.db.historico.find(query).sort("created_at", -1).limit(limit)
            
            historico = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                historico.append(doc)
            
            return {
                "success": True,
                "project_id": project_id,
                "historico": historico,
                "count": len(historico)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_all_projects_history(self, limit: int = 10):
        """Obtém histórico de todos os projetos"""
        try:
            pipeline = [
                {"$group": {"_id": "$project_id", "last_activity": {"$max": "$created_at"}}},
                {"$sort": {"last_activity": -1}}
            ]
            
            projects = list(self.db.historico.aggregate(pipeline))
            result = {}
            
            for project in projects:
                project_id = project["_id"]
                history = await self.get_historico(project_id, limit)
                if history["success"]:
                    result[project_id] = {
                        "last_activity": project["last_activity"],
                        "history": history["historico"]
                    }
            
            return {
                "success": True,
                "projects": result,
                "count": len(result)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos para regras de desenvolvimento
    async def insert_rule(self, _id: str, title: str, description: str, category: str, 
                         rules: List[dict], scope: List[str] = None, examples: List[dict] = None,
                         related_documents: List[str] = None, createdBy: str = None, 
                         version: str = "1.0.0"):
        """Insere um documento completo de regras de desenvolvimento"""
        try:
            document = {
                "_id": _id,
                "title": title,
                "description": description,
                "category": category,
                "scope": scope or [],
                "examples": examples or [],
                "rules": rules,
                "related_documents": related_documents or [],
                "createdBy": createdBy,
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "updatedAt": datetime.utcnow().isoformat() + "Z",
                "version": version
            }
            
            result = self.db.rules.insert_one(document)
            return {
                "success": True,
                "message": "Documento de regras inserido com sucesso",
                "id": _id
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_rules(self, _id: str = None, category: str = None, title_contains: str = None, scope: str = None):
        """Obtém documentos de regras por ID específico ou filtros"""
        try:
            if _id:
                # Buscar por ID específico
                doc = self.db.rules.find_one({"_id": _id})
                if doc:
                    return {
                        "success": True,
                        "rules": [doc],
                        "count": 1
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Documento com ID {_id} não encontrado"
                    }
            else:
                # Construir query baseada nos filtros
                query = {}
                if category:
                    query["category"] = {"$regex": category, "$options": "i"}
                if title_contains:
                    query["title"] = {"$regex": title_contains, "$options": "i"}
                if scope:
                    query["scope"] = {"$in": [scope]}
                
                cursor = self.db.rules.find(query).sort([("updatedAt", -1)])
                
                rules = []
                for doc in cursor:
                    rules.append(doc)
                
                return {
                    "success": True,
                    "rules": rules,
                    "count": len(rules)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_rule(self, _id: str, title: str = None, description: str = None, 
                         category: str = None, scope: List[str] = None, rules: List[dict] = None,
                         examples: List[dict] = None, related_documents: List[str] = None, 
                         version: str = None):
        """Atualiza um documento de regras existente"""
        try:
            update_fields = {"updatedAt": datetime.utcnow().isoformat() + "Z"}
            
            if title:
                update_fields["title"] = title
            if description:
                update_fields["description"] = description
            if category:
                update_fields["category"] = category
            if scope is not None:
                update_fields["scope"] = scope
            if rules is not None:
                update_fields["rules"] = rules
            if examples is not None:
                update_fields["examples"] = examples
            if related_documents is not None:
                update_fields["related_documents"] = related_documents
            if version:
                update_fields["version"] = version
            
            result = self.db.rules.update_one(
                {"_id": _id},
                {"$set": update_fields}
            )
            
            if result.matched_count > 0:
                return {"success": True, "message": "Documento de regras atualizado com sucesso"}
            else:
                return {"success": False, "message": "Documento não encontrado"}
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos para padrões de desenvolvimento
    async def insert_pattern(self, technology: str, pattern_name: str, pattern_description: str,
                           pattern_example: str = None, category: str = "general",
                           use_cases: List[str] = None, benefits: List[str] = None,
                           complexity: str = "medium"):
        """Insere um padrão de desenvolvimento"""
        try:
            document = {
                "technology": technology.lower(),
                "pattern_name": pattern_name,
                "pattern_description": pattern_description,
                "pattern_example": pattern_example,
                "category": category,
                "use_cases": use_cases or [],
                "benefits": benefits or [],
                "complexity": complexity,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.db.patterns.insert_one(document)
            return {
                "success": True,
                "message": "Padrão inserido com sucesso",
                "id": str(result.inserted_id)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_patterns(self, technology: str, category: str = None, complexity: str = None):
        """Obtém padrões de desenvolvimento por tecnologia"""
        try:
            query = {"technology": technology.lower()}
            if category:
                query["category"] = category
            if complexity:
                query["complexity"] = complexity
            
            cursor = self.db.patterns.find(query).sort("created_at", -1)
            
            patterns = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                patterns.append(doc)
            
            return {
                "success": True,
                "technology": technology,
                "patterns": patterns,
                "count": len(patterns)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos para contexto de projetos
    async def insert_project_context(self, project_id: str, context_type: str, 
                                   context_content: str, priority: int = 5,
                                   tags: List[str] = None):
        """Insere contexto específico de um projeto"""
        try:
            document = {
                "project_id": project_id,
                "context_type": context_type,
                "context_content": context_content,
                "priority": priority,
                "tags": tags or [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.db.project_context.insert_one(document)
            return {
                "success": True,
                "message": "Contexto do projeto inserido com sucesso",
                "id": str(result.inserted_id)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_project_context(self, project_id: str = None, context_type: str = None, priority: int = None, tags: list = None):
        """Obtém contexto específico de um projeto por project_id, tags, context_type ou priority"""
        try:
            query = {}
            if project_id:
                query["project_id"] = project_id
            if context_type:
                query["context_type"] = context_type
            if priority is not None:
                query["priority"] = priority
            if tags:
                query["tags"] = {"$in": tags}

            cursor = self.db.project_context.find(query).sort([("priority", -1), ("created_at", -1)])
            context = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                context.append(doc)
            return {
                "success": True,
                "query": query,
                "context": context,
                "count": len(context)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def search_project_context(self, search_term: str, project_id: str = None, context_type: str = None, priority_min: int = None, tags: list = None, limit: int = 20):
        """Busca contexto de projeto usando texto no campo context_content"""
        try:
            query = {"$text": {"$search": search_term}}
            if project_id:
                query["project_id"] = project_id
            if context_type:
                query["context_type"] = context_type
            if priority_min is not None:
                query["priority"] = {"$gte": priority_min}
            if tags:
                query["tags"] = {"$in": tags}

            cursor = self.db.project_context.find(
                query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"}), ("priority", -1), ("created_at", -1)]).limit(limit)

            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)
            return {
                "success": True,
                "search_term": search_term,
                "query": query,
                "results": results,
                "count": len(results)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos para protocolos
    async def insert_protocol(self, protocol_name: str, protocol_description: str,
                            steps: List[str], applies_to: List[str] = None,
                            category: str = "general"):
        """Insere um protocolo de desenvolvimento"""
        try:
            document = {
                "protocol_name": protocol_name,
                "protocol_description": protocol_description,
                "steps": steps,
                "applies_to": applies_to or [],
                "category": category,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.db.protocols.insert_one(document)
            return {
                "success": True,
                "message": "Protocolo inserido com sucesso",
                "id": str(result.inserted_id)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_protocols(self, category: str = None, applies_to: str = None):
        """Obtém protocolos de desenvolvimento"""
        try:
            query = {}
            if category:
                query["category"] = category
            if applies_to:
                query["applies_to"] = {"$in": [applies_to]}
            
            cursor = self.db.protocols.find(query).sort("created_at", -1)
            
            protocols = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                protocols.append(doc)
            
            return {
                "success": True,
                "protocols": protocols,
                "count": len(protocols)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos de busca
    async def search_historico(self, search_term: str, project_id: str = None, 
                             technology: str = None, limit: int = 20):
        """Busca no histórico por termos específicos"""
        try:
            query = {
                "$text": {"$search": search_term}
            }
            
            if project_id:
                query["project_id"] = project_id
            if technology:
                query["technologies"] = {"$in": [technology]}
            
            cursor = self.db.historico.find(
                query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return {
                "success": True,
                "search_term": search_term,
                "results": results,
                "count": len(results)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def search_global(self, search_term: str, collections: List[str] = None, limit: int = 10):
        """Busca global em todas as coleções"""
        try:
            search_collections = collections or ['historico', 'rules', 'patterns', 'project_context', 'protocols']
            results = {}
            
            existing_collections = list(self.db.list_collection_names())
            for collection_name in search_collections:
                if collection_name in existing_collections:
                    collection = self.db[collection_name]
                    
                    # Busca por texto
                    cursor = collection.find(
                        {"$text": {"$search": search_term}},
                        {"score": {"$meta": "textScore"}}
                    ).sort([("score", {"$meta": "textScore"})]).limit(limit)
                    
                    collection_results = []
                    for doc in cursor:
                        doc["_id"] = str(doc["_id"])
                        collection_results.append(doc)
                    
                    results[collection_name] = collection_results
            
            return {
                "success": True,
                "search_term": search_term,
                "results": results,
                "collections_searched": len(results)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos de estatísticas
    async def get_database_stats(self):
        """Obtém estatísticas completas do banco de dados"""
        try:
            stats = {}
            
            # Estatísticas das coleções
            collections = list(self.db.list_collection_names())
            for collection in collections:
                count = self.db[collection].count_documents({})
                stats[collection] = {
                    "count": count,
                    "size_bytes": self.db.command("collStats", collection).get("size", 0)
                }
            
            # Estatísticas gerais do banco
            db_stats = self.db.command("dbStats")
            stats["database"] = {
                "name": DATABASE_NAME,
                "collections": len(collections),
                "data_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0),
                "indexes": db_stats.get("indexes", 0)
            }
            
            return {
                "success": True,
                "stats": stats
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_project_stats(self, project_id: str):
        """Obtém estatísticas de um projeto específico"""
        try:
            stats = {}
            
            # Estatísticas do histórico
            total_tasks = self.db.historico.count_documents({"project_id": project_id})
            completed_tasks = self.db.historico.count_documents({
                "project_id": project_id, 
                "status": "completed"
            })
            
            # Tecnologias utilizadas
            pipeline = [
                {"$match": {"project_id": project_id}},
                {"$unwind": "$technologies"},
                {"$group": {"_id": "$technologies", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            technologies = list(self.db.historico.aggregate(pipeline))
            
            # Contextos do projeto
            context_count = self.db.project_context.count_documents({"project_id": project_id})
            
            stats = {
                "project_id": project_id,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "technologies_used": technologies,
                "context_entries": context_count
            }
            
            return {
                "success": True,
                "stats": stats
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def get_technology_usage(self):
        """Obtém estatísticas de uso de tecnologias"""
        try:
            pipeline = [
                {"$unwind": "$technologies"},
                {"$group": {
                    "_id": "$technologies", 
                    "count": {"$sum": 1},
                    "projects": {"$addToSet": "$project_id"}
                }},
                {"$addFields": {"project_count": {"$size": "$projects"}}},
                {"$sort": {"count": -1}}
            ]
            
            technology_stats = list(self.db.historico.aggregate(pipeline))
            
            return {
                "success": True,
                "technology_usage": technology_stats,
                "total_technologies": len(technology_stats)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    # Métodos administrativos
    async def backup_collection(self, collection_name: str):
        """Cria backup de uma coleção"""
        try:
            existing_collections = list(self.db.list_collection_names())
            if collection_name not in existing_collections:
                return {"success": False, "message": "Coleção não encontrada"}
            
            # Exportar todos os documentos
            documents = list(self.db[collection_name].find({}))
            
            # Converter ObjectId para string
            for doc in documents:
                doc["_id"] = str(doc["_id"])
            
            backup_doc = {
                "collection_name": collection_name,
                "backup_date": datetime.utcnow(),
                "document_count": len(documents),
                "data": documents
            }
            
            result = self.db.backups.insert_one(backup_doc)
            
            return {
                "success": True,
                "message": f"Backup da coleção '{collection_name}' criado com sucesso",
                "backup_id": str(result.inserted_id),
                "document_count": len(documents)
            }
        except PyMongoError as e:
            return {"success": False, "error": str(e)}
    
    async def restore_collection(self, collection_name: str, backup_data: str):
        """Restaura uma coleção do backup"""
        try:
            import json
            
            # Parse dos dados de backup
            backup_documents = json.loads(backup_data)
            
            # Limpar coleção existente
            self.db[collection_name].drop()
            
            # Restaurar documentos
            if backup_documents:
                self.db[collection_name].insert_many(backup_documents)
            
            return {
                "success": True,
                "message": f"Coleção '{collection_name}' restaurada com sucesso",
                "documents_restored": len(backup_documents)
            }
        except (PyMongoError, json.JSONDecodeError) as e:
            return {"success": False, "error": str(e)}

# Instância global do servidor
mongo_server = MongoDevMemoryServer()

@mongo_server.server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Manipula chamadas de ferramentas"""
    
    # Conectar ao MongoDB se ainda não estiver conectado
    if mongo_server.db is None:
        await mongo_server.connect_mongo()
    
    try:
        # Roteamento das ferramentas
        if name == "mongo_connect":
            result = await mongo_server.connect_mongo()
        elif name == "mongo_create_collection":
            result = await mongo_server.create_collection(arguments["collection_name"])
        elif name == "mongo_drop_collection":
            result = await mongo_server.drop_collection(arguments["collection_name"])
        elif name == "mongo_list_collections":
            result = await mongo_server.list_collections()
        
        # Histórico
        elif name == "mongo_insert_historico":
            result = await mongo_server.insert_historico(
                arguments["project_id"],
                arguments["task_description"],
                arguments.get("technologies"),
                arguments.get("files_modified"),
                arguments.get("context"),
                arguments.get("status", "completed"),
                arguments.get("duration_minutes")
            )
        elif name == "mongo_get_historico":
            result = await mongo_server.get_historico(
                arguments["project_id"],
                arguments.get("limit", 50),
                arguments.get("status")
            )
        elif name == "mongo_get_all_projects_history":
            result = await mongo_server.get_all_projects_history(
                arguments.get("limit", 10)
            )
        
        # Regras
        elif name == "mongo_insert_rule":
            result = await mongo_server.insert_rule(
                arguments["_id"],
                arguments["title"],
                arguments["description"],
                arguments["category"],
                arguments["rules"],
                arguments.get("scope"),
                arguments.get("examples"),
                arguments.get("related_documents"),
                arguments.get("createdBy"),
                arguments.get("version", "1.0.0")
            )
        elif name == "mongo_get_rules":
            result = await mongo_server.get_rules(
                arguments.get("_id"),
                arguments.get("category"),
                arguments.get("title_contains"),
                arguments.get("scope")
            )
        elif name == "mongo_update_rule":
            result = await mongo_server.update_rule(
                arguments["_id"],
                arguments.get("title"),
                arguments.get("description"),
                arguments.get("category"),
                arguments.get("scope"),
                arguments.get("rules"),
                arguments.get("examples"),
                arguments.get("related_documents"),
                arguments.get("version")
            )
        
        # Padrões
        elif name == "mongo_insert_pattern":
            result = await mongo_server.insert_pattern(
                arguments["technology"],
                arguments["pattern_name"],
                arguments["pattern_description"],
                arguments.get("pattern_example"),
                arguments.get("category", "general"),
                arguments.get("use_cases"),
                arguments.get("benefits"),
                arguments.get("complexity", "medium")
            )
        elif name == "mongo_get_patterns":
            result = await mongo_server.get_patterns(
                arguments["technology"],
                arguments.get("category"),
                arguments.get("complexity")
            )
        
        # Contexto de projetos
        elif name == "mongo_insert_project_context":
            result = await mongo_server.insert_project_context(
                arguments["project_id"],
                arguments["context_type"],
                arguments["context_content"],
                arguments.get("priority", 5),
                arguments.get("tags")
            )
        elif name == "mongo_get_project_context":
            result = await mongo_server.get_project_context(
                arguments["project_id"],
                arguments.get("context_type"),
                arguments.get("priority_min")
            )
        elif name == "mongo_search_project_context":
            result = await mongo_server.search_project_context(
                arguments["search_term"],
                arguments.get("project_id"),
                arguments.get("context_type"),
                arguments.get("priority_min"),
                arguments.get("tags"),
                arguments.get("limit", 20)
            )
        
        # Protocolos
        elif name == "mongo_insert_protocol":
            result = await mongo_server.insert_protocol(
                arguments["protocol_name"],
                arguments["protocol_description"],
                arguments["steps"],
                arguments.get("applies_to"),
                arguments.get("category", "general")
            )
        elif name == "mongo_get_protocols":
            result = await mongo_server.get_protocols(
                arguments.get("category"),
                arguments.get("applies_to")
            )
        
        # Busca
        elif name == "mongo_search_historico":
            result = await mongo_server.search_historico(
                arguments["search_term"],
                arguments.get("project_id"),
                arguments.get("technology"),
                arguments.get("limit", 20)
            )
        elif name == "mongo_search_global":
            result = await mongo_server.search_global(
                arguments["search_term"],
                arguments.get("collections"),
                arguments.get("limit", 10)
            )
        
        # Estatísticas
        elif name == "mongo_get_database_stats":
            result = await mongo_server.get_database_stats()
        elif name == "mongo_get_project_stats":
            result = await mongo_server.get_project_stats(arguments["project_id"])
        elif name == "mongo_get_technology_usage":
            result = await mongo_server.get_technology_usage()
        
        # Administrativo
        elif name == "mongo_backup_collection":
            result = await mongo_server.backup_collection(arguments["collection_name"])
        elif name == "mongo_restore_collection":
            result = await mongo_server.restore_collection(
                arguments["collection_name"],
                arguments["backup_data"]
            )
        
        else:
            result = {"success": False, "error": f"Ferramenta '{name}' não encontrada"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except Exception as e:
        logger.error(f"Erro ao executar ferramenta {name}: {e}")
        error_result = {"success": False, "error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """Função principal do servidor"""
    logger.info("Iniciando servidor MCP MongoDB Dev Memory...")
    
    # Conectar ao MongoDB na inicialização
    connection_result = await mongo_server.connect_mongo()
    if connection_result["success"]:
        logger.info(f"Conectado ao MongoDB: {connection_result['message']}")
    else:
        logger.error(f"Erro na conexão: {connection_result['error']}")
        sys.exit(1)
    
    # Executar o servidor
    async with stdio_server() as (read_stream, write_stream):
        await mongo_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mongo-dev-memory-mcp",
                server_version="2.0.0",
                capabilities=mongo_server.server.get_capabilities(
                    NotificationOptions(
                        prompts_changed=False,
                        resources_changed=False,
                        tools_changed=False,
                    ),
                    {},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal no servidor: {e}")
        sys.exit(1)