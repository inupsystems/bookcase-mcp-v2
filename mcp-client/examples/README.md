# Exemplos de Uso do MCP Client

Este diretório contém exemplos de configuração e uso do MCP Client.

## Arquivos de Configuração

### `config.json`
Configuração completa baseada no `mcp-exemplo.json` do projeto, incluindo:
- Servidor de memória (NPM)
- Servidor de pensamento sequencial (NPM)
- Agent API Tester (local)
- Servidor Docker (local)
- Servidor MongoDB (local)

### `simple-config.json`
Configuração simples para testes básicos com servidores de exemplo.

## Exemplos de Uso

### 1. Iniciando o Cliente

```bash
# Usando configuração padrão
mcp-client status

# Usando configuração específica
mcp-client -c examples/config.json status
```

### 2. Listando Servidores

```bash
# Listar servidores configurados
mcp-client servers list

# Testar conexão com servidores
mcp-client servers test

# Testar servidor específico
mcp-client servers test memory
```

### 3. Gerenciando Tools

```bash
# Listar todas as tools disponíveis
mcp-client tools list

# Listar tools de um servidor específico
mcp-client tools list --server memory

# Buscar tools por nome ou descrição
mcp-client tools list --search "create"

# Descrever uma tool específica
mcp-client tools describe memory_create

# Listar em formato JSON
mcp-client tools list --format json
```

### 4. Executando Tools

```bash
# Executar tool com parâmetros simples
mcp-client tools call memory_create --param key=test --param value="Hello World"

# Executar tool com parâmetros JSON
mcp-client tools call api_call --params-json '{"url": "https://api.github.com", "method": "GET"}'

# Executar tool específica de um servidor
mcp-client tools call --server docker container_list

# Executar tool com timeout personalizado
mcp-client tools call slow_operation --timeout 60

# Testar tool com parâmetros padrão
mcp-client tools test memory_create
```

### 5. Exemplos de Configuração Programática

```python
import asyncio
from mcp_client import MCPClient, MCPConfig

async def main():
    # Carregar de arquivo
    client = MCPClient.from_config_file("examples/config.json")
    
    # Inicializar e conectar
    await client.initialize()
    await client.connect()
    
    # Descobrir tools
    tools = await client.discover_tools()
    print(f"Descobri {sum(len(t) for t in tools.values())} tools")
    
    # Executar uma tool
    result = await client.execute_tool(
        tool_name="memory_create",
        parameters={"key": "test", "value": "Hello from Python!"}
    )
    
    if result.success:
        print(f"Tool executada com sucesso: {result.result}")
    else:
        print(f"Erro na execução: {result.error}")
    
    # Verificar status
    health = await client.health_check()
    print(f"Status: {health}")
    
    # Limpar
    await client.disconnect()

# Executar
asyncio.run(main())
```

### 6. Uso com Context Manager

```python
import asyncio
from mcp_client import MCPClient

async def main():
    async with MCPClient.from_config_file("examples/config.json") as client:
        await client.initialize()
        await client.connect()
        
        # Buscar por tools
        tools = client.search_tools("docker")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

asyncio.run(main())
```

### 7. Execução em Lote

```python
import asyncio
from mcp_client import MCPClient, ToolInvocation

async def main():
    client = MCPClient.from_config_file("examples/config.json")
    await client.initialize()
    await client.connect()
    
    # Executar múltiplas tools em paralelo
    invocations = [
        ToolInvocation(
            tool_name="memory_list",
            server_name="memory",
            parameters={}
        ),
        ToolInvocation(
            tool_name="docker_container_list",
            server_name="docker",
            parameters={}
        )
    ]
    
    results = await client.batch_execute(invocations)
    
    for result in results:
        if result.success:
            print(f"{result.tool_name}: {result.result}")
        else:
            print(f"{result.tool_name} falhou: {result.error}")
    
    await client.disconnect()

asyncio.run(main())
```

## Configuração de Desenvolvimento

Para desenvolver e testar com o MCP Client:

```bash
# Instalar em modo desenvolvimento
cd mcp-client
pip install -e ".[dev]"

# Executar testes
pytest

# Verificar cobertura
pytest --cov

# Verificar tipos
mypy src/

# Formatar código
black src/ tests/
isort src/ tests/
```

## Debugging

Para habilitar logs detalhados:

```bash
# Com verbose
mcp-client -v status

# Ou definir nível de log em Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Troubleshooting

### Problemas Comuns

1. **Servidor não conecta**
   - Verificar se o comando está correto
   - Verificar se as dependências estão instaladas
   - Verificar logs com `-v`

2. **Tool não encontrada**
   - Verificar se o servidor está conectado
   - Atualizar cache de tools: `mcp-client tools list --refresh`

3. **Timeout na execução**
   - Aumentar timeout na configuração
   - Usar `--timeout` no comando CLI

4. **Erro de parâmetros**
   - Verificar schema da tool: `mcp-client tools describe tool_name`
   - Validar JSON de parâmetros
