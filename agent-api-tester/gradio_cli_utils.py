import subprocess
import os
import requests
import json
import tempfile
import shutil
from pathlib import Path

def download_swagger_from_url(url):
    """
    Baixa especificação Swagger de uma URL e salva em arquivo temporário.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        # Se a resposta for JSON, salvar formatado
        if response.headers.get('content-type', '').startswith('application/json'):
            json_data = response.json()
            json.dump(json_data, temp_file, indent=2)
        else:
            temp_file.write(response.text)
        
        temp_file.close()
        return temp_file.name, None
    except Exception as e:
        return None, f"Erro ao baixar Swagger: {str(e)}"

def save_uploaded_file(file):
    """
    Salva arquivo carregado para um local temporário.
    """
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False)
        shutil.copyfileobj(file, temp_file)
        temp_file.close()
        return temp_file.name, None
    except Exception as e:
        return None, f"Erro ao salvar arquivo: {str(e)}"

def run_cli_generate_tools(swagger_path, base_url=None):
    """
    Executa o comando CLI para gerar tools MCP a partir do arquivo swagger.
    """
    try:
        # Construir comando base
        cmd = ["python3", "-m", "src.api_agent.cli"]
        
        # Adicionar base-url como opção global se fornecida
        if base_url:
            cmd.extend(["--base-url", base_url])
        
        # Adicionar subcomando e arquivo
        cmd.extend(["ingest", "--file", swagger_path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd="/home/john/workspace/bookcase-mcp-v2/agent-api-tester")
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        return None, f"Erro ao executar CLI: {e.stderr or str(e)}"

def run_cli_list_tools():
    """
    Lista as tools MCP disponíveis.
    """
    try:
        cmd = ["python3", "-m", "src.api_agent.cli", "list-tools", "--format", "json"]
        # Usar ambiente sem cores para evitar caracteres de controle
        env = os.environ.copy()
        env["NO_COLOR"] = "1"
        env["TERM"] = "dumb"
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True, 
            cwd="/home/john/workspace/bookcase-mcp-v2/agent-api-tester",
            env=env
        )
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        return None, f"Erro ao listar tools: {e.stderr or str(e)}"

def run_cli_tests(tool_name=None):
    """
    Executa testes automáticos via CLI.
    """
    try:
        cmd = ["python3", "-m", "src.api_agent.cli", "run-tests"]
        if tool_name:
            cmd.extend(["--tool", tool_name])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd="/home/john/workspace/bookcase-mcp-v2/agent-api-tester")
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        return None, f"Erro ao executar testes: {e.stderr or str(e)}"

def format_tools_for_display(tools_json):
    """
    Formata a saída JSON das tools para exibição amigável.
    """
    try:
        if not tools_json.strip():
            return "Nenhuma tool encontrada"
        
        # Limpar e corrigir o JSON
        # Remover caracteres de controle e corrigir quebras de linha em strings
        lines = tools_json.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remover caracteres de controle, mas manter espaços, tabs e quebras de linha
            clean_line = ''.join(char for char in line if ord(char) >= 32 or char in '\r\n\t')
            cleaned_lines.append(clean_line)
        
        # Rejoinar as linhas
        clean_json = '\n'.join(cleaned_lines)
        
        # Tentar corrigir quebras de linha no meio de strings
        import re
        # Corrigir padrão: "text\nID." -> "text ID."
        clean_json = re.sub(r'(\w+)\n(\w+\.?")', r'\1 \2', clean_json)
        
        tools = json.loads(clean_json)
        if not tools:
            return "Nenhuma tool encontrada"
        
        formatted = "🔧 **Tools disponíveis:**\n\n"
        for tool in tools:
            formatted += f"**{tool['name']}** (`{tool['id']}`)\n"
            formatted += f"- Método: {tool['method']}\n"
            formatted += f"- Path: {tool['path']}\n"
            formatted += f"- Descrição: {tool['description']}\n"
            formatted += f"- Auth: {'Sim' if tool['requires_auth'] else 'Não'}\n\n"
        
        return formatted
    except json.JSONDecodeError as e:
        # Se falhar, retornar uma versão simplificada
        try:
            # Tentar extrair apenas os IDs e nomes das tools
            import re
            ids = re.findall(r'"id":\s*"([^"]+)"', tools_json)
            names = re.findall(r'"name":\s*"([^"]+)"', tools_json)
            
            if ids:
                formatted = f"🔧 **{len(ids)} Tools encontradas:**\n\n"
                for i, tool_id in enumerate(ids):
                    name = names[i] if i < len(names) else "Nome não encontrado"
                    formatted += f"- **{name}** (`{tool_id}`)\n"
                return formatted
            else:
                return f"Erro JSON, mas tools detectadas na resposta: {len(tools_json)} caracteres"
                
        except Exception:
            return f"Erro ao decodificar JSON: {str(e)}\nConteúdo recebido: {tools_json[:200]}..."
    except Exception as e:
        return f"Erro ao formatar tools: {str(e)}"
