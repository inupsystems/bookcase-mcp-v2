#!/usr/bin/env python3
"""
Demonstração do MCP Client
Este script demonstra as funcionalidades principais do MCP Client.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_client import MCPClient, MCPConfig, ToolInvocation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_usage():
    """Demonstrar uso básico do MCP Client."""
    print("🚀 Demonstração do MCP Client")
    print("=" * 50)
    
    # 1. Carregar configuração
    config_path = Path(__file__).parent / "examples" / "config.json"
    
    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return
    
    try:
        print(f"📁 Carregando configuração de: {config_path}")
        client = MCPClient.from_config_file(config_path)
        
        # 2. Inicializar cliente
        print("🔧 Inicializando cliente...")
        success = await client.initialize()
        if not success:
            print("❌ Falha na inicialização do cliente")
            return
        
        print("✅ Cliente inicializado com sucesso")
        
        # 3. Conectar aos servidores
        print("\n🔌 Conectando aos servidores MCP...")
        connection_results = await client.connect()
        
        connected_count = sum(1 for success in connection_results.values() if success)
        total_count = len(connection_results)
        
        print(f"📊 Conectado a {connected_count}/{total_count} servidores:")
        for server_name, success in connection_results.items():
            status = "✅ Conectado" if success else "❌ Falhou"
            print(f"  - {server_name}: {status}")
        
        if connected_count == 0:
            print("⚠️  Nenhum servidor conectado. Verificar configuração.")
            return
        
        # 4. Descobrir tools
        print(f"\n🔍 Descobrindo tools dos servidores conectados...")
        tools_by_server = await client.discover_tools()
        
        total_tools = sum(len(tools) for tools in tools_by_server.values())
        print(f"📋 Descobertas {total_tools} tools:")
        
        for server_name, tools in tools_by_server.items():
            if tools:
                print(f"\n  🏷️  {server_name} ({len(tools)} tools):")
                for tool in tools[:3]:  # Show first 3 tools
                    params_count = len(tool.parameters)
                    required_count = sum(1 for p in tool.parameters if p.required)
                    print(f"    - {tool.name}: {tool.description or 'Sem descrição'}")
                    print(f"      Parâmetros: {params_count} total, {required_count} obrigatórios")
                
                if len(tools) > 3:
                    print(f"    ... e mais {len(tools) - 3} tools")
        
        # 5. Executar tool de exemplo (se disponível)
        print(f"\n⚡ Testando execução de tools...")
        
        # Try to find a simple tool to test
        all_tools = client.get_tools()
        
        if all_tools:
            # Find a tool with minimal required parameters
            simple_tools = [tool for tool in all_tools 
                          if len([p for p in tool.parameters if p.required]) <= 2]
            
            if simple_tools:
                test_tool = simple_tools[0]
                print(f"🧪 Testando tool: {test_tool.name}")
                
                try:
                    result = await client.test_tool(test_tool.name)
                    
                    if result.success:
                        print(f"✅ Tool executada com sucesso em {result.execution_time:.2f}s")
                        if result.result:
                            print(f"📤 Resultado: {str(result.result)[:100]}...")
                    else:
                        print(f"❌ Falha na execução: {result.error}")
                        
                except Exception as e:
                    print(f"❌ Erro durante teste: {e}")
            else:
                print("ℹ️  Nenhuma tool simples encontrada para teste")
        
        # 6. Estatísticas finais
        print(f"\n📊 Estatísticas do cliente:")
        stats = client.get_statistics()
        
        print(f"  - Servidores configurados: {stats['config']['servers']}")
        print(f"  - Servidores conectados: {stats['servers']['connected']}")
        print(f"  - Total de tools: {stats['tools'].get('total_tools', 0)}")
        print(f"  - Execuções realizadas: {stats['execution'].get('total_executions', 0)}")
        
        # 7. Health check
        print(f"\n🏥 Verificação de saúde:")
        health = await client.health_check()
        
        healthy_servers = sum(1 for is_healthy in health['servers'].values() if is_healthy)
        print(f"  - Servidores saudáveis: {healthy_servers}/{len(health['servers'])}")
        
        # 8. Limpeza
        print(f"\n🧹 Desconectando...")
        await client.disconnect()
        print("✅ Desconectado de todos os servidores")
        
    except Exception as e:
        logger.error(f"Erro durante demonstração: {e}")
        print(f"❌ Erro: {e}")


async def demo_tool_search():
    """Demonstrar busca e descoberta de tools."""
    print("\n🔍 Demonstração de busca de tools")
    print("=" * 40)
    
    config_path = Path(__file__).parent / "examples" / "config.json"
    
    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado")
        return
    
    try:
        client = MCPClient.from_config_file(config_path)
        await client.initialize()
        await client.connect()
        
        # Search for tools by keyword
        search_terms = ["create", "list", "get", "docker", "memory"]
        
        for term in search_terms:
            results = client.search_tools(term)
            if results:
                print(f"\n🔎 Busca por '{term}': {len(results)} resultados")
                for tool in results[:2]:  # Show first 2 results
                    print(f"  - {tool.name} ({tool.server_name}): {tool.description or 'Sem descrição'}")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Erro na busca: {e}")


async def demo_batch_execution():
    """Demonstrar execução em lote de tools."""
    print("\n⚡ Demonstração de execução em lote")
    print("=" * 40)
    
    config_path = Path(__file__).parent / "examples" / "config.json"
    
    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado")
        return
    
    try:
        client = MCPClient.from_config_file(config_path)
        await client.initialize()
        connection_results = await client.connect()
        
        connected_servers = [name for name, success in connection_results.items() if success]
        
        if not connected_servers:
            print("❌ Nenhum servidor conectado para teste em lote")
            return
        
        # Create batch invocations (using test parameters)
        invocations = []
        
        # Try to create simple invocations for testing
        all_tools = client.get_tools()
        simple_tools = [tool for tool in all_tools 
                       if len([p for p in tool.parameters if p.required]) == 0]
        
        if simple_tools:
            for tool in simple_tools[:3]:  # Test up to 3 tools
                invocation = ToolInvocation(
                    tool_name=tool.name,
                    server_name=tool.server_name,
                    parameters={}
                )
                invocations.append(invocation)
        
        if invocations:
            print(f"🚀 Executando {len(invocations)} tools em paralelo...")
            
            start_time = asyncio.get_event_loop().time()
            results = await client.batch_execute(invocations)
            end_time = asyncio.get_event_loop().time()
            
            successful = sum(1 for result in results if result.success)
            total_time = end_time - start_time
            
            print(f"📊 Resultados:")
            print(f"  - Executadas: {len(results)} tools")
            print(f"  - Sucessos: {successful}")
            print(f"  - Falhas: {len(results) - successful}")
            print(f"  - Tempo total: {total_time:.2f}s")
            
            for result in results:
                status = "✅" if result.success else "❌"
                print(f"  {status} {result.tool_name}: {result.error or 'OK'}")
        else:
            print("ℹ️  Nenhuma tool adequada encontrada para teste em lote")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Erro na execução em lote: {e}")


async def main():
    """Função principal da demonstração."""
    print("🎯 Demonstração Completa do MCP Client")
    print("=" * 60)
    
    # Basic usage demo
    await demo_basic_usage()
    
    # Tool search demo
    await demo_tool_search()
    
    # Batch execution demo
    await demo_batch_execution()
    
    print(f"\n🎉 Demonstração concluída!")
    print("Para usar o CLI, execute:")
    print("  mcp-client --help")
    print("  mcp-client -c examples/config.json status")
    print("  mcp-client -c examples/config.json tools list")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demonstração interrompida pelo usuário")
    except Exception as e:
        logger.error(f"Erro na demonstração: {e}")
        print(f"❌ Erro geral: {e}")
        sys.exit(1)
