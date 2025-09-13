# Agent API Tester - Interface Gradio

Interface web para o Agent API Tester que permite:

## Funcionalidades

✅ **Importação de Swagger**: Via URL ou arquivo JSON/YAML  
✅ **Geração de Tools MCP**: Execução automática do CLI  
✅ **Execução de Testes**: Testes automáticos com monitoramento  
✅ **Status em Tempo Real**: Job assíncrono com atualização automática  
✅ **Resultados Visuais**: Exibição clara de sucessos e falhas  
✅ **Feedback Visual**: Ícones, status e progresso em tempo real  
✅ **Download de Relatórios**: Exportação dos resultados  
✅ **Tratamento de Erros**: Mensagens claras e informativas  
✅ **Interface Responsiva**: Design otimizado para diferentes dispositivos  

## Como usar

1. **Instalar dependências**:
   ```bash
   pip install -r requirements-gradio.txt
   ```

2. **Executar a interface**:
   ```bash
   python gradio_interface.py
   ```

3. **Acessar**: `http://localhost:7860`

## Fluxo de uso

1. **Importar Swagger**: Cole uma URL ou faça upload de um arquivo
2. **Gerar Tools**: Clique em "Importar Swagger" para gerar tools MCP
3. **Executar Testes**: Use o botão "Executar Testes" para iniciar os testes
4. **Monitorar**: Acompanhe o status em tempo real
5. **Visualizar Resultados**: Veja os resultados detalhados
6. **Baixar Relatório**: Exporte os resultados se necessário

## Arquivos

- `gradio_interface.py`: Interface principal
- `gradio_cli_utils.py`: Utilitários para execução do CLI
- `requirements-gradio.txt`: Dependências necessárias
