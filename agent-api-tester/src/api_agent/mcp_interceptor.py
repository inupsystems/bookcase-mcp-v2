"""
Wrapper global para interceptar e monitorar chamadas MCP.
Garante que todos os testes sejam capturados independentemente da origem.
"""

import functools
import inspect
import time
from typing import Any, Callable, Dict, Optional
from .test_monitor import TestResultsMonitor


class MCPTestInterceptor:
    """Interceptador global para monitorar chamadas de ferramentas MCP."""
    
    def __init__(self):
        self.monitor = TestResultsMonitor.get_global_instance()
        self.active = True
    
    def intercept_tool_call(self, tool_name: str):
        """Decorator para interceptar chamadas de ferramentas MCP."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.active:
                    return await func(*args, **kwargs)
                
                start_time = time.time()
                success = False
                error = None
                result = None
                
                try:
                    # Extrair inputs dos argumentos
                    inputs = self._extract_inputs(func, args, kwargs)
                    
                    # Executar função original
                    result = await func(*args, **kwargs)
                    success = True
                    
                    # Extrair outputs do resultado
                    outputs = self._extract_outputs(result)
                    
                except Exception as e:
                    error = str(e)
                    outputs = {}
                    raise  # Re-raise para não quebrar o fluxo
                finally:
                    # Registrar no monitor
                    execution_time = (time.time() - start_time) * 1000
                    self.monitor.log_tool_invocation(
                        tool_id=tool_name,
                        inputs=inputs,
                        outputs=outputs,
                        success=success,
                        error=error,
                        execution_time=execution_time
                    )
                
                return result
            
            return wrapper
        return decorator
    
    def _extract_inputs(self, func: Callable, args: tuple, kwargs: dict) -> Dict:
        """Extrai inputs dos argumentos da função."""
        try:
            # Obter assinatura da função
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Converter para dict serializável
            inputs = {}
            for name, value in bound_args.arguments.items():
                if isinstance(value, (str, int, float, bool, dict, list, type(None))):
                    inputs[name] = value
                else:
                    inputs[name] = str(value)
            
            return inputs
        except Exception:
            return {"args": str(args), "kwargs": str(kwargs)}
    
    def _extract_outputs(self, result: Any) -> Dict:
        """Extrai outputs do resultado."""
        try:
            if hasattr(result, '__dict__'):
                # Se é um objeto, converter para dict
                return {k: v for k, v in result.__dict__.items() 
                       if isinstance(v, (str, int, float, bool, dict, list, type(None)))}
            elif isinstance(result, (dict, list, str, int, float, bool, type(None))):
                return {"result": result}
            else:
                return {"result": str(result)}
        except Exception:
            return {"result": str(result)}
    
    def enable(self):
        """Ativa o interceptador."""
        self.active = True
    
    def disable(self):
        """Desativa o interceptador."""
        self.active = False


# Instância global do interceptador
global_interceptor = MCPTestInterceptor()


def mcp_tool_monitor(tool_name: str):
    """Decorator para monitorar ferramentas MCP."""
    return global_interceptor.intercept_tool_call(tool_name)


def enable_monitoring():
    """Ativa o monitoramento global."""
    global_interceptor.enable()


def disable_monitoring():
    """Desativa o monitoramento global."""
    global_interceptor.disable()


def get_monitor_instance():
    """Retorna a instância do monitor."""
    return global_interceptor.monitor
