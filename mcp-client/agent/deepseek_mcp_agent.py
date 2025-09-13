"""
Agent Tester - Sistema integrado DeepSeek + MCP Client
Sistema para executar testes automatizados usando IA e ferramentas MCP
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path to import mcp_client
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai import OpenAI
from mcp_client import MCPClient, MCPConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeepSeekMCPAgent:
    """Agent que integra DeepSeek AI com MCP Client para testes automatizados."""
    
    def __init__(self, api_key: str, config_path: str):
        """
        Inicializa o agent.
        
        Args:
            api_key: Chave da API do DeepSeek
            config_path: Caminho para o arquivo de configuração MCP
        """
        self.api_key = api_key
        self.config_path = config_path
        
        # Inicializar cliente DeepSeek
        self.deepseek_client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # Inicializar MCP Client
        self.mcp_client = None
        self.available_tools = {}
        
        # Sistema de prompt
        self.system_prompt = self._create_system_prompt()
        
        # Histórico de conversas
        self.conversation_history = []
        
    def _create_system_prompt(self) -> str:
        """Cria o prompt de sistema para o agent."""
        return """Você é um Agent Tester especializado em executar testes automatizados usando ferramentas MCP.

SUAS CAPACIDADES:
- Executar testes de API usando ferramentas do agent-api-tester
- Salvar resultados de testes no mongo-dev-memory **quando solicitado**
- Analisar e interpretar resultados de testes
- Sugerir melhorias e correções
- Fornecer relatórios claros e concisos

FERRAMENTAS DISPONÍVEIS:
Você tem acesso a várias ferramentas MCP que podem incluir:
- agent-api-tester: Para testes de API (GET, POST, etc.)
- mongo-dev-memory: Para salvar histórico de testes
- memory: Para armazenar informações temporárias

INSTRUÇÕES:
1. Quando receber uma solicitação de teste, primeiro identifique que tipo de teste é necessário
2. Use as ferramentas apropriadas para executar o teste
3. Analise os resultados
4. Salve o histórico no mongo-dev-memory se solicitado
5. Forneça um relatório claro dos resultados

FORMATO DE RESPOSTA:
- Seja claro e objetivo
- Explique que ferramentas você vai usar
- Mostre os resultados dos testes
- Indique se houve sucesso ou falha
- Sugira próximos passos se necessário

Quando você precisar executar uma ferramenta, indique claramente:
FERRAMENTA: nome_da_ferramenta
PARÂMETROS: {parâmetros em JSON}
MOTIVO: explicação do por que está usando esta ferramenta"""

    async def initialize(self) -> bool:
        """Inicializa o MCP Client e carrega as ferramentas disponíveis."""
        try:
            logger.info("Inicializando MCP Client...")
            
            # Carregar configuração
            config = MCPConfig.from_file(self.config_path)
            self.mcp_client = MCPClient(config)
            
            # Inicializar e conectar
            await self.mcp_client.initialize()
            connection_results = await self.mcp_client.connect()
            
            # Verificar conexões bem-sucedidas
            connected_servers = [
                name for name, success in connection_results.items() if success
            ]
            
            if not connected_servers:
                logger.error("Nenhum servidor MCP conectado")
                return False
            
            logger.info(f"Conectado aos servidores: {connected_servers}")
            
            # Descobrir ferramentas
            tools_by_server = await self.mcp_client.discover_tools()
            
            # Organizar ferramentas por nome
            for server_name, tools in tools_by_server.items():
                for tool in tools:
                    tool_key = f"{server_name}:{tool.name}"
                    self.available_tools[tool_key] = {
                        'server': server_name,
                        'tool': tool,
                        'name': tool.name,
                        'description': tool.description or 'Sem descrição',
                        'parameters': [
                            {
                                'name': p.name,
                                'type': p.type,
                                'required': p.required,
                                'description': p.description or ''
                            }
                            for p in tool.parameters
                        ]
                    }
            
            logger.info(f"Ferramentas descobertas: {len(self.available_tools)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização: {e}")
            return False
    
    def get_tools_description(self) -> str:
        """Retorna descrição das ferramentas disponíveis."""
        if not self.available_tools:
            return "Nenhuma ferramenta disponível."
        
        description = "FERRAMENTAS DISPONÍVEIS:\n\n"
        
        for tool_key, tool_info in self.available_tools.items():
            description += f"🔧 {tool_info['name']} ({tool_info['server']})\n"
            description += f"   Descrição: {tool_info['description']}\n"
            
            if tool_info['parameters']:
                description += "   Parâmetros:\n"
                for param in tool_info['parameters']:
                    required = " (obrigatório)" if param['required'] else " (opcional)"
                    description += f"     - {param['name']} ({param['type']}){required}: {param['description']}\n"
            else:
                description += "   Sem parâmetros\n"
            
            description += "\n"
        
        return description
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                          server_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa uma ferramenta MCP.
        
        Args:
            tool_name: Nome da ferramenta
            parameters: Parâmetros para a ferramenta
            server_name: Nome do servidor (opcional)
            
        Returns:
            Resultado da execução
        """
        try:
            if not self.mcp_client:
                return {
                    'success': False,
                    'error': 'MCP Client não inicializado'
                }
            
            logger.info(f"Executando ferramenta: {tool_name} com parâmetros: {parameters}")
            
            result = await self.mcp_client.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                server_name=server_name
            )
            
            return {
                'success': result.success,
                'result': result.result,
                'error': result.error,
                'execution_time': result.execution_time,
                'server_name': result.server_name,
                'timestamp': result.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na execução da ferramenta: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def process_request(self, user_message: str) -> str:
        """
        Processa uma solicitação do usuário usando DeepSeek AI.
        
        Args:
            user_message: Mensagem do usuário
            
        Returns:
            Resposta do agent
        """
        try:
            # Adicionar informações sobre ferramentas disponíveis ao contexto
            tools_info = self.get_tools_description()
            
            # Construir histórico da conversa
            messages = [
                {"role": "system", "content": f"{self.system_prompt}\n\n{tools_info}"}
            ]
            
            # Adicionar histórico de conversas
            for msg in self.conversation_history[-10:]:  # Últimas 10 mensagens
                messages.append(msg)
            
            # Adicionar mensagem atual
            messages.append({"role": "user", "content": user_message})
            
            logger.info("Enviando solicitação para DeepSeek...")
            
            # Chamar DeepSeek
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Processar resposta para identificar chamadas de ferramentas
            processed_response = await self._process_ai_response(ai_response)
            
            # Adicionar ao histórico
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": processed_response})
            
            return processed_response
            
        except Exception as e:
            logger.error(f"Erro no processamento da solicitação: {e}")
            return f"❌ Erro no processamento: {str(e)}"
    
    async def _process_ai_response(self, ai_response: str) -> str:
        """
        Processa a resposta da IA para identificar e executar chamadas de ferramentas.
        
        Args:
            ai_response: Resposta da IA
            
        Returns:
            Resposta processada com resultados das ferramentas
        """
        processed_response = ai_response
        
        # Procurar por indicações de uso de ferramentas
        if "FERRAMENTA:" in ai_response and "PARÂMETROS:" in ai_response:
            lines = ai_response.split('\n')
            
            tool_name = None
            parameters = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                if line.startswith("FERRAMENTA:"):
                    tool_name = line.replace("FERRAMENTA:", "").strip()
                
                elif line.startswith("PARÂMETROS:"):
                    params_text = line.replace("PARÂMETROS:", "").strip()
                    try:
                        parameters = json.loads(params_text)
                    except json.JSONDecodeError:
                        # Tentar pegar parâmetros da próxima linha se necessário
                        if i + 1 < len(lines):
                            try:
                                parameters = json.loads(lines[i + 1].strip())
                            except:
                                parameters = {}
            
            # Executar ferramenta se identificada
            if tool_name and parameters is not None:
                logger.info(f"Executando ferramenta identificada: {tool_name}")
                
                result = await self.execute_tool(tool_name, parameters)
                
                # Adicionar resultado à resposta
                processed_response += f"\n\n🔧 **EXECUÇÃO DA FERRAMENTA**\n"
                processed_response += f"Ferramenta: {tool_name}\n"
                processed_response += f"Parâmetros: {json.dumps(parameters, indent=2)}\n"
                
                if result['success']:
                    processed_response += f"✅ **SUCESSO** (tempo: {result.get('execution_time', 0):.2f}s)\n"
                    processed_response += f"Resultado:\n```json\n{json.dumps(result['result'], indent=2)}\n```"
                else:
                    processed_response += f"❌ **ERRO**: {result['error']}"
        
        return processed_response
    
    async def save_test_result(self, test_name: str, result: Dict[str, Any]) -> bool:
        """
        Salva resultado de teste no mongo-dev-memory.
        
        Args:
            test_name: Nome do teste
            result: Resultado do teste
            
        Returns:
            True se salvou com sucesso
        """
        try:
            # Tentar salvar no mongo-dev-memory
            save_result = await self.execute_tool(
                tool_name="mongo_insert_historico",
                parameters={
                    "project_id": "agent-tester",
                    "task_description": test_name,
                    "context": json.dumps(result),
                    "status": "completed" if result.get('success') else "failed",
                    "technologies": ["API", "MCP", "DeepSeek"]
                },
                server_name="mongo-dev-memory"
            )
            
            return save_result['success']
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultado: {e}")
            return False
    
    async def cleanup(self):
        """Limpa recursos do agent."""
        if self.mcp_client:
            await self.mcp_client.disconnect()
            logger.info("Agent desconectado")


# Função para teste independente
async def test_agent():
    """Testa o agent independentemente."""
    api_key = "sk-61fc548eca5946359d33520127d80cbe"
    config_path = "../examples/config.json"
    
    agent = DeepSeekMCPAgent(api_key, config_path)
    
    try:
        # Inicializar
        success = await agent.initialize()
        if not success:
            print("❌ Falha na inicialização")
            return
        
        print("✅ Agent inicializado com sucesso")
        print(f"Ferramentas disponíveis: {len(agent.available_tools)}")
        
        # Teste simples
        response = await agent.process_request(
            "Liste as ferramentas disponíveis e suas funcionalidades"
        )
        
        print("\n📝 Resposta do Agent:")
        print(response)
        
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(test_agent())
