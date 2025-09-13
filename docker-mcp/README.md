# Docker MCP Server

Um servidor MCP (Model Context Protocol) para gerenciar Docker containers, imagens, volumes, redes e mais.

## Funcionalidades

### Containers
- `docker_container_list` - Lista todos os containers
- `docker_container_create` - Cria um novo container
- `docker_container_start` - Inicia um container parado
- `docker_container_stop` - Para um container em execução
- `docker_container_remove` - Remove um container
- `docker_container_logs` - Visualiza logs de um container
- `docker_container_stats` - Mostra estatísticas de uso de recursos

### Imagens
- `docker_image_list` - Lista todas as imagens
- `docker_image_pull` - Baixa uma imagem do registry
- `docker_image_remove` - Remove uma imagem
- `docker_image_build` - Constrói uma imagem a partir de um Dockerfile

### Volumes
- `docker_volume_list` - Lista todos os volumes
- `docker_volume_create` - Cria um novo volume
- `docker_volume_remove` - Remove um volume

### Redes
- `docker_network_list` - Lista todas as redes
- `docker_network_create` - Cria uma nova rede
- `docker_network_remove` - Remove uma rede

### Sistema
- `docker_system_info` - Mostra informações do sistema Docker
- `docker_system_df` - Mostra uso de espaço em disco
- `docker_system_prune` - Limpa recursos não utilizados

## Instalação

1. Pré-requisitos:
   - Python 3.8+
   - Docker instalado e rodando
   - Permissões para acessar o Docker daemon

2. Criar ambiente virtual e instalar dependências:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   Ou use o script de instalação:
   ```bash
   ./install.sh
   ```

3. Executar o servidor:
   ```bash
   source venv/bin/activate
   python main.py
   ```

## Configuração

Exemplo para Claude Desktop ou Cursor (ajuste caminhos):
```json
{
  "mcpServers": {
    "docker": {
      "command": "/caminho/para/docker-mcp/venv/bin/python",
      "args": ["/caminho/para/docker-mcp/main.py"],
      "env": {}
    }
  }
}
```

## Exemplos de Uso

### Listar containers
```
Liste todos os containers Docker
```

### Criar e iniciar um container
```
Crie um container nginx na porta 8080
```

### Ver logs de um container
```
Mostre os logs do container nginx
```

### Construir uma imagem
```
Construa uma imagem Docker a partir do Dockerfile na pasta /path/to/project com a tag minha-app:latest
```

### Limpar sistema
```
Execute uma limpeza do sistema Docker removendo recursos não utilizados
```

## Segurança

⚠️ Importante: Este servidor MCP tem acesso completo ao Docker daemon. Use apenas em ambientes confiáveis e com as devidas precauções.

- Pode criar, modificar e remover containers, imagens, volumes e redes
- Cuidado com `docker_system_prune`
- Considere autenticação/autorização em produção

## Desenvolvimento

Estrutura do projeto:
```
docker-mcp/
├── src/
│   ├── __init__.py
│   └── server.py
├── main.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

Para adicionar ferramentas:
1. Defina em `handle_list_tools()`
2. Despache em `handle_call_tool()`
3. Implemente a função

## Troubleshooting

### "Cliente Docker não inicializado"
- Verifique `docker ps`
- Permissões do daemon
- Linux: `sudo usermod -aG docker $USER`

### "Permission denied"
- Acesso a `/var/run/docker.sock`

### Container não inicia
- Imagem existe? Portas livres? Veja logs

## Licença

MIT License
