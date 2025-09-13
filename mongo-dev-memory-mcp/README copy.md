# MongoDB Dev Memory MCP Server

Um servidor MCP (Model Context Protocol) para gerenciar memória de desenvolvimento usando MongoDB. Este servidor permite que agentes de IA armazenem e recuperem informações sobre projetos, regras de desenvolvimento, padrões e contextos.

## 🚀 Funcionalidades

### 📝 Histórico de Desenvolvimento
- Armazenar tarefas completadas por projeto
- Rastrear tecnologias utilizadas
- Acompanhar arquivos modificados
- Contexto detalhado de cada tarefa

### 📏 Regras de Desenvolvimento
- Regras específicas por tecnologia (Java, Python, NestJS, etc.)
- Categorização por tipo (naming, structure, security, performance)
- Sistema de prioridades
- Aplicabilidade contextual

### 🎨 Padrões de Desenvolvimento
- Padrões arquiteturais e de design
- Exemplos de implementação
- Casos de uso e benefícios
- Níveis de complexidade

### 🎯 Contexto de Projetos
- Informações específicas por projeto
- Arquitetura e requisitos
- Sistema de tags e prioridades
- Contexto evolutivo

### 🔄 Protocolos e Processos
- Protocolos de desenvolvimento
- Processos de deployment
- Fluxos de trabalho
- Aplicabilidade por tecnologia

## 🛠️ Configuração

### Pré-requisitos

1. **Docker** (para MongoDB)
2. **Python 3.8+**
3. **Dependências Python**:
   ```bash
   pip install -r requirements.txt
   ```

### 1. Container MongoDB

O container MongoDB já está configurado e rodando na porta 2018:

```bash
# Verificar se está rodando
docker ps | grep mongo-dev-memory
```

### 2. Configuração do Servidor

O servidor está configurado para conectar ao MongoDB com:
- **URI**: `mongodb://admin:admin123@localhost:2018`
- **Database**: `dev_memory_db`
- **Permissões**: Administrativas (root)

### 3. Executar o Servidor

```bash
cd mong0-dev-memory-mcp
python3 server.py
```

## 🔧 Ferramentas Disponíveis

### Administração
- `mongo_connect` - Conecta ao MongoDB
- `mongo_create_collection` - Cria nova coleção
- `mongo_drop_collection` - Remove coleção
- `mongo_list_collections` - Lista todas as coleções

### Histórico de Desenvolvimento
- `mongo_insert_historico` - Insere registro no histórico
- `mongo_get_historico` - Obtém histórico de um projeto
- `mongo_get_all_projects_history` - Histórico de todos os projetos
- `mongo_search_historico` - Busca no histórico

### Regras de Desenvolvimento
- `mongo_insert_rule` - Insere regra de desenvolvimento
- `mongo_get_rules` - Obtém regras por tecnologia
- `mongo_update_rule` - Atualiza regra existente

### Padrões de Desenvolvimento
- `mongo_insert_pattern` - Insere padrão de desenvolvimento
- `mongo_get_patterns` - Obtém padrões por tecnologia

### Contexto de Projetos
- `mongo_insert_project_context` - Insere contexto de projeto
- `mongo_get_project_context` - Obtém contexto de projeto

### Protocolos
- `mongo_insert_protocol` - Insere protocolo
- `mongo_get_protocols` - Obtém protocolos

### Busca e Análise
- `mongo_search_global` - Busca global em todas as coleções
- `mongo_get_database_stats` - Estatísticas do banco
- `mongo_get_project_stats` - Estatísticas de projeto específico
- `mongo_get_technology_usage` - Estatísticas de uso de tecnologias

### Administrativo
- `mongo_backup_collection` - Backup de coleção
- `mongo_restore_collection` - Restaurar coleção

## 📊 Estrutura do Banco

### Coleções Principais

1. **historico** - Histórico de desenvolvimento
   ```json
   {
     "project_id": "string",
     "task_description": "string",
     "technologies": ["array"],
     "files_modified": ["array"],
     "context": "string",
     "status": "completed|in_progress|failed",
     "duration_minutes": "integer",
     "created_at": "datetime"
   }
   ```

2. **rules** - Regras de desenvolvimento
   ```json
   {
     "technology": "string",
     "rule_name": "string",
     "rule_content": "string",
     "category": "string",
     "priority": "integer",
     "applies_to": ["array"],
     "created_at": "datetime"
   }
   ```

3. **patterns** - Padrões de desenvolvimento
   ```json
   {
     "technology": "string",
     "pattern_name": "string",
     "pattern_description": "string",
     "pattern_example": "string",
     "category": "string",
     "use_cases": ["array"],
     "benefits": ["array"],
     "complexity": "low|medium|high",
     "created_at": "datetime"
   }
   ```

4. **project_context** - Contexto de projetos
   ```json
   {
     "project_id": "string",
     "context_type": "string",
     "context_content": "string",
     "priority": "integer",
     "tags": ["array"],
     "created_at": "datetime"
   }
   ```

5. **protocols** - Protocolos e processos
   ```json
   {
     "protocol_name": "string",
     "protocol_description": "string",
     "steps": ["array"],
     "applies_to": ["array"],
     "category": "string",
     "created_at": "datetime"
   }
   ```

## 🔍 Índices Otimizados

O servidor cria automaticamente índices otimizados para:
- Busca por projeto e data
- Busca por tecnologia
- Busca textual (full-text search)
- Filtragem por prioridade e categoria

## 🧪 Teste

Execute o script de teste para verificar se tudo está funcionando:

```bash
python3 test_connection.py
```

## 📝 Uso com MCP

Este servidor implementa o protocolo MCP e pode ser usado com qualquer cliente MCP compatível. As ferramentas estarão disponíveis para o agente de IA usar conforme necessário.

### Exemplo de Uso

1. **Registrar uma tarefa completada**:
   ```json
   {
     "name": "mongo_insert_historico",
     "arguments": {
       "project_id": "meu_projeto_001",
       "task_description": "Implementação de autenticação JWT",
       "technologies": ["nestjs", "typescript", "jwt"],
       "files_modified": ["auth.service.ts", "auth.controller.ts"],
       "context": "Implementação completa com middleware de validação",
       "status": "completed",
       "duration_minutes": 120
     }
   }
   ```

2. **Buscar regras para uma tecnologia**:
   ```json
   {
     "name": "mongo_get_rules",
     "arguments": {
       "technology": "nestjs",
       "category": "structure"
     }
   }
   ```

## 🔒 Segurança

- Conexão autenticada com MongoDB
- Permissões administrativas para gerenciamento completo
- Validação de entrada em todas as operações
- Tratamento de erros robusto

## 🚀 Benefícios

- **Memória Persistente**: O agente nunca perde o contexto do projeto
- **Aprendizado Contínuo**: Regras e padrões são acumulados ao longo do tempo
- **Consistência**: Padrões uniformes entre diferentes sessões
- **Rastreabilidade**: Histórico completo de desenvolvimento
- **Flexibilidade**: Suporte a múltiplas tecnologias e projetos

---

**Versão**: 2.0.0  
**Compatibilidade**: MCP 1.0+  
**MongoDB**: 7.0+