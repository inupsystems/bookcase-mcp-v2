#!/usr/bin/env python3
"""
Script de teste para o Docker MCP Server
Testa as funcionalidades básicas do servidor
"""

import docker
import json
import sys
import os

def test_docker_connection():
    """Testa conexão com Docker"""
    try:
        client = docker.from_env()
        client.ping()
        print("✅ Conexão com Docker OK")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com Docker: {e}")
        return False

def test_docker_commands():
    """Testa comandos básicos do Docker"""
    try:
        client = docker.from_env()
        
        # Testar listagem de containers
        containers = client.containers.list(all=True)
        print(f"✅ Containers encontrados: {len(containers)}")
        
        # Testar listagem de imagens
        images = client.images.list()
        print(f"✅ Imagens encontradas: {len(images)}")
        
        # Testar listagem de volumes
        volumes = client.volumes.list()
        print(f"✅ Volumes encontrados: {len(volumes)}")
        
        # Testar listagem de redes
        networks = client.networks.list()
        print(f"✅ Redes encontradas: {len(networks)}")
        
        # Testar informações do sistema
        info = client.info()
        print(f"✅ Docker Version: {info.get('ServerVersion', 'Desconhecida')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar comandos Docker: {e}")
        return False

def test_mcp_imports():
    """Testa se as dependências MCP estão instaladas"""
    try:
        import mcp
        from mcp.server import Server
        from mcp.types import Tool, TextContent
        print("✅ Dependências MCP OK")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar MCP: {e}")
        print("   Execute: pip install -r requirements.txt")
        return False

def main():
    """Função principal de teste"""
    print("🧪 Testando Docker MCP Server...\n")
    
    tests = [
        ("Dependências MCP", test_mcp_imports),
        ("Conexão Docker", test_docker_connection),
        ("Comandos Docker", test_docker_commands)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}:")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! O servidor está pronto para uso.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique as mensagens de erro acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

