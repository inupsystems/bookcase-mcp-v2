"""
Gerador de relatórios profissionais para testes de API.
Integra com pytest-html, allure e plotly para criar relatórios visuais ricos.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from jinja2 import Template


class ProfessionalReportGenerator:
    """Gerador de relatórios profissionais para testes de API."""
    
    def __init__(self, results_dir: str = "test_results", reports_dir: str = "reports"):
        self.results_dir = Path(results_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_html_report(self, session_data: Dict) -> str:
        """Gera relatório HTML profissional com gráficos interativos."""
        
        # Template HTML moderno
        html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Testes - Agent API Tester</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {
            --primary-color: #2563eb;
            --success-color: #059669;
            --error-color: #dc2626;
            --warning-color: #d97706;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--bg-secondary);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            background: var(--bg-primary);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: var(--primary-color);
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .header .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-primary);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .success { color: var(--success-color); }
        .error { color: var(--error-color); }
        .warning { color: var(--warning-color); }
        .primary { color: var(--primary-color); }
        
        .chart-section {
            background: var(--bg-primary);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }
        
        .test-results {
            background: var(--bg-primary);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .test-item {
            display: flex;
            align-items: center;
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .test-item:last-child { border-bottom: none; }
        
        .test-status {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            margin-right: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            color: white;
        }
        
        .test-status.success { background: var(--success-color); }
        .test-status.error { background: var(--error-color); }
        
        .test-details {
            flex: 1;
        }
        
        .test-name {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .test-time {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .test-execution-time {
            font-size: 0.9rem;
            color: var(--warning-color);
            font-weight: 500;
        }
        
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding: 1rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Relatório de Testes</h1>
            <div class="subtitle">Agent API Tester - Sessão {{ session_id }}</div>
            <div class="subtitle">{{ start_time }} - {{ end_time }}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value primary">{{ total_tests }}</div>
                <div class="stat-label">Total de Testes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value success">{{ successful_tests }}</div>
                <div class="stat-label">Sucessos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value error">{{ failed_tests }}</div>
                <div class="stat-label">Falhas</div>
            </div>
            <div class="stat-card">
                <div class="stat-value primary">{{ success_rate }}%</div>
                <div class="stat-label">Taxa de Sucesso</div>
            </div>
            <div class="stat-card">
                <div class="stat-value warning">{{ avg_time }}ms</div>
                <div class="stat-label">Tempo Médio</div>
            </div>
            <div class="stat-card">
                <div class="stat-value primary">{{ tools_tested }}</div>
                <div class="stat-label">Tools Testadas</div>
            </div>
        </div>
        
        <div class="chart-section">
            <div class="chart-title">📊 Distribuição dos Resultados</div>
            <div id="results-chart"></div>
        </div>
        
        <div class="chart-section">
            <div class="chart-title">⚡ Performance por Tool</div>
            <div id="performance-chart"></div>
        </div>
        
        <div class="test-results">
            <div class="chart-title">📝 Detalhes dos Testes</div>
            {% for test in test_results %}
            <div class="test-item">
                <div class="test-status {{ 'success' if test.success else 'error' }}">
                    {{ '✓' if test.success else '✗' }}
                </div>
                <div class="test-details">
                    <div class="test-name">{{ test.tool_id }}</div>
                    <div class="test-time">{{ test.timestamp }}</div>
                    {% if test.error %}
                    <div style="color: var(--error-color); font-size: 0.9rem; margin-top: 0.25rem;">
                        Erro: {{ test.error[:100] }}{% if test.error|length > 100 %}...{% endif %}
                    </div>
                    {% endif %}
                </div>
                {% if test.execution_time_ms %}
                <div class="test-execution-time">{{ "%.2f"|format(test.execution_time_ms) }}ms</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            Relatório gerado em {{ report_time }} por Agent API Tester v2.0.0
        </div>
    </div>
    
    <script>
        // Gráfico de pizza - Resultados
        const resultsData = [{
            values: [{{ successful_tests }}, {{ failed_tests }}],
            labels: ['Sucessos', 'Falhas'],
            type: 'pie',
            marker: {
                colors: ['#059669', '#dc2626']
            },
            textinfo: 'label+percent',
            hovertemplate: '%{label}: %{value}<br>%{percent}<extra></extra>'
        }];
        
        const resultsLayout = {
            showlegend: true,
            height: 400,
            margin: { t: 20, b: 20, l: 20, r: 20 }
        };
        
        Plotly.newPlot('results-chart', resultsData, resultsLayout, {responsive: true});
        
        // Gráfico de barras - Performance
        const performanceData = [{
            x: {{ tool_names | tojson }},
            y: {{ tool_times | tojson }},
            type: 'bar',
            marker: {
                color: '#2563eb'
            },
            hovertemplate: '%{x}<br>Tempo médio: %{y:.2f}ms<extra></extra>'
        }];
        
        const performanceLayout = {
            xaxis: { title: 'Tools' },
            yaxis: { title: 'Tempo Médio (ms)' },
            height: 400,
            margin: { t: 20, b: 80, l: 60, r: 20 }
        };
        
        Plotly.newPlot('performance-chart', performanceData, performanceLayout, {responsive: true});
    </script>
</body>
</html>
        """
        
        # Preparar dados para o template
        summary = session_data.get("summary", {})
        performance = summary.get("performance", {})
        tools_summary = summary.get("tools_summary", {})
        
        # Dados para gráficos
        tool_names = list(tools_summary.keys())
        tool_times = [tools_summary[tool].get("avg_time_ms", 0) for tool in tool_names]
        
        template_data = {
            "session_id": session_data.get("session_id", "N/A"),
            "start_time": session_data.get("start_time", "N/A"),
            "end_time": session_data.get("end_time", "Em andamento"),
            "total_tests": summary.get("total_tests", 0),
            "successful_tests": summary.get("successful_tests", 0),
            "failed_tests": summary.get("failed_tests", 0),
            "success_rate": f"{summary.get('success_rate', 0):.1f}",
            "avg_time": f"{performance.get('avg_execution_time_ms', 0):.2f}",
            "tools_tested": summary.get("tools_tested", 0),
            "test_results": session_data.get("test_results", [])[-20:],  # Últimos 20
            "tool_names": tool_names,
            "tool_times": tool_times,
            "report_time": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        # Renderizar template
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        # Salvar arquivo
        report_file = self.reports_dir / f"test_report_{self.timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_file)
    
    def generate_json_report(self, session_data: Dict) -> str:
        """Gera relatório em formato JSON para integração com CI/CD."""
        report_file = self.reports_dir / f"test_report_{self.timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return str(report_file)
    
    def generate_junit_xml(self, session_data: Dict) -> str:
        """Gera relatório em formato JUnit XML para integração com ferramentas de CI."""
        from xml.etree.ElementTree import Element, SubElement, tostring
        import xml.dom.minidom
        
        testsuites = Element('testsuites')
        testsuite = SubElement(testsuites, 'testsuite')
        
        summary = session_data.get("summary", {})
        test_results = session_data.get("test_results", [])
        
        testsuite.set('name', 'Agent API Tests')
        testsuite.set('tests', str(summary.get('total_tests', 0)))
        testsuite.set('failures', str(summary.get('failed_tests', 0)))
        testsuite.set('time', str(summary.get('performance', {}).get('total_execution_time_ms', 0) / 1000))
        
        for test_result in test_results:
            testcase = SubElement(testsuite, 'testcase')
            testcase.set('classname', 'AgentAPITest')
            testcase.set('name', test_result['tool_id'])
            testcase.set('time', str(test_result.get('execution_time_ms', 0) / 1000))
            
            if not test_result['success']:
                failure = SubElement(testcase, 'failure')
                failure.set('message', test_result.get('error', 'Unknown error'))
                failure.text = test_result.get('error', 'Unknown error')
        
        # Salvar XML
        xml_str = xml.dom.minidom.parseString(tostring(testsuites)).toprettyxml(indent="  ")
        report_file = self.reports_dir / f"test_report_{self.timestamp}.xml"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        return str(report_file)
