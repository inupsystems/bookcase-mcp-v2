"""Command Line Interface for API-Agent."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

from .swagger_parser import SwaggerParser, SwaggerParseError
from .mcp_adapter import MCPAdapter
from .http_executor import HTTPExecutor
from .test_generator import TestGenerator
from .models import MCPToolRequest
from .tools_storage import ToolsStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)
console = Console()


class CLIContext:
    """Context object for CLI state."""
    
    def __init__(self):
        self.parser = SwaggerParser()
        self.adapter = MCPAdapter()
        self.executor = HTTPExecutor()
        self.generator = TestGenerator(executor=self.executor)
        self.tools = []
        self.storage = ToolsStorage()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--base-url", help="Base URL for API calls")
@click.option("--timeout", default=30, help="Request timeout in seconds")
@click.pass_context
def cli(ctx, verbose, base_url, timeout):
    """API-Agent: Transform OpenAPI specs into MCP tools for LLM agents."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.ensure_object(CLIContext)
    ctx.obj.parser.base_url = base_url
    ctx.obj.parser.timeout = timeout
    ctx.obj.executor.base_url = base_url
    ctx.obj.executor.timeout = timeout


@cli.command()
@click.option("--url", help="URL to OpenAPI specification")
@click.option("--file", type=click.Path(exists=True), help="Path to OpenAPI specification file")
@click.option("--env", default="dev", help="Environment context (dev/staging/prod)")
@click.option("--output", type=click.Path(), help="Output file for parsed tools (JSON)")
@click.option("--save-as", type=click.Path(), help="Save downloaded spec to local file (only with --url)")
@click.pass_context
def ingest(ctx, url, file, env, output, save_as):
    """Ingest OpenAPI/Swagger specification and extract tools."""
    try:
        console.print(f"[bold blue]Ingesting OpenAPI specification...[/bold blue]")
        
        if url:
            console.print(f"Loading from URL: {url}")
            spec = ctx.obj.parser.load_from_url(url)
            
            # Save downloaded spec to local file if requested
            if save_as:
                console.print(f"Saving spec to local file: {save_as}")
                with open(save_as, 'w', encoding='utf-8') as f:
                    json.dump(spec, f, indent=2, ensure_ascii=False)
                console.print(f"[green]✓ Spec saved to {save_as}[/green]")
                
        elif file:
            console.print(f"Loading from file: {file}")
            spec = ctx.obj.parser.load_from_file(file)
            
            # Validate save-as option usage
            if save_as:
                console.print("[yellow]Warning: --save-as option ignored when using --file[/yellow]")
        else:
            console.print("[red]Error: Must provide either --url or --file[/red]")
            sys.exit(1)
        
        # Extract tools
        tools = ctx.obj.parser.get_endpoints()
        ctx.obj.tools = tools
        
        # Update adapter with tools
        ctx.obj.adapter.update_tools(tools)
        
        # Save tools to storage for persistence
        ctx.obj.storage.save_tools(tools)
        
        # Display summary
        info = ctx.obj.parser.get_info()
        console.print(f"\n[green]Successfully ingested API specification![/green]")
        console.print(f"API Title: {info.get('title', 'Unknown')}")
        console.print(f"API Version: {info.get('version', 'Unknown')}")
        console.print(f"Environment: {env}")
        console.print(f"Tools extracted: {len(tools)}")
        
        # Export to file if requested
        if output:
            ctx.obj.parser.export_tools_json(output)
            console.print(f"Tools exported to: {output}")
        
    except SwaggerParseError as e:
        console.print(f"[red]Parse error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--format", "output_format", default="table", type=click.Choice(["table", "json"]), help="Output format")
@click.option("--tag", help="Filter by tag")
@click.option("--method", type=click.Choice(["GET", "POST", "PUT", "PATCH", "DELETE"]), help="Filter by HTTP method")
@click.pass_context
def list_tools(ctx, output_format, tag, method):
    """List available tools."""
    # Try to get tools from storage first, then from context, then from adapter
    tools = ctx.obj.storage.load_tools() or ctx.obj.adapter.get_tools() or ctx.obj.tools
    
    # Apply filters
    if tag:
        tools = [t for t in tools if tag in t.tags]
    if method:
        tools = [t for t in tools if t.method.upper() == method.upper()]
    
    if not tools:
        console.print("[yellow]No tools found. Please run 'ingest' command first.[/yellow]")
        return
    
    if output_format == "json":
        tools_data = [
            {
                "id": tool.id,
                "name": tool.name,
                "method": tool.method,
                "path": tool.path,
                "description": tool.description,
                "tags": tool.tags,
                "requires_auth": tool.requires_auth()
            }
            for tool in tools
        ]
        console.print(json.dumps(tools_data, indent=2))
    else:
        table = Table(title="Available Tools")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Method", style="green")
        table.add_column("Path", style="yellow")
        table.add_column("Auth", style="red")
        table.add_column("Tags", style="blue")
        
        for tool in tools:
            auth_status = "Yes" if tool.requires_auth() else "No"
            tags_str = ", ".join(tool.tags) if tool.tags else ""
            table.add_row(
                tool.id,
                tool.name,
                tool.method,
                tool.path,
                auth_status,
                tags_str
            )
        
        console.print(table)


@cli.command()
@click.option("--tool", required=True, help="Tool ID to invoke")
@click.option("--data", help="Input data as JSON string")
@click.option("--file", type=click.Path(exists=True), help="Input data from JSON file")
@click.option("--env", default="dev", help="Environment context")
@click.option("--output", type=click.Path(), help="Output file for response")
@click.pass_context
def call(ctx, tool, data, file, env, output):
    """Call a specific tool."""
    try:
        # Parse input data
        inputs = {}
        if data:
            inputs = json.loads(data)
        elif file:
            with open(file, 'r') as f:
                inputs = json.load(f)
        
        console.print(f"[bold blue]Calling tool: {tool}[/bold blue]")
        console.print(f"Environment: {env}")
        console.print(f"Inputs: {json.dumps(inputs, indent=2)}")
        
        # Execute tool
        async def execute():
            response = await ctx.obj.adapter.invoke_tool_direct(
                tool_id=tool,
                inputs=inputs,
                environment=env
            )
            return response
        
        response = asyncio.run(execute())
        
        # Display response
        if response.success:
            console.print(f"\n[green]✓ Tool execution successful![/green]")
            console.print(f"Status Code: {response.status_code}")
            if response.data:
                console.print("Response Data:")
                console.print(json.dumps(response.data, indent=2))
        else:
            console.print(f"\n[red]✗ Tool execution failed![/red]")
            console.print(f"Error: {response.error}")
        
        # Save to file if requested
        if output:
            result_data = {
                "tool_id": tool,
                "success": response.success,
                "status_code": response.status_code,
                "data": response.data,
                "error": response.error,
                "metadata": response.metadata
            }
            with open(output, 'w') as f:
                json.dump(result_data, f, indent=2)
            console.print(f"Response saved to: {output}")
        
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON data: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Execution error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--tool", help="Specific tool to test (if not provided, tests all tools)")
@click.option("--output", type=click.Path(), help="Output file for test results")
@click.option("--types", default="positive,negative,edge", help="Test types to run (comma-separated)")
@click.option("--parallel", is_flag=True, help="Run tests in parallel")
@click.pass_context
def run_tests(ctx, tool, output, types, parallel):
    """Generate and run test suites."""
    try:
        test_types = [t.strip() for t in types.split(",")]
        
        if tool:
            # Test specific tool
            tool_obj = next((t for t in ctx.obj.tools if t.id == tool), None)
            if not tool_obj:
                console.print(f"[red]Tool '{tool}' not found[/red]")
                sys.exit(1)
            
            tools_to_test = [tool_obj]
        else:
            # Test all tools
            tools_to_test = ctx.obj.tools
        
        console.print(f"[bold blue]Running tests for {len(tools_to_test)} tool(s)...[/bold blue]")
        console.print(f"Test types: {', '.join(test_types)}")
        
        async def run_all_tests():
            all_results = []
            
            for tool_obj in tools_to_test:
                console.print(f"\nTesting tool: {tool_obj.id}")
                
                # Generate and run test suite
                test_suite = await ctx.obj.generator.run_test_suite(tool_obj)
                all_results.append(test_suite)
                
                # Display summary
                success_rate = (test_suite.passed / test_suite.total_tests * 100) if test_suite.total_tests > 0 else 0
                console.print(f"  Tests: {test_suite.total_tests}")
                console.print(f"  Passed: {test_suite.passed}")
                console.print(f"  Failed: {test_suite.failed}")
                console.print(f"  Success Rate: {success_rate:.1f}%")
                console.print(f"  Execution Time: {test_suite.execution_time:.2f}s")
            
            return all_results
        
        results = asyncio.run(run_all_tests())
        
        # Overall summary
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        console.print(f"\n[bold green]Overall Test Results:[/bold green]")
        console.print(f"Total Tests: {total_tests}")
        console.print(f"Passed: {total_passed}")
        console.print(f"Failed: {total_failed}")
        console.print(f"Success Rate: {overall_success_rate:.1f}%")
        
        # Export results if requested
        if output:
            results_data = {
                "summary": {
                    "total_tests": total_tests,
                    "passed": total_passed,
                    "failed": total_failed,
                    "success_rate": overall_success_rate,
                    "tools_tested": len(results)
                },
                "tool_results": [
                    {
                        "tool_id": r.tool_id,
                        "total_tests": r.total_tests,
                        "passed": r.passed,
                        "failed": r.failed,
                        "execution_time": r.execution_time,
                        "timestamp": r.timestamp
                    }
                    for r in results
                ]
            }
            
            with open(output, 'w') as f:
                json.dump(results_data, f, indent=2)
            console.print(f"Test results exported to: {output}")
        
    except Exception as e:
        console.print(f"[red]Test execution error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8000, help="Port to run the server on")
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--reload", is_flag=True, help="Enable auto-reload in development")
@click.pass_context
def serve(ctx, port, host, reload):
    """Start the MCP server."""
    # Carregar tools do storage se não há tools no contexto
    if not ctx.obj.tools:
        ctx.obj.tools = ctx.obj.storage.load_tools()
    
    console.print(f"[bold blue]Starting MCP server on {host}:{port}[/bold blue]")
    console.print(f"Tools available: {len(ctx.obj.tools)}")
    console.print(f"Discovery endpoint: http://{host}:{port}/mcp/tools")
    console.print(f"Invocation endpoint: http://{host}:{port}/mcp/invoke")
    console.print(f"Health check: http://{host}:{port}/health")
    console.print(f"API Documentation: http://{host}:{port}/docs")
    
    if not ctx.obj.tools:
        console.print("[yellow]Warning: No tools loaded. Run 'ingest' command first.[/yellow]")
    
    # Update adapter with current tools
    ctx.obj.adapter.update_tools(ctx.obj.tools)
    
    # Iniciar monitoramento de testes
    ctx.obj.adapter.start_test_monitoring()
    console.print("[green]Test monitoring started![/green]")
    
    # Run the server
    uvicorn.run(
        ctx.obj.adapter.get_app(),
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@cli.command()
@click.option("--tool", help="Tool ID to get details for")
@click.pass_context
def describe(ctx, tool):
    """Get detailed information about a tool."""
    if not tool:
        console.print("[red]Error: Must provide --tool[/red]")
        sys.exit(1)
    
    tool_obj = next((t for t in ctx.obj.tools if t.id == tool), None)
    if not tool_obj:
        console.print(f"[red]Tool '{tool}' not found[/red]")
        sys.exit(1)
    
    console.print(f"[bold blue]Tool Details: {tool}[/bold blue]")
    console.print(f"Name: {tool_obj.name}")
    console.print(f"Description: {tool_obj.description}")
    console.print(f"Method: {tool_obj.method}")
    console.print(f"Path: {tool_obj.path}")
    console.print(f"Requires Auth: {tool_obj.requires_auth()}")
    
    if tool_obj.tags:
        console.print(f"Tags: {', '.join(tool_obj.tags)}")
    
    if tool_obj.parameters:
        console.print("\nParameters:")
        for param in tool_obj.parameters:
            required_str = " (required)" if param.required else ""
            console.print(f"  - {param.name} ({param.location.value}){required_str}")
            if param.description:
                console.print(f"    {param.description}")
    
    if tool_obj.request_schema:
        console.print("\nRequest Schema:")
        console.print(json.dumps(tool_obj.request_schema, indent=2))
    
    if tool_obj.response_schema:
        console.print("\nResponse Schema:")
        console.print(json.dumps(tool_obj.response_schema, indent=2))
    
    if tool_obj.examples:
        console.print("\nExamples:")
        for example in tool_obj.examples:
            console.print(f"  - {example.name}")
            if example.description:
                console.print(f"    {example.description}")
            if example.value:
                console.print(f"    Value: {json.dumps(example.value, indent=2)}")


@cli.command()
@click.option("--output", type=click.Path(), help="Output file for MCP schema")
@click.pass_context
def export_schema(ctx, output):
    """Export MCP-compatible schema for all tools."""
    schema = ctx.obj.adapter.export_mcp_schema()
    
    if output:
        with open(output, 'w') as f:
            json.dump(schema, f, indent=2)
        console.print(f"MCP schema exported to: {output}")
    else:
        console.print(json.dumps(schema, indent=2))


@cli.command("mcp-stdio")
@click.option("--spec-file", help="Path to OpenAPI specification file")
@click.option("--spec-url", help="URL to OpenAPI specification")
@click.pass_context
def mcp_stdio(ctx, spec_file, spec_url):
    """Start MCP stdio server for VS Code integration."""
    import os
    
    # Set environment variables for the stdio server
    if spec_file:
        os.environ["API_SPEC_FILE"] = spec_file
    elif spec_url:
        os.environ["API_SPEC_URL"] = spec_url
    
    # Import and run the stdio server
    from .mcp_stdio import main as run_stdio
    asyncio.run(run_stdio())


def main():
    """Entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
