# Guia de Configuração e Uso - MongoDB Dev Memory MCP Server

## 🚀 Configuração Rápida

### 1. Pré-requisitos
- Docker instalado e rodando
- Python 3.8+
- Acesso à internet para download de dependências

### 2. Container MongoDB
O container MongoDB já está configurado e rodando:
- **Container**: mongo-dev-memory
- **Porta**: 2018 (mapeada para 27018)
- **Credenciais**: admin/admin123
- **Status**: ✅ Rodando

### 3. Instalação de Dependências
```bash
cd mong0-dev-memory-mcp
pip3 install pymongo --break-system-packages
```

### 4. Inicialização do Banco
```bash
python3 init_database.py
```

### 5. Teste de Funcionalidade
```bash
python3 test_server.py
```

## 📋 Estrutura do Projeto

```
mong0-dev-memory-mcp/
├── server.py              # Servidor MCP principal
├── init_database.py       # Script de inicialização do banco
├── test_server.py         # Script de teste
├── demo.py               # Demonstração completa
├── requirements.txt      # Dependências Python
├── README.md            # Documentação principal
├── SETUP.md             # Este guia
├── mcp-config.json      # Configuração MCP
└── client-config.json   # Configuração do cliente
```

## 🔧 Configuração do Cliente MCP

### Para Cursor/VS Code
Adicione ao seu arquivo de configuração MCP:

```json
{
  "mcpServers": {
    "mongo-dev-memory": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/caminho/para/mong0-dev-memory-mcp",
      "env": {
        "PYTHONPATH": "/caminho/para/mong0-dev-memory-mcp"
      }
    }
  }
}
```

### Para Claude Desktop
Use o arquivo `client-config.json` fornecido.

## 🛠️ Ferramentas Disponíveis

### Histórico de Desenvolvimento
- `mongo_insert_historico`: Insere registro no histórico
- `mongo_get_historico`: Obtém histórico de projeto
- `mongo_search_historico`: Busca no histórico por termos

### Regras de Desenvolvimento
- `mongo_insert_rule`: Insere regra de desenvolvimento
- `mongo_get_rules`: Obtém regras por tecnologia

### Padrões de Desenvolvimento
- `mongo_insert_pattern`: Insere padrão de desenvolvimento
- `mongo_get_patterns`: Obtém padrões por tecnologia

### Contexto de Projeto
- `mongo_insert_project_context`: Insere contexto de projeto
- `mongo_get_project_context`: Obtém contexto de projeto

### Gerenciamento
- `mongo_connect`: Conecta ao MongoDB
- `mongo_create_collection`: Cria nova coleção
- `mongo_get_database_stats`: Obtém estatísticas

## 📊 Dados Iniciais

O banco já está populado com:

### Regras de Desenvolvimento
- **Java/Spring**: 6 regras (naming, structure, best_practices, error_handling)
- **Python**: 5 regras (naming, structure, best_practices, documentation)
- **NestJS**: 5 regras (naming, structure, best_practices, error_handling)

### Padrões de Desenvolvimento
- **Java/Spring**: 3 padrões (Repository, Service Layer, DTO)
- **Python**: 2 padrões (Repository, Service Layer)
- **NestJS**: 2 padrões (Repository, Service)

## 🎯 Casos de Uso

### 1. Registrar Tarefa Concluída
```json
{
  "name": "mongo_insert_historico",
  "arguments": {
    "project_id": "meu-projeto",
    "task_description": "Implementado endpoint de usuários",
    "technologies": ["java", "spring"],
    "files_modified": ["UserController.java", "UserService.java"],
    "context": "Criado CRUD completo de usuários com validações"
  }
}
```

### 2. Consultar Regras de Java
```json
{
  "name": "mongo_get_rules",
  "arguments": {
    "technology": "java",
    "category": "naming"
  }
}
```

### 3. Buscar Histórico de Projeto
```json
{
  "name": "mongo_get_historico",
  "arguments": {
    "project_id": "meu-projeto",
    "limit": 10
  }
}
```

### 4. Adicionar Contexto de Projeto
```json
{
  "name": "mongo_insert_project_context",
  "arguments": {
    "project_id": "meu-projeto",
    "context_type": "architecture",
    "context_content": "Arquitetura em camadas com Spring Boot",
    "priority": 8
  }
}
```

## 🔍 Monitoramento

### Verificar Status do Container
```bash
docker ps | grep mongo-dev-memory
```

### Verificar Logs do MongoDB
```bash
docker logs mongo-dev-memory
```

### Estatísticas do Banco
```bash
python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://admin:admin123@localhost:2018')
db = client['dev_memory_db']
print('Regras:', db.rules.count_documents({}))
print('Padrões:', db.patterns.count_documents({}))
print('Histórico:', db.historico.count_documents({}))
print('Contexto:', db.project_context.count_documents({}))
"
```

## 🚨 Solução de Problemas

### Erro de Conexão
- Verificar se o container está rodando: `docker ps`
- Verificar porta: `netstat -tlnp | grep 2018`
- Reiniciar container: `docker restart mongo-dev-memory`

### Erro de Dependências
- Instalar pymongo: `pip3 install pymongo --break-system-packages`
- Verificar Python: `python3 --version`

### Erro de Permissões
- Verificar credenciais MongoDB: admin/admin123
- Verificar URI de conexão no código

## 📈 Próximos Passos

1. **Integração com IA**: Configure o servidor MCP no seu cliente preferido
2. **Personalização**: Adicione suas próprias regras e padrões
3. **Automação**: Configure triggers para inserção automática de histórico
4. **Backup**: Configure backup regular do banco de dados
5. **Monitoramento**: Implemente alertas e métricas

## 🎉 Status Atual

- ✅ Container MongoDB rodando
- ✅ Banco inicializado com dados
- ✅ Servidor MCP funcional
- ✅ Testes passando
- ✅ Documentação completa

**O servidor está pronto para uso!** 🚀


