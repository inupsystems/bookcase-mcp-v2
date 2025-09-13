# Agent Tester - Sistema DeepSeek + MCP

Sistema integrado que combina DeepSeek AI com ferramentas MCP para testes automatizados.

## 🚀 Funcionalidades

- **Interface Gradio**: Interface web intuitiva na porta 7862
- **DeepSeek AI**: Processamento inteligente de solicitações de teste
- **Integração MCP**: Acesso a múltiplas ferramentas via Model Context Protocol
- **Testes Automatizados**: Execução de testes de API e validações
- **Armazenamento**: Histórico de testes salvos em MongoDB
- **Chat Inteligente**: Conversação natural para execução de testes

## 🛠️ Instalação

1. **Instalar dependências**:
   ```bash
   cd agent/
   ./install.sh
   ```

2. **Ativar ambiente virtual**:
   ```bash
   source venv/bin/activate
   ```

3. **Executar interface**:
   ```bash
   python gradio_interface.py
   ```

4. **Acessar interface**:
   - Abrir navegador em: http://localhost:7862

## ⚙️ Configuração

### API Key do DeepSeek

1. Obter chave em: https://platform.deepseek.com/
2. Inserir na interface web no campo "DeepSeek API Key"
3. Clicar em "Inicializar Agent"

### Ferramentas MCP

O sistema conecta automaticamente às ferramentas configuradas em `../examples/config.json`:

- **agent-api-tester**: Testes de API HTTP
- **mongo-dev-memory**: Armazenamento de histórico
- **memory**: Memória temporária
- **docker**: Gerenciamento de containers
- **sequentialthinking**: Raciocínio estruturado

## 📋 Como Usar

### Chat Inteligente

Digite solicitações em linguagem natural:

- "Execute um teste GET na API https://jsonplaceholder.typicode.com/posts/1"
- "Salve o resultado do último teste no histórico"
- "Mostre as ferramentas disponíveis"
- "Teste se o Docker está funcionando"

### Testes Rápidos

Use os testes predefinidos:

- **Conectividade**: Verifica conexões MCP
- **API Básica**: Testa endpoint HTTP simples
- **Memória**: Valida MongoDB
- **Docker**: Verifica containers
- **Histórico**: Mostra testes salvos

### Exemplos de Comandos

```
Lista das ferramentas disponíveis
Execute um teste GET na API https://jsonplaceholder.typicode.com/posts/1
Teste se o servidor de memória está funcionando
Salve um resultado de teste no histórico
Mostre o histórico de testes do projeto 'agent-tester'
Execute um teste POST para criar um novo carrier
Verifique a conectividade com o Docker
Teste de busca global no mongo-dev-memory
```

## 🏗️ Arquitetura

### DeepSeekMCPAgent

Classe principal que integra:

- **Cliente DeepSeek**: Conexão com API DeepSeek
- **Cliente MCP**: Gerenciamento de ferramentas MCP
- **Processamento de Comandos**: Interpretação de linguagem natural
- **Execução de Ferramentas**: Chamadas automáticas de ferramentas

### Gradio Interface

Interface web com:

- **Chat Tab**: Conversação principal
- **Ferramentas Tab**: Lista de ferramentas disponíveis
- **Testes Rápidos Tab**: Testes predefinidos
- **Ajuda Tab**: Documentação e exemplos

### Fluxo de Operação

1. **Usuário**: Digita solicitação
2. **DeepSeek**: Processa e identifica ferramentas necessárias
3. **MCP Client**: Executa ferramentas identificadas
4. **Agent**: Retorna resultados formatados
5. **Interface**: Exibe resposta ao usuário

## 🔧 Desenvolvimento

### Estrutura de Arquivos

```
agent/
├── deepseek_mcp_agent.py      # Agent principal
├── gradio_interface.py        # Interface web
├── requirements.txt           # Dependências
├── install.sh                # Script de instalação
├── README.md                 # Documentação
└── venv/                     # Ambiente virtual
```

### Extensões

Para adicionar novas funcionalidades:

1. **Novas Ferramentas**: Configurar em `../examples/config.json`
2. **Prompts Customizados**: Modificar `system_prompt` em `deepseek_mcp_agent.py`
3. **Interface**: Adicionar tabs ou elementos em `gradio_interface.py`

### Debug

Para debug e desenvolvimento:

```bash
# Teste independente do agent
python deepseek_mcp_agent.py

# Logs detalhados
export PYTHONPATH=$PYTHONPATH:/path/to/mcp-client/src
python gradio_interface.py
```

## 📊 Monitoramento

### Logs

O sistema gera logs detalhados para:

- Inicialização de conexões MCP
- Execução de ferramentas
- Respostas do DeepSeek
- Erros e exceções

### Histórico

Todos os testes são salvos em MongoDB via `mongo-dev-memory`:

- Projeto ID: "agent-tester"
- Contexto: Resultados em JSON
- Status: completed/failed
- Tecnologias: ["API", "MCP", "DeepSeek"]

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de importação MCP**: 
   - Verificar instalação: `pip install -e ../`

2. **DeepSeek API não responde**:
   - Verificar chave da API
   - Verificar conectividade de rede

3. **Ferramentas MCP não conectam**:
   - Verificar `../examples/config.json`
   - Verificar servidores MCP rodando

4. **Interface não carrega**:
   - Verificar porta 7862 disponível
   - Verificar instalação do Gradio

### Suporte

Para problemas adicionais:

1. Verificar logs do sistema
2. Testar `deepseek_mcp_agent.py` independentemente
3. Validar configuração MCP
4. Verificar ambiente Python 3.8+
