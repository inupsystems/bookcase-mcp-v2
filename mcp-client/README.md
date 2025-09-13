# MCP Client

A Python client for connecting to multiple MCP (Model Context Protocol) servers through configuration.

## Requisitos Funcionais

### 1. Gerenciamento de Configuração
- ✅ Ler configuração de servidores MCP de arquivo JSON
- ✅ Validar configuração com esquemas JSON Schema
- ✅ Suporte a diferentes tipos de conexão:
  - `stdio`: Comunicação via stdin/stdout
  - `socket`: Comunicação via socket TCP/Unix
  - `http`: Comunicação via HTTP/REST
- ✅ Configurações específicas por servidor:
  - Comando e argumentos para execução
  - Variáveis de ambiente
  - Diretório de trabalho
  - Timeout de conexão
  - Tipo de comunicação

### 2. Gerenciamento de Conexões
- ✅ Conectar automaticamente aos servidores configurados
- ✅ Detectar e ignorar servidores com erro
- ✅ Manter estado de conexão (conectado/desconectado/erro)
- ✅ Reconexão automática para servidores perdidos
- ✅ Pool de conexões para múltiplos servidores
- ✅ Timeout configurável para operações

### 3. Descoberta de Tools
- ✅ Listar tools disponíveis em cada servidor
- ✅ Descoberta automática ao conectar
- ✅ Cache de tools descobertas
- ✅ Refresh periódico da lista de tools
- ✅ Metadados das tools (nome, descrição, parâmetros, schema)

### 4. Execução de Tools
- ✅ Executar tools em servidores específicos
- ✅ Validação de parâmetros de entrada
- ✅ Handling de erros de execução
- ✅ Timeout configurável para execução
- ✅ Logs de execução e resultados

### 5. Interface de Usuário
- ✅ CLI para operações básicas
- ✅ Comandos para listar servidores e tools
- ✅ Comandos para executar tools
- ✅ Output formatado (JSON, tabular, etc.)

## Requisitos Não-Funcionais

### 1. Performance
- ✅ Conexões assíncronas para múltiplos servidores
- ✅ Cache eficiente de tools e metadados
- ✅ Pool de conexões reutilizáveis

### 2. Confiabilidade
- ✅ Tratamento robusto de erros
- ✅ Reconnection automática
- ✅ Validação rigorosa de inputs
- ✅ Logs detalhados para debugging

### 3. Extensibilidade
- ✅ Arquitetura modular
- ✅ Interfaces bem definidas
- ✅ Plugins para novos tipos de conexão
- ✅ Configuração flexível

### 4. Usabilidade
- ✅ CLI intuitiva
- ✅ Documentação clara
- ✅ Exemplos de uso
- ✅ Mensagens de erro informativas

## Instalação Rápida

```bash
cd mcp-client
./install.sh
```

Ou manualmente:

```bash
cd mcp-client
pip install -e .
```

## Uso Básico

```bash
# Verificar status
mcp-client status

# Listar servidores configurados
mcp-client servers list

# Testar conexões
mcp-client servers test

# Listar tools disponíveis
mcp-client tools list

# Executar uma tool
mcp-client tools call tool_name --param key=value

# Executar demonstração
python demo.py
```

## Configuração

Exemplo de arquivo de configuração (`config.json`):

```json
{
  "servers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {"MEMORY_FILE_PATH": "memory.txt"},
      "type": "stdio",
      "timeout": 30000
    },
    "api-server": {
      "command": "./api-server.sh",
      "args": [],
      "type": "stdio",
      "env": {"API_BASE_URL": "http://localhost:8881"},
      "cwd": "/path/to/server",
      "timeout": 30000
    }
  }
}
```

## Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# Executar testes
pytest

# Formatação de código
black src/ tests/
isort src/ tests/

# Verificação de tipos
mypy src/
```
