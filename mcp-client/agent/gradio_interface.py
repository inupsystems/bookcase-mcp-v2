"""
Interface Gradio para o Agent Tester
Interface web para executar testes automatizados usando DeepSeek + MCP
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gradio as gr

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from deepseek_mcp_agent import DeepSeekMCPAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentTesterUI:
    """Interface Gradio para o Agent Tester."""
    
    def __init__(self):
        self.agent = None
        self.is_initialized = False
        self.conversation_history = []
        
    async def initialize_agent(self, api_key: str) -> Tuple[str, bool]:
        """
        Inicializa o agent com a chave da API.
        
        Returns:
            Tupla com (mensagem_status, sucesso)
        """
        try:
            if not api_key.strip():
                return "❌ Por favor, forneça uma chave de API válida", False
            
            config_path = str(Path(__file__).parent.parent / "examples" / "config.json")
            
            if not Path(config_path).exists():
                return f"❌ Arquivo de configuração não encontrado: {config_path}", False
            
            self.agent = DeepSeekMCPAgent(api_key.strip(), config_path)
            
            success = await self.agent.initialize()
            
            if success:
                self.is_initialized = True
                tools_count = len(self.agent.available_tools)
                return f"✅ Agent inicializado com sucesso!\n🔧 {tools_count} ferramentas disponíveis", True
            else:
                return "❌ Falha na inicialização do agent", False
                
        except Exception as e:
            logger.error(f"Erro na inicialização: {e}")
            return f"❌ Erro: {str(e)}", False
    
    async def send_message(self, message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """
        Envia mensagem para o agent e retorna a resposta.
        
        Args:
            message: Mensagem do usuário
            history: Histórico da conversa
            
        Returns:
            Tupla com (resposta, histórico_atualizado)
        """
        try:
            if not self.is_initialized or not self.agent:
                return "", history + [[message, "❌ Agent não inicializado. Configure a API key primeiro."]]
            
            if not message.strip():
                return "", history
            
            # Processar mensagem
            response = await self.agent.process_request(message.strip())
            
            # Atualizar histórico
            updated_history = history + [[message, response]]
            
            return "", updated_history
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {e}")
            error_response = f"❌ Erro no processamento: {str(e)}"
            return "", history + [[message, error_response]]
    
    def get_available_tools(self) -> str:
        """Retorna lista das ferramentas disponíveis."""
        if not self.is_initialized or not self.agent:
            return "Agent não inicializado"
        
        return self.agent.get_tools_description()
    
    def get_quick_test_examples(self) -> List[str]:
        """Retorna exemplos de testes rápidos."""
        return [
            "Liste as ferramentas disponíveis",
            "Execute um teste GET na API https://jsonplaceholder.typicode.com/posts/1",
            "Teste se o servidor de memória está funcionando",
            "Salve um resultado de teste no histórico",
            "Mostre o histórico de testes do projeto 'agent-tester'",
            "Execute um teste POST para criar um novo carrier",
            "Verifique a conectividade com o Docker",
            "Teste de busca global no mongo-dev-memory"
        ]
    
    async def run_quick_test(self, test_type: str) -> str:
        """
        Executa um teste rápido predefinido.
        
        Args:
            test_type: Tipo de teste a executar
            
        Returns:
            Resultado do teste
        """
        if not self.is_initialized or not self.agent:
            return "❌ Agent não inicializado"
        
        test_messages = {
            "Conectividade": "Verifique se todas as ferramentas MCP estão conectadas e funcionando",
            "API Básica": "Execute um teste GET simples na API https://jsonplaceholder.typicode.com/posts/1",
            "Memória": "Teste a funcionalidade de salvar e recuperar dados do mongo-dev-memory",
            "Docker": "Verifique se o Docker está funcionando e liste os containers",
            "Histórico": "Mostre o histórico de testes salvos no projeto 'agent-tester'"
        }
        
        message = test_messages.get(test_type, "Liste as ferramentas disponíveis")
        return await self.agent.process_request(message)
    
    def create_interface(self) -> gr.Interface:
        """Cria a interface Gradio."""
        
        with gr.Blocks(
            title="Agent Tester - DeepSeek + MCP",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
            }
            .chat-container {
                height: 600px !important;
            }
            """
        ) as interface:
            
            gr.Markdown("""
            # 🤖 Agent Tester - DeepSeek + MCP
            
            Sistema automatizado de testes usando DeepSeek AI e ferramentas MCP.
            Configure sua API key e comece a executar testes inteligentes!
            """)
            
            with gr.Tab("💬 Chat"):
                with gr.Row():
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            height=600,
                            container=True,
                            elem_classes=["chat-container"]
                        )
                        
                        with gr.Row():
                            msg_input = gr.Textbox(
                                placeholder="Digite sua solicitação de teste...",
                                lines=2,
                                max_lines=5,
                                scale=4
                            )
                            send_btn = gr.Button("Enviar", variant="primary", scale=1)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### ⚙️ Configuração")
                        
                        api_key_input = gr.Textbox(
                            label="DeepSeek API Key",
                            type="password",
                            placeholder="sk-..."
                        )
                        
                        init_btn = gr.Button("Inicializar Agent", variant="secondary")
                        status_text = gr.Textbox(
                            label="Status",
                            interactive=False,
                            lines=3
                        )
                        
                        gr.Markdown("### 📋 Exemplos Rápidos")
                        
                        example_dropdown = gr.Dropdown(
                            choices=self.get_quick_test_examples(),
                            label="Selecione um exemplo",
                            interactive=True
                        )
                        
                        use_example_btn = gr.Button("Usar Exemplo", variant="secondary")
            
            with gr.Tab("🔧 Ferramentas"):
                tools_display = gr.Textbox(
                    label="Ferramentas Disponíveis",
                    lines=20,
                    interactive=False
                )
                
                refresh_tools_btn = gr.Button("Atualizar Lista", variant="secondary")
            
            with gr.Tab("⚡ Testes Rápidos"):
                gr.Markdown("### Testes Predefinidos")
                
                with gr.Row():
                    test_type = gr.Radio(
                        choices=["Conectividade", "API Básica", "Memória", "Docker", "Histórico"],
                        label="Tipo de Teste",
                        value="Conectividade"
                    )
                
                run_test_btn = gr.Button("Executar Teste", variant="primary")
                test_result = gr.Textbox(
                    label="Resultado do Teste",
                    lines=15,
                    interactive=False
                )
            
            with gr.Tab("ℹ️ Ajuda"):
                gr.Markdown("""
                ## Como usar o Agent Tester
                
                ### 1. Configuração Inicial
                - Insira sua chave da API do DeepSeek
                - Clique em "Inicializar Agent"
                - Aguarde a confirmação de inicialização
                
                ### 2. Executando Testes
                
                #### Via Chat:
                - Digite solicitações em linguagem natural
                - Exemplo: "Teste a API de posts do JSONPlaceholder"
                - Exemplo: "Salve um resultado de teste no histórico"
                
                #### Via Testes Rápidos:
                - Selecione um tipo de teste predefinido
                - Clique em "Executar Teste"
                
                ### 3. Comandos Úteis
                
                - **"Liste as ferramentas disponíveis"** - Mostra todas as ferramentas MCP
                - **"Execute um teste GET em [URL]"** - Testa endpoint HTTP
                - **"Salve no histórico [dados]"** - Armazena resultado no MongoDB
                - **"Mostre o histórico do projeto [nome]"** - Recupera histórico salvo
                
                ### 4. Ferramentas Disponíveis
                
                - **agent-api-tester**: Testes de API HTTP
                - **mongo-dev-memory**: Armazenamento de histórico
                - **memory**: Memória temporária
                - **docker**: Gerenciamento de containers
                - **sequentialthinking**: Raciocínio estruturado
                
                ### 5. Dicas
                
                - Seja específico nas solicitações
                - Use linguagem natural - o AI entende contexto
                - Combine múltiplas ferramentas em uma solicitação
                - Verifique o status de inicialização antes de usar
                """)
            
            # Event handlers
            async def handle_init(api_key):
                message, success = await self.initialize_agent(api_key)
                return message
            
            async def handle_send(message, history):
                return await self.send_message(message, history)
            
            def handle_example(example):
                return example
            
            def handle_tools_refresh():
                return self.get_available_tools()
            
            async def handle_quick_test(test_type):
                return await self.run_quick_test(test_type)
            
            # Connect events
            init_btn.click(
                handle_init,
                inputs=[api_key_input],
                outputs=[status_text]
            )
            
            send_btn.click(
                handle_send,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            msg_input.submit(
                handle_send,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            use_example_btn.click(
                handle_example,
                inputs=[example_dropdown],
                outputs=[msg_input]
            )
            
            refresh_tools_btn.click(
                handle_tools_refresh,
                outputs=[tools_display]
            )
            
            run_test_btn.click(
                handle_quick_test,
                inputs=[test_type],
                outputs=[test_result]
            )
        
        return interface


def main():
    """Função principal para executar a interface."""
    print("🚀 Iniciando Agent Tester UI...")
    
    ui = AgentTesterUI()
    interface = ui.create_interface()
    
    # Executar interface
    interface.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        debug=True,
        show_error=True
    )


if __name__ == "__main__":
    main()
