## Configuração do Model Context Protocol no VS Code

Para integrar o projeto com o Model Context Protocol (MCP) no VS Code:

1. Copie o arquivo `mcp-exemplo.json` para o local de configuração do MCP ou ajuste conforme necessário.
2. No VS Code, utilize a extensão ou plugin do MCP e selecione o arquivo de configuração `mcp-exemplo.json`.
3. O arquivo já traz exemplos de comandos para diferentes servidores (memory, sequentialthinking, docker, mongo-dev-memory). Basta ajustar os caminhos se necessário para o seu ambiente.
4. Para o servidor mongo-dev-memory, certifique-se que o ambiente está preparado e o container do MongoDB está rodando.

Exemplo de configuração:
```json
{
	"memory": { ... },
	"sequentialthinking": { ... },
	"docker": { ... },
	"mongo-dev-memory": { ... }
}
```

Com isso, o VS Code poderá se comunicar com os servidores MCP do projeto, facilitando automação e integração inteligente.
## Como executar o projeto

1. Para subir todo o ambiente principal, execute na raiz:
	```bash
	./run-container.sh
	```
	Isso irá subir o MongoDB, instalar dependências do mongo-dev-memory-mcp e preparar o banco.

2. O serviço memory-ui estará disponível em:
	[http://127.0.0.1:7860/](http://127.0.0.1:7860/)
	Basta acessar pelo navegador e preencher o formulário para salvar o contexto do projeto.

## Sobre o memory-ui

O memory-ui é uma interface web simples para cadastro de contexto de projetos. O usuário acessa a tela, preenche o formulário e salva informações diretamente no banco MongoDB.

## Integração com docker-mcp ou outros MCPs

Para preparar o ambiente docker-mcp ou outro MCP integrado, execute o script `install` do respectivo módulo separadamente:
```bash
cd docker-mcp
./install.sh
```

## Pasta work-AI

A pasta `work-AI` contém arquivos de instruções e contexto para uso do modelo de IA, facilitando a geração de contexto e automação de tarefas inteligentes.
# bookcase-mcp-v2
