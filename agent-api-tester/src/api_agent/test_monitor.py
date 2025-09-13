import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class TestResultsMonitor:
    """Monitora e armazena resultados de testes executados via agent/IA."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, results_dir: str = "test_results"):
        """Implementa singleton para garantir sessão global única."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TestResultsMonitor, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, results_dir: str = "test_results"):
        if self._initialized:
            return
            
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.session_file = self.results_dir / f"session_{int(time.time())}.json"
        self.session_data = {
            "session_id": int(time.time()),
            "start_time": datetime.now().isoformat(),
            "status": "active",
            "tools_tested": [],
            "test_results": [],
            "summary": {},
            "metadata": {
                "version": "2.0.0",
                "created_by": "agent-api-tester",
                "session_type": "global"
            }
        }
        self._save_session()
        self._initialized = True
    
    @classmethod
    def get_global_instance(cls, results_dir: str = "test_results"):
        """Retorna a instância global do monitor."""
        return cls(results_dir)
    
    @classmethod  
    def reset_session(cls, results_dir: str = "test_results"):
        """Reseta a sessão global (usado para testes)."""
        with cls._lock:
            if cls._instance:
                cls._instance._initialized = False
            cls._instance = None
        return cls(results_dir)
    
    def _save_session(self):
        """Salva dados da sessão no arquivo."""
        # Note: assumes lock is already acquired by caller
        with open(self.session_file, 'w') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
    
    def start_monitoring(self):
        """Inicia o monitoramento de testes."""
        with self._lock:
            self.session_data["status"] = "running"
            self.session_data["start_time"] = datetime.now().isoformat()
            self._save_session()
    
    def log_tool_invocation(self, tool_name: str = None, tool_id: str = None, 
                           arguments: Dict = None, inputs: Dict = None, 
                           outputs: Dict = None, result: Dict = None,
                           success: bool = True, error: Optional[str] = None,
                           execution_time: Optional[float] = None, response_time: Optional[float] = None,
                           http_status: Optional[int] = None, endpoint: Optional[str] = None):
        """Registra uma invocação de tool pelo agent."""
        with self._lock:
            # Unifica parâmetros para compatibilidade
            final_tool_id = tool_name or tool_id or "unknown_tool"
            final_inputs = arguments or inputs or {}
            final_outputs = result or outputs or {}
            final_execution_time = response_time or execution_time
            
            result_entry = {
                "timestamp": datetime.now().isoformat(),
                "tool_id": final_tool_id,
                "tool_name": final_tool_id,
                "inputs": final_inputs,
                "outputs": final_outputs,
                "success": success,
                "error": error,
                "execution_time_ms": final_execution_time * 1000 if final_execution_time else None,
                "response_time_seconds": final_execution_time,
                "http_status": http_status,
                "endpoint": endpoint,
                "test_id": f"{final_tool_id}_{int(time.time() * 1000)}"
            }
            
            self.session_data["test_results"].append(result_entry)
            
            # Atualizar lista de tools testadas
            if final_tool_id not in self.session_data["tools_tested"]:
                self.session_data["tools_tested"].append(final_tool_id)
            
            # Atualizar status para running se não estava
            if self.session_data["status"] == "active":
                self.session_data["status"] = "running"
            
            self._save_session()
            return result_entry
    
    def finish_monitoring(self):
        """Finaliza o monitoramento e gera sumário."""
        with self._lock:
            self.session_data["status"] = "completed"
            self.session_data["end_time"] = datetime.now().isoformat()
            
            # Gerar sumário
            total_tests = len(self.session_data["test_results"])
            successful_tests = sum(1 for r in self.session_data["test_results"] if r["success"])
            failed_tests = total_tests - successful_tests
            
            tools_summary = {}
            execution_times = []
            
            for result in self.session_data["test_results"]:
                tool_id = result["tool_id"]
                if tool_id not in tools_summary:
                    tools_summary[tool_id] = {
                        "total": 0, 
                        "success": 0, 
                        "failed": 0,
                        "avg_time_ms": 0,
                        "min_time_ms": float('inf'),
                        "max_time_ms": 0
                    }
                
                tools_summary[tool_id]["total"] += 1
                if result["success"]:
                    tools_summary[tool_id]["success"] += 1
                else:
                    tools_summary[tool_id]["failed"] += 1
                
                # Calcular métricas de tempo
                if result.get("execution_time_ms"):
                    exec_time = result["execution_time_ms"]
                    execution_times.append(exec_time)
                    tools_summary[tool_id]["min_time_ms"] = min(tools_summary[tool_id]["min_time_ms"], exec_time)
                    tools_summary[tool_id]["max_time_ms"] = max(tools_summary[tool_id]["max_time_ms"], exec_time)
            
            # Calcular médias de tempo por tool
            for tool_id in tools_summary:
                tool_times = [r["execution_time_ms"] for r in self.session_data["test_results"] 
                             if r["tool_id"] == tool_id and r.get("execution_time_ms")]
                if tool_times:
                    tools_summary[tool_id]["avg_time_ms"] = sum(tool_times) / len(tool_times)
                else:
                    tools_summary[tool_id]["min_time_ms"] = 0
            
            self.session_data["summary"] = {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                "tools_tested": len(self.session_data["tools_tested"]),
                "tools_summary": tools_summary,
                "performance": {
                    "avg_execution_time_ms": sum(execution_times) / len(execution_times) if execution_times else 0,
                    "min_execution_time_ms": min(execution_times) if execution_times else 0,
                    "max_execution_time_ms": max(execution_times) if execution_times else 0,
                    "total_execution_time_ms": sum(execution_times) if execution_times else 0
                }
            }
            
            self._save_session()
    
    def get_current_status(self) -> Dict:
        """Retorna o status atual da sessão."""
        with self._lock:
            # Garantir que os campos existem e são do tipo correto
            test_results = self.session_data.get("test_results", [])
            tools_tested = self.session_data.get("tools_tested", [])
            
            # Garantir que são listas
            if not isinstance(test_results, list):
                test_results = []
                self.session_data["test_results"] = test_results
            
            if not isinstance(tools_tested, list):
                tools_tested = []
                self.session_data["tools_tested"] = tools_tested
            
            return {
                **self.session_data,  # Retorna todos os dados da sessão
                "total_tests": len(test_results),
                "tools_tested_count": len(tools_tested),
                "latest_results": test_results[-5:] if test_results else []
            }
    
    def get_formatted_results(self) -> str:
        """Retorna resultados formatados para exibição."""
        with self._lock:
            if not self.session_data["test_results"]:
                return "🔄 Aguardando testes do agent..."
            
            summary = self.session_data.get("summary", {})
            performance = summary.get("performance", {})
            results = []
            
            results.append("📊 **RELATÓRIO DE TESTES - AGENT API TESTER**")
            results.append("=" * 50)
            results.append(f"📅 **Sessão**: {self.session_data.get('session_id', 'N/A')}")
            results.append(f"🕐 **Início**: {self.session_data.get('start_time', 'N/A')}")
            if self.session_data.get('end_time'):
                results.append(f"🕐 **Fim**: {self.session_data.get('end_time', 'N/A')}")
            results.append(f"📊 **Status**: {self.session_data.get('status', 'N/A').upper()}")
            results.append("")
            
            results.append("📈 **RESUMO GERAL:**")
            results.append(f"- **Total de testes**: {summary.get('total_tests', 0)}")
            results.append(f"- **✅ Sucessos**: {summary.get('successful_tests', 0)}")
            results.append(f"- **❌ Falhas**: {summary.get('failed_tests', 0)}")
            results.append(f"- **📊 Taxa de sucesso**: {summary.get('success_rate', 0):.1f}%")
            results.append(f"- **🔧 Tools testadas**: {summary.get('tools_tested', 0)}")
            results.append("")
            
            if performance:
                results.append("⚡ **PERFORMANCE:**")
                results.append(f"- **Tempo médio**: {performance.get('avg_execution_time_ms', 0):.2f}ms")
                results.append(f"- **Tempo mínimo**: {performance.get('min_execution_time_ms', 0):.2f}ms")
                results.append(f"- **Tempo máximo**: {performance.get('max_execution_time_ms', 0):.2f}ms")
                results.append(f"- **Tempo total**: {performance.get('total_execution_time_ms', 0):.2f}ms")
                results.append("")
            
            results.append("🔧 **RESUMO POR TOOL:**")
            tools_summary = summary.get("tools_summary", {})
            for tool_id, stats in tools_summary.items():
                success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
                avg_time = stats.get("avg_time_ms", 0)
                results.append(f"- **{tool_id}**:")
                results.append(f"  - Testes: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
                if avg_time > 0:
                    results.append(f"  - Tempo médio: {avg_time:.2f}ms")
            
            results.append("")
            results.append("📝 **ÚLTIMOS TESTES (5 mais recentes):**")
            for result in self.session_data["test_results"][-5:]:
                status = "✅" if result["success"] else "❌"
                timestamp = result["timestamp"].split("T")[1].split(".")[0]
                exec_time = f" ({result.get('execution_time_ms', 0):.1f}ms)" if result.get('execution_time_ms') else ""
                results.append(f"{status} {timestamp} - **{result['tool_id']}**{exec_time}")
                if not result["success"] and result["error"]:
                    error_msg = result['error'][:100] + "..." if len(result['error']) > 100 else result['error']
                    results.append(f"   💥 **Erro**: {error_msg}")
            
            return "\n".join(results)
    
    def export_reports(self) -> Dict[str, str]:
        """Exporta relatórios em múltiplos formatos."""
        try:
            from .professional_reports import ProfessionalReportGenerator
            
            generator = ProfessionalReportGenerator()
            reports = {}
            
            # Gerar relatórios
            reports['html'] = generator.generate_html_report(self.session_data)
            reports['json'] = generator.generate_json_report(self.session_data)
            reports['junit_xml'] = generator.generate_junit_xml(self.session_data)
            
            return reports
        except Exception as e:
            return {"error": f"Erro ao gerar relatórios: {str(e)}"}
    
    def get_dashboard_data(self) -> Dict:
        """Retorna dados formatados para dashboard em tempo real."""
        with self._lock:
            summary = self.session_data.get("summary", {})
            performance = summary.get("performance", {})
            
            # Estatísticas em tempo real
            recent_tests = self.session_data["test_results"][-10:] if self.session_data["test_results"] else []
            
            return {
                "session_info": {
                    "id": self.session_data.get("session_id"),
                    "status": self.session_data.get("status"),
                    "start_time": self.session_data.get("start_time"),
                    "end_time": self.session_data.get("end_time")
                },
                "metrics": {
                    "total_tests": len(self.session_data["test_results"]),
                    "successful_tests": sum(1 for r in self.session_data["test_results"] if r["success"]),
                    "failed_tests": sum(1 for r in self.session_data["test_results"] if not r["success"]),
                    "success_rate": summary.get("success_rate", 0),
                    "tools_tested": len(self.session_data["tools_tested"]),
                    "avg_execution_time": performance.get("avg_execution_time_ms", 0)
                },
                "recent_tests": recent_tests,
                "tools_summary": summary.get("tools_summary", {}),
                "performance": performance
            }
    
    @classmethod
    def get_latest_session(cls, results_dir: str = "test_results") -> Optional["TestResultsMonitor"]:
        """Recupera a sessão mais recente."""
        results_path = Path(results_dir)
        if not results_path.exists():
            return None
        
        session_files = list(results_path.glob("session_*.json"))
        if not session_files:
            return None
        
        latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
        
        monitor = cls.__new__(cls)
        monitor.results_dir = results_path
        monitor.session_file = latest_file
        
        try:
            with open(latest_file, 'r') as f:
                monitor.session_data = json.load(f)
            return monitor
        except Exception:
            return None
