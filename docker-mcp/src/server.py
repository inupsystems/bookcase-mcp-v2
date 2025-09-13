#!/usr/bin/env python3
"""
Servidor MCP para Docker
Fornece ferramentas para gerenciar containers, imagens, volumes, redes e mais.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
import os

import docker
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource, 
    LoggingLevel
)
from pydantic import AnyUrl

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docker-mcp-server")

# Inicializar servidor MCP
server = Server("docker-mcp-server")

# Cliente Docker
docker_client = None

def init_docker_client():
    """Inicializa o cliente Docker"""
    global docker_client
    try:
        docker_client = docker.from_env()
        # Testar conexão
        docker_client.ping()
        logger.info("Conectado ao Docker com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar com Docker: {e}")
        return False

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Lista todas as ferramentas disponíveis"""
    return [
        Tool(
            name="docker_container_list",
            description="Lista todos os containers Docker (rodando e parados)",
            inputSchema={
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "description": "Se True, mostra todos os containers (incluindo parados). Default: True",
                        "default": True
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filtros para aplicar na listagem (ex: {'status': 'running'})",
                        "default": {}
                    }
                }
            }
        ),
        Tool(
            name="docker_container_create",
            description="Cria e opcionalmente inicia um novo container",
            inputSchema={
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "description": "Nome da imagem Docker para usar"
                    },
                    "name": {
                        "type": "string",
                        "description": "Nome para o container (opcional)"
                    },
                    "command": {
                        "type": "string",
                        "description": "Comando para executar no container (opcional)"
                    },
                    "ports": {
                        "type": "object",
                        "description": "Mapeamento de portas (ex: {'80/tcp': 8080})",
                        "default": {}
                    },
                    "environment": {
                        "type": "object",
                        "description": "Variáveis de ambiente (ex: {'ENV_VAR': 'value'})",
                        "default": {}
                    },
                    "volumes": {
                        "type": "object",
                        "description": "Mapeamento de volumes (ex: {'/host/path': {'bind': '/container/path', 'mode': 'rw'}})",
                        "default": {}
                    },
                    "detach": {
                        "type": "boolean",
                        "description": "Executar em background",
                        "default": True
                    },
                    "auto_start": {
                        "type": "boolean",
                        "description": "Iniciar o container automaticamente após criação",
                        "default": True
                    }
                },
                "required": ["image"]
            }
        ),
        Tool(
            name="docker_container_start",
            description="Inicia um container parado",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "ID ou nome do container para iniciar"
                    }
                },
                "required": ["container_id"]
            }
        ),
        Tool(
            name="docker_container_stop",
            description="Para um container em execução",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "ID ou nome do container para parar"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout em segundos antes de forçar parada",
                        "default": 10
                    }
                },
                "required": ["container_id"]
            }
        ),
        Tool(
            name="docker_container_remove",
            description="Remove um container (deve estar parado)",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "ID ou nome do container para remover"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Forçar remoção mesmo se estiver rodando",
                        "default": False
                    },
                    "remove_volumes": {
                        "type": "boolean",
                        "description": "Remover volumes associados",
                        "default": False
                    }
                },
                "required": ["container_id"]
            }
        ),
        Tool(
            name="docker_container_logs",
            description="Obtém os logs de um container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "ID ou nome do container"
                    },
                    "tail": {
                        "type": "integer",
                        "description": "Número de linhas do final para mostrar (default: 100)",
                        "default": 100
                    },
                    "follow": {
                        "type": "boolean",
                        "description": "Seguir logs em tempo real (cuidado com performance)",
                        "default": False
                    },
                    "timestamps": {
                        "type": "boolean",
                        "description": "Incluir timestamps nos logs",
                        "default": True
                    }
                },
                "required": ["container_id"]
            }
        ),
        Tool(
            name="docker_container_stats",
            description="Obtém estatísticas de uso de recursos de um container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "ID ou nome do container"
                    }
                },
                "required": ["container_id"]
            }
        ),
        Tool(
            name="docker_image_list",
            description="Lista todas as imagens Docker locais",
            inputSchema={
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "description": "Mostrar todas as imagens, incluindo intermediárias",
                        "default": False
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filtros para aplicar",
                        "default": {}
                    }
                }
            }
        ),
        Tool(
            name="docker_image_pull",
            description="Baixa uma imagem do registry",
            inputSchema={
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Nome da imagem para baixar (ex: 'nginx:latest')"
                    },
                    "tag": {
                        "type": "string",
                        "description": "Tag específica (opcional, default: 'latest')",
                        "default": "latest"
                    }
                },
                "required": ["repository"]
            }
        ),
        Tool(
            name="docker_image_remove",
            description="Remove uma imagem Docker",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_id": {
                        "type": "string",
                        "description": "ID ou nome da imagem para remover"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Forçar remoção mesmo se estiver em uso",
                        "default": False
                    }
                },
                "required": ["image_id"]
            }
        ),
        Tool(
            name="docker_image_build",
            description="Constrói uma imagem Docker a partir de um Dockerfile",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho para o diretório com Dockerfile"
                    },
                    "tag": {
                        "type": "string",
                        "description": "Tag para a imagem construída"
                    },
                    "dockerfile": {
                        "type": "string",
                        "description": "Nome do Dockerfile (default: 'Dockerfile')",
                        "default": "Dockerfile"
                    },
                    "no_cache": {
                        "type": "boolean",
                        "description": "Não usar cache durante a construção",
                        "default": False
                    }
                },
                "required": ["path", "tag"]
            }
        ),
        Tool(
            name="docker_volume_list",
            description="Lista todos os volumes Docker",
            inputSchema={
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": "Filtros para aplicar",
                        "default": {}
                    }
                }
            }
        ),
        Tool(
            name="docker_volume_create",
            description="Cria um novo volume Docker",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome do volume"
                    },
                    "driver": {
                        "type": "string",
                        "description": "Driver do volume (default: 'local')",
                        "default": "local"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="docker_volume_remove",
            description="Remove um volume Docker",
            inputSchema={
                "type": "object",
                "properties": {
                    "volume_name": {
                        "type": "string",
                        "description": "Nome do volume para remover"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Forçar remoção",
                        "default": False
                    }
                },
                "required": ["volume_name"]
            }
        ),
        Tool(
            name="docker_network_list",
            description="Lista todas as redes Docker",
            inputSchema={
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": "Filtros para aplicar",
                        "default": {}
                    }
                }
            }
        ),
        Tool(
            name="docker_network_create",
            description="Cria uma nova rede Docker",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome da rede"
                    },
                    "driver": {
                        "type": "string",
                        "description": "Driver da rede (default: 'bridge')",
                        "default": "bridge"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="docker_network_remove",
            description="Remove uma rede Docker",
            inputSchema={
                "type": "object",
                "properties": {
                    "network_name": {
                        "type": "string",
                        "description": "Nome da rede para remover"
                    }
                },
                "required": ["network_name"]
            }
        ),
        Tool(
            name="docker_system_info",
            description="Obtém informações do sistema Docker",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="docker_system_df",
            description="Mostra uso de espaço em disco do Docker",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="docker_system_prune",
            description="Remove recursos não utilizados (containers parados, redes não utilizadas, imagens órfãs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "description": "Remover todas as imagens não utilizadas, não apenas as órfãs",
                        "default": False
                    },
                    "volumes": {
                        "type": "boolean",
                        "description": "Incluir volumes na limpeza",
                        "default": False
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Manipula chamadas de ferramentas"""
    
    if not docker_client:
        return [TextContent(type="text", text="Erro: Cliente Docker não inicializado")]
    
    try:
        if name == "docker_container_list":
            return await handle_container_list(arguments)
        elif name == "docker_container_create":
            return await handle_container_create(arguments)
        elif name == "docker_container_start":
            return await handle_container_start(arguments)
        elif name == "docker_container_stop":
            return await handle_container_stop(arguments)
        elif name == "docker_container_remove":
            return await handle_container_remove(arguments)
        elif name == "docker_container_logs":
            return await handle_container_logs(arguments)
        elif name == "docker_container_stats":
            return await handle_container_stats(arguments)
        elif name == "docker_image_list":
            return await handle_image_list(arguments)
        elif name == "docker_image_pull":
            return await handle_image_pull(arguments)
        elif name == "docker_image_remove":
            return await handle_image_remove(arguments)
        elif name == "docker_image_build":
            return await handle_image_build(arguments)
        elif name == "docker_volume_list":
            return await handle_volume_list(arguments)
        elif name == "docker_volume_create":
            return await handle_volume_create(arguments)
        elif name == "docker_volume_remove":
            return await handle_volume_remove(arguments)
        elif name == "docker_network_list":
            return await handle_network_list(arguments)
        elif name == "docker_network_create":
            return await handle_network_create(arguments)
        elif name == "docker_network_remove":
            return await handle_network_remove(arguments)
        elif name == "docker_system_info":
            return await handle_system_info(arguments)
        elif name == "docker_system_df":
            return await handle_system_df(arguments)
        elif name == "docker_system_prune":
            return await handle_system_prune(arguments)
        else:
            return [TextContent(type="text", text=f"Ferramenta desconhecida: {name}")]
    
    except Exception as e:
        logger.error(f"Erro ao executar ferramenta {name}: {e}")
        return [TextContent(type="text", text=f"Erro ao executar {name}: {str(e)}")]

# Implementações das ferramentas
async def handle_container_list(args: Dict[str, Any]) -> List[TextContent]:
    """Lista containers"""
    all_containers = args.get("all", True)
    filters = args.get("filters", {})
    
    containers = docker_client.containers.list(all=all_containers, filters=filters)
    
    if not containers:
        return [TextContent(type="text", text="Nenhum container encontrado")]
    
    result = "## Containers Docker\n\n"
    for container in containers:
        status = container.status
        ports = container.ports
        port_info = ""
        if ports:
            port_mappings = []
            for container_port, host_ports in ports.items():
                if host_ports:
                    for host_port in host_ports:
                        port_mappings.append(f"{host_port['HostPort']}:{container_port}")
            if port_mappings:
                port_info = f" | Portas: {', '.join(port_mappings)}"
        
        result += f"**{container.name}** ({container.short_id})\n"
        result += f"- Status: {status}\n"
        result += f"- Imagem: {container.image.tags[0] if container.image.tags else container.image.short_id}\n"
        if port_info:
            result += f"- {port_info.strip(' |')}\n"
        result += f"- Criado: {container.attrs['Created'][:19]}\n\n"
    
    return [TextContent(type="text", text=result)]

async def handle_container_create(args: Dict[str, Any]) -> List[TextContent]:
    """Cria um container"""
    image = args["image"]
    name = args.get("name")
    command = args.get("command")
    ports = args.get("ports", {})
    environment = args.get("environment", {})
    volumes = args.get("volumes", {})
    detach = args.get("detach", True)
    auto_start = args.get("auto_start", True)
    
    try:
        container = docker_client.containers.create(
            image=image,
            name=name,
            command=command,
            ports=ports,
            environment=environment,
            volumes=volumes,
            detach=detach
        )
        
        result = f"✅ Container criado: {container.name} ({container.short_id})\n"
        
        if auto_start:
            container.start()
            result += f"✅ Container iniciado com sucesso\n"
        
        return [TextContent(type="text", text=result)]
        
    except docker.errors.ImageNotFound:
        return [TextContent(type="text", text=f"❌ Erro: Imagem '{image}' não encontrada")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao criar container: {str(e)}")]

async def handle_container_start(args: Dict[str, Any]) -> List[TextContent]:
    """Inicia um container"""
    container_id = args["container_id"]
    
    try:
        container = docker_client.containers.get(container_id)
        container.start()
        return [TextContent(type="text", text=f"✅ Container {container.name} iniciado com sucesso")]
    except docker.errors.NotFound:
        return [TextContent(type="text", text=f"❌ Container '{container_id}' não encontrado")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao iniciar container: {str(e)}")]

async def handle_container_stop(args: Dict[str, Any]) -> List[TextContent]:
    """Para um container"""
    container_id = args["container_id"]
    timeout = args.get("timeout", 10)
    
    try:
        container = docker_client.containers.get(container_id)
        container.stop(timeout=timeout)
        return [TextContent(type="text", text=f"✅ Container {container.name} parado com sucesso")]
    except docker.errors.NotFound:
        return [TextContent(type="text", text=f"❌ Container '{container_id}' não encontrado")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao parar container: {str(e)}")]

async def handle_container_remove(args: Dict[str, Any]) -> List[TextContent]:
    """Remove um container"""
    container_id = args["container_id"]
    force = args.get("force", False)
    remove_volumes = args.get("remove_volumes", False)
    
    try:
        container = docker_client.containers.get(container_id)
        container_name = container.name
        container.remove(force=force, v=remove_volumes)
        return [TextContent(type="text", text=f"✅ Container {container_name} removido com sucesso")]
    except docker.errors.NotFound:
        return [TextContent(type="text", text=f"❌ Container '{container_id}' não encontrado")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao remover container: {str(e)}")]

async def handle_container_logs(args: Dict[str, Any]) -> List[TextContent]:
    """Obtém logs de um container"""
    container_id = args["container_id"]
    tail = args.get("tail", 100)
    timestamps = args.get("timestamps", True)
    
    try:
        container = docker_client.containers.get(container_id)
        logs = container.logs(tail=tail, timestamps=timestamps).decode('utf-8')
        
        if not logs.strip():
            return [TextContent(type="text", text=f"Nenhum log encontrado para o container {container.name}")]
        
        result = f"## Logs do Container: {container.name}\n\n```\n{logs}\n```"
        return [TextContent(type="text", text=result)]
        
    except docker.errors.NotFound:
        return [TextContent(type="text", text=f"❌ Container '{container_id}' não encontrado")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao obter logs: {str(e)}")]

async def handle_container_stats(args: Dict[str, Any]) -> List[TextContent]:
    """Obtém estatísticas de um container"""
    container_id = args["container_id"]
    
    try:
        container = docker_client.containers.get(container_id)
        stats = container.stats(stream=False)
        
        # Calcular CPU usage
        cpu_stats = stats['cpu_stats']
        precpu_stats = stats['precpu_stats']
        
        cpu_usage = 0.0
        if 'cpu_usage' in cpu_stats and 'cpu_usage' in precpu_stats:
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            if system_delta > 0:
                cpu_usage = (cpu_delta / system_delta) * len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', [])) * 100.0
        
        # Memory usage
        memory_stats = stats['memory_stats']
        memory_usage = memory_stats.get('usage', 0)
        memory_limit = memory_stats.get('limit', 0)
        memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
        
        # Network I/O
        networks = stats.get('networks', {})
        net_rx = sum(net['rx_bytes'] for net in networks.values())
        net_tx = sum(net['tx_bytes'] for net in networks.values())
        
        result = f"## Estatísticas do Container: {container.name}\n\n"
        result += f"**CPU:** {cpu_usage:.2f}%\n"
        result += f"**Memória:** {memory_usage / 1024 / 1024:.2f} MB / {memory_limit / 1024 / 1024:.2f} MB ({memory_percent:.2f}%)\n"
        result += f"**Rede RX:** {net_rx / 1024 / 1024:.2f} MB\n"
        result += f"**Rede TX:** {net_tx / 1024 / 1024:.2f} MB\n"
        
        return [TextContent(type="text", text=result)]
        
    except docker.errors.NotFound:
        return [TextContent(type="text", text=f"❌ Container '{container_id}' não encontrado")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao obter estatísticas: {str(e)}")]

async def handle_image_list(args: Dict[str, Any]) -> List[TextContent]:
    """Lista imagens"""
    all_images = args.get("all", False)
    filters = args.get("filters", {})
    
    images = docker_client.images.list(all=all_images, filters=filters)
    
    if not images:
        return [TextContent(type="text", text="Nenhuma imagem encontrada")]
    
    result = "## Imagens Docker\n\n"
    for image in images:
        tags = image.tags if image.tags else ["<none>"]
        size = image.attrs.get('Size', 0) / 1024 / 1024  # MB
        created = image.attrs.get('Created', '')[:19] if image.attrs.get('Created') else 'Desconhecido'
        
        result += f"**{tags[0]}** ({image.short_id})\n"
        result += f"- Tamanho: {size:.2f} MB\n"
        result += f"- Criado: {created}\n"
        if len(tags) > 1:
            result += f"- Tags adicionais: {', '.join(tags[1:])}\n"
        result += "\n"
    
    return [TextContent(type="text", text=result)]

async def handle_image_pull(args: Dict[str, Any]) -> List[TextContent]:
    """Baixa uma imagem"""
    repository = args["repository"]
    tag = args.get("tag", "latest")
    
    full_name = f"{repository}:{tag}" if ":" not in repository else repository
    
    try:
        image = docker_client.images.pull(full_name)
        return [TextContent(type="text", text=f"✅ Imagem {full_name} baixada com sucesso")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao baixar imagem: {str(e)}")]

async def handle_image_remove(args: Dict[str, Any]) -> List[TextContent]:
    """Remove uma imagem"""
    image_id = args["image_id"]
    force = args.get("force", False)
    
    try:
        docker_client.images.remove(image_id, force=force)
        return [TextContent(type="text", text=f"✅ Imagem {image_id} removida com sucesso")]
    except docker.errors.ImageNotFound:
        return [TextContent(type="text", text=f"❌ Imagem '{image_id}' não encontrada")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao remover imagem: {str(e)}")]

async def handle_image_build(args: Dict[str, Any]) -> List[TextContent]:
    """Constrói uma imagem"""
    path = args["path"]
    tag = args["tag"]
    dockerfile = args.get("dockerfile", "Dockerfile")
    no_cache = args.get("no_cache", False)
    
    try:
        if not os.path.exists(path):
            return [TextContent(type="text", text=f"❌ Caminho não encontrado: {path}")]
        
        dockerfile_path = os.path.join(path, dockerfile)
        if not os.path.exists(dockerfile_path):
            return [TextContent(type="text", text=f"❌ Dockerfile não encontrado: {dockerfile_path}")]
        
        image, build_logs = docker_client.images.build(
            path=path,
            tag=tag,
            dockerfile=dockerfile,
            nocache=no_cache
        )
        
        return [TextContent(type="text", text=f"✅ Imagem {tag} construída com sucesso")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao construir imagem: {str(e)}")]

async def handle_volume_list(args: Dict[str, Any]) -> List[TextContent]:
    """Lista volumes"""
    filters = args.get("filters", {})
    
    volumes = docker_client.volumes.list(filters=filters)
    
    if not volumes:
        return [TextContent(type="text", text="Nenhum volume encontrado")]
    
    result = "## Volumes Docker\n\n"
    for volume in volumes:
        driver = volume.attrs.get('Driver', 'desconhecido')
        mountpoint = volume.attrs.get('Mountpoint', 'desconhecido')
        created = volume.attrs.get('CreatedAt', '')[:19] if volume.attrs.get('CreatedAt') else 'Desconhecido'
        
        result += f"**{volume.name}**\n"
        result += f"- Driver: {driver}\n"
        result += f"- Mountpoint: {mountpoint}\n"
        result += f"- Criado: {created}\n\n"
    
    return [TextContent(type="text", text=result)]

async def handle_volume_create(args: Dict[str, Any]) -> List[TextContent]:
    """Cria um volume"""
    name = args["name"]
    driver = args.get("driver", "local")
    
    try:
        volume = docker_client.volumes.create(name=name, driver=driver)
        return [TextContent(type="text", text=f"✅ Volume {name} criado com sucesso")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao criar volume: {str(e)}")]

async def handle_volume_remove(args: Dict[str, Any]) -> List[TextContent]:
    """Remove um volume"""
    volume_name = args["volume_name"]
    force = args.get("force", False)
    
    try:
        volume = docker_client.volumes.get(volume_name)
        volume.remove(force=force)
        return [TextContent(type="text", text=f"✅ Volume {volume_name} removido com sucesso")]
    except docker.errors.NotFound:
        return [TextContent(type="text", text=f"❌ Volume '{volume_name}' não encontrado")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao remover volume: {str(e)}")]

async def handle_network_list(args: Dict[str, Any]) -> List[TextContent]:
    """Lista redes"""
    filters = args.get("filters", {})
    
    networks = docker_client.networks.list(filters=filters)
    
    if not networks:
        return [TextContent(type="text", text="Nenhuma rede encontrada")]
    
    result = "## Redes Docker\n\n"
    for network in networks:
        driver = network.attrs.get('Driver', 'desconhecido')
        scope = network.attrs.get('Scope', 'desconhecido')
        created = network.attrs.get('Created', '')[:19] if network.attrs.get('Created') else 'Desconhecido'
        
        result += f"**{network.name}** ({network.short_id})\n"
        result += f"- Driver: {driver}\n"
        result += f"- Scope: {scope}\n"
        result += f"- Criado: {created}\n\n"
    
    return [TextContent(type="text", text=result)]

async def handle_network_create(args: Dict[str, Any]) -> List[TextContent]:
    """Cria uma rede"""
    name = args["name"]
    driver = args.get("driver", "bridge")
    
    try:
        network = docker_client.networks.create(name=name, driver=driver)
        return [TextContent(type="text", text=f"✅ Rede {name} criada com sucesso")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao criar rede: {str(e)}")]

async def handle_network_remove(args: Dict[str, Any]) -> List[TextContent]:
    """Remove uma rede"""
    network_name = args["network_name"]
    
    try:
        network = docker_client.networks.get(network_name)
        network.remove()
        return [TextContent(type="text", text=f"✅ Rede {network_name} removida com sucesso")]
    except docker.errors.NotFound:
        return [TextContent(type="text", text=f"❌ Rede '{network_name}' não encontrada")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao remover rede: {str(e)}")]

async def handle_system_info(args: Dict[str, Any]) -> List[TextContent]:
    """Obtém informações do sistema Docker"""
    try:
        info = docker_client.info()
        
        result = "## Informações do Sistema Docker\n\n"
        result += f"**Versão do Docker:** {info.get('ServerVersion', 'Desconhecida')}\n"
        result += f"**Containers:** {info.get('Containers', 0)} (Rodando: {info.get('ContainersRunning', 0)}, Pausados: {info.get('ContainersPaused', 0)}, Parados: {info.get('ContainersStopped', 0)})\n"
        result += f"**Imagens:** {info.get('Images', 0)}\n"
        result += f"**Driver de Storage:** {info.get('Driver', 'Desconhecido')}\n"
        result += f"**Root Dir:** {info.get('DockerRootDir', 'Desconhecido')}\n"
        result += f"**CPUs:** {info.get('NCPU', 0)}\n"
        result += f"**Memória Total:** {info.get('MemTotal', 0) / 1024 / 1024 / 1024:.2f} GB\n"
        result += f"**Kernel Version:** {info.get('KernelVersion', 'Desconhecida')}\n"
        result += f"**Operating System:** {info.get('OperatingSystem', 'Desconhecido')}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao obter informações do sistema: {str(e)}")]

async def handle_system_df(args: Dict[str, Any]) -> List[TextContent]:
    """Mostra uso de espaço em disco"""
    try:
        df_info = docker_client.df()
        
        result = "## Uso de Espaço em Disco Docker\n\n"
        
        # Images
        images = df_info.get('Images', [])
        total_images_size = sum(img.get('Size', 0) for img in images)
        result += f"**Imagens:** {len(images)} imagens, {total_images_size / 1024 / 1024 / 1024:.2f} GB\n"
        
        # Containers
        containers = df_info.get('Containers', [])
        total_containers_size = sum(cont.get('SizeRw', 0) + cont.get('SizeRootFs', 0) for cont in containers)
        result += f"**Containers:** {len(containers)} containers, {total_containers_size / 1024 / 1024 / 1024:.2f} GB\n"
        
        # Volumes
        volumes = df_info.get('Volumes', [])
        total_volumes_size = sum(vol.get('Size', 0) for vol in volumes if vol.get('Size'))
        result += f"**Volumes:** {len(volumes)} volumes, {total_volumes_size / 1024 / 1024 / 1024:.2f} GB\n"
        
        # Build Cache
        build_cache = df_info.get('BuildCache', [])
        total_cache_size = sum(cache.get('Size', 0) for cache in build_cache)
        result += f"**Build Cache:** {len(build_cache)} entradas, {total_cache_size / 1024 / 1024 / 1024:.2f} GB\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao obter informações de disco: {str(e)}")]

async def handle_system_prune(args: Dict[str, Any]) -> List[TextContent]:
    """Limpa recursos não utilizados"""
    prune_all = args.get("all", False)
    prune_volumes = args.get("volumes", False)
    
    try:
        result = "## Limpeza do Sistema Docker\n\n"
        
        # Prune containers
        container_prune = docker_client.containers.prune()
        result += f"**Containers removidos:** {len(container_prune.get('ContainersDeleted', []))}\n"
        result += f"**Espaço liberado (containers):** {container_prune.get('SpaceReclaimed', 0) / 1024 / 1024:.2f} MB\n\n"
        
        # Prune images
        image_prune = docker_client.images.prune(filters={'dangling': False} if prune_all else {'dangling': True})
        result += f"**Imagens removidas:** {len(image_prune.get('ImagesDeleted', []))}\n"
        result += f"**Espaço liberado (imagens):** {image_prune.get('SpaceReclaimed', 0) / 1024 / 1024:.2f} MB\n\n"
        
        # Prune networks
        network_prune = docker_client.networks.prune()
        result += f"**Redes removidas:** {len(network_prune.get('NetworksDeleted', []))}\n\n"
        
        # Prune volumes if requested
        if prune_volumes:
            volume_prune = docker_client.volumes.prune()
            result += f"**Volumes removidos:** {len(volume_prune.get('VolumesDeleted', []))}\n"
            result += f"**Espaço liberado (volumes):** {volume_prune.get('SpaceReclaimed', 0) / 1024 / 1024:.2f} MB\n\n"
        
        total_space = (
            container_prune.get('SpaceReclaimed', 0) + 
            image_prune.get('SpaceReclaimed', 0) +
            (volume_prune.get('SpaceReclaimed', 0) if prune_volumes else 0)
        )
        result += f"**Total de espaço liberado:** {total_space / 1024 / 1024:.2f} MB\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Erro ao limpar sistema: {str(e)}")]

async def main():
    """Função principal do servidor"""
    # Inicializar cliente Docker
    if not init_docker_client():
        logger.error("Falha ao inicializar cliente Docker. Verifique se o Docker está rodando.")
        sys.exit(1)
    
    # Configurações de transporte
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="docker-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
