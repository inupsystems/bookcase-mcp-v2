"""Command-line interface for MCP Client."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from .client import MCPClient
from .config import MCPConfig
from .models import ToolInvocation

console = Console()


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]Success:[/green] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]Info:[/blue] {message}")


def format_json(data: Any) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=2, ensure_ascii=False)


async def run_async_command(func):
    """Run an async command."""
    try:
        return await func()
    except Exception as e:
        print_error(f"Command failed: {str(e)}")
        sys.exit(1)


@click.group()
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    default='config.json',
    help='Configuration file path'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config: Path, verbose: bool):
    """MCP Client - Connect to multiple MCP servers and execute tools."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)


@cli.group()
def servers():
    """Manage MCP servers."""
    pass


@servers.command('list')
@click.pass_context
def servers_list(ctx):
    """List configured servers."""
    async def _list_servers():
        config_path = ctx.obj['config_path']
        
        try:
            config = MCPConfig.from_file(config_path)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return
        
        if not config.servers:
            print_info("No servers configured")
            return
        
        table = Table(title="Configured MCP Servers")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Command", style="yellow")
        table.add_column("Status", style="green")
        
        client = MCPClient(config)
        await client.initialize()
        
        # Try to connect to get status
        try:
            connection_results = await client.connect()
            
            for name, server_config in config.servers.items():
                status = "Connected" if connection_results.get(name, False) else "Disconnected"
                status_style = "green" if connection_results.get(name, False) else "red"
                
                table.add_row(
                    name,
                    server_config.type.value,
                    f"{server_config.command} {' '.join(server_config.args[:2])}...",
                    Text(status, style=status_style)
                )
        finally:
            await client.disconnect()
        
        console.print(table)
    
    asyncio.run(run_async_command(_list_servers))


@servers.command('test')
@click.argument('server_name', required=False)
@click.pass_context
def servers_test(ctx, server_name: Optional[str]):
    """Test connection to servers."""
    async def _test_servers():
        config_path = ctx.obj['config_path']
        
        try:
            config = MCPConfig.from_file(config_path)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return
        
        client = MCPClient(config)
        await client.initialize()
        
        try:
            connection_results = await client.connect()
            
            if server_name:
                if server_name not in connection_results:
                    print_error(f"Server '{server_name}' not found in configuration")
                    return
                
                success = connection_results[server_name]
                if success:
                    print_success(f"Successfully connected to {server_name}")
                else:
                    print_error(f"Failed to connect to {server_name}")
            else:
                for name, success in connection_results.items():
                    if success:
                        print_success(f"Connected to {name}")
                    else:
                        print_error(f"Failed to connect to {name}")
        finally:
            await client.disconnect()
    
    asyncio.run(run_async_command(_test_servers))


@cli.group()
def tools():
    """Manage and execute tools."""
    pass


@tools.command('list')
@click.option('--server', '-s', help='Filter by server name')
@click.option('--search', help='Search tools by name or description')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json']), 
              default='table',
              help='Output format')
@click.pass_context
def tools_list(ctx, server: Optional[str], search: Optional[str], output_format: str):
    """List available tools."""
    async def _list_tools():
        config_path = ctx.obj['config_path']
        
        try:
            config = MCPConfig.from_file(config_path)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return
        
        client = MCPClient(config)
        await client.initialize()
        
        try:
            await client.connect()
            
            # Get tools
            if search:
                tools_list = client.search_tools(search)
            else:
                tools_list = client.get_tools(server)
            
            if not tools_list:
                print_info("No tools found")
                return
            
            if output_format == 'json':
                tools_data = [
                    {
                        'name': tool.name,
                        'description': tool.description,
                        'server': tool.server_name,
                        'parameters': [
                            {
                                'name': p.name,
                                'type': p.type,
                                'required': p.required,
                                'description': p.description
                            }
                            for p in tool.parameters
                        ]
                    }
                    for tool in tools_list
                ]
                console.print(format_json(tools_data))
            else:
                table = Table(title="Available Tools")
                table.add_column("Name", style="cyan")
                table.add_column("Server", style="magenta")
                table.add_column("Description", style="yellow")
                table.add_column("Parameters", style="green")
                
                for tool in tools_list:
                    params = f"{len(tool.parameters)} params"
                    if tool.parameters:
                        required_params = [p.name for p in tool.parameters if p.required]
                        if required_params:
                            params += f" ({len(required_params)} required)"
                    
                    table.add_row(
                        tool.name,
                        tool.server_name or "Unknown",
                        tool.description or "No description",
                        params
                    )
                
                console.print(table)
        finally:
            await client.disconnect()
    
    asyncio.run(run_async_command(_list_tools))


@tools.command('describe')
@click.argument('tool_name')
@click.option('--server', '-s', help='Server name (if tool exists on multiple servers)')
@click.pass_context
def tools_describe(ctx, tool_name: str, server: Optional[str]):
    """Describe a specific tool."""
    async def _describe_tool():
        config_path = ctx.obj['config_path']
        
        try:
            config = MCPConfig.from_file(config_path)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return
        
        client = MCPClient(config)
        await client.initialize()
        
        try:
            await client.connect()
            
            tool = client.find_tool(tool_name, server)
            if not tool:
                print_error(f"Tool '{tool_name}' not found")
                return
            
            console.print(f"[bold cyan]Tool: {tool.name}[/bold cyan]")
            console.print(f"[bold]Server:[/bold] {tool.server_name}")
            console.print(f"[bold]Description:[/bold] {tool.description or 'No description'}")
            
            if tool.parameters:
                console.print("\n[bold]Parameters:[/bold]")
                
                param_table = Table()
                param_table.add_column("Name", style="cyan")
                param_table.add_column("Type", style="magenta")
                param_table.add_column("Required", style="yellow")
                param_table.add_column("Description", style="green")
                
                for param in tool.parameters:
                    param_table.add_row(
                        param.name,
                        param.type,
                        "Yes" if param.required else "No",
                        param.description or "No description"
                    )
                
                console.print(param_table)
            else:
                console.print("\n[bold]Parameters:[/bold] None")
            
            if tool.input_schema:
                console.print(f"\n[bold]Input Schema:[/bold]")
                console.print(format_json(tool.input_schema))
        finally:
            await client.disconnect()
    
    asyncio.run(run_async_command(_describe_tool))


@tools.command('call')
@click.argument('tool_name')
@click.option('--server', '-s', help='Server name')
@click.option('--param', '-p', multiple=True, help='Parameters as key=value pairs')
@click.option('--params-json', help='Parameters as JSON string')
@click.option('--timeout', type=float, help='Execution timeout in seconds')
@click.option('--format', 'output_format',
              type=click.Choice(['json', 'text']),
              default='text',
              help='Output format')
@click.pass_context
def tools_call(ctx, tool_name: str, server: Optional[str], param: List[str], 
               params_json: Optional[str], timeout: Optional[float], output_format: str):
    """Execute a tool."""
    async def _call_tool():
        config_path = ctx.obj['config_path']
        
        try:
            config = MCPConfig.from_file(config_path)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return
        
        # Parse parameters
        parameters = {}
        
        if params_json:
            try:
                parameters = json.loads(params_json)
            except json.JSONDecodeError as e:
                print_error(f"Invalid JSON in parameters: {e}")
                return
        
        for p in param:
            if '=' not in p:
                print_error(f"Invalid parameter format: {p}. Use key=value")
                return
            key, value = p.split('=', 1)
            
            # Try to parse value as JSON, fallback to string
            try:
                parameters[key] = json.loads(value)
            except json.JSONDecodeError:
                parameters[key] = value
        
        client = MCPClient(config)
        await client.initialize()
        
        try:
            await client.connect()
            
            result = await client.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                server_name=server,
                timeout=timeout
            )
            
            if output_format == 'json':
                result_data = {
                    'success': result.success,
                    'result': result.result,
                    'error': result.error,
                    'execution_time': result.execution_time,
                    'server_name': result.server_name,
                    'tool_name': result.tool_name,
                    'timestamp': result.timestamp.isoformat()
                }
                console.print(format_json(result_data))
            else:
                if result.success:
                    print_success(f"Tool executed successfully in {result.execution_time:.2f}s")
                    console.print("\n[bold]Result:[/bold]")
                    if isinstance(result.result, (dict, list)):
                        console.print(format_json(result.result))
                    else:
                        console.print(str(result.result))
                else:
                    print_error(f"Tool execution failed: {result.error}")
        finally:
            await client.disconnect()
    
    asyncio.run(run_async_command(_call_tool))


@tools.command('test')
@click.argument('tool_name')
@click.option('--server', '-s', help='Server name')
@click.pass_context
def tools_test(ctx, tool_name: str, server: Optional[str]):
    """Test a tool with default parameters."""
    async def _test_tool():
        config_path = ctx.obj['config_path']
        
        try:
            config = MCPConfig.from_file(config_path)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return
        
        client = MCPClient(config)
        await client.initialize()
        
        try:
            await client.connect()
            
            result = await client.test_tool(tool_name, server)
            
            if result.success:
                print_success(f"Tool test passed in {result.execution_time:.2f}s")
                console.print("\n[bold]Result:[/bold]")
                if isinstance(result.result, (dict, list)):
                    console.print(format_json(result.result))
                else:
                    console.print(str(result.result))
            else:
                print_error(f"Tool test failed: {result.error}")
        finally:
            await client.disconnect()
    
    asyncio.run(run_async_command(_test_tool))


@cli.command('status')
@click.pass_context
def status(ctx):
    """Show client status and health check."""
    async def _status():
        config_path = ctx.obj['config_path']
        
        try:
            config = MCPConfig.from_file(config_path)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return
        
        client = MCPClient(config)
        await client.initialize()
        
        try:
            await client.connect()
            
            health = await client.health_check()
            stats = client.get_statistics()
            
            console.print("[bold cyan]MCP Client Status[/bold cyan]")
            console.print(f"Initialized: {health['initialized']}")
            
            if health['servers']:
                console.print(f"\n[bold]Servers:[/bold]")
                for server_name, is_healthy in health['servers'].items():
                    status_text = "Healthy" if is_healthy else "Unhealthy"
                    status_style = "green" if is_healthy else "red"
                    console.print(f"  {server_name}: [bold {status_style}]{status_text}[/bold {status_style}]")
            
            if health['tools']:
                console.print(f"\n[bold]Tools:[/bold]")
                console.print(f"  Total: {health['tools'].get('total_tools', 0)}")
                console.print(f"  Servers with tools: {health['tools'].get('servers_with_tools', 0)}")
            
            if health['execution']:
                console.print(f"\n[bold]Execution History:[/bold]")
                console.print(f"  Total executions: {health['execution'].get('total_executions', 0)}")
                console.print(f"  Success rate: {health['execution'].get('success_rate', 0):.1f}%")
                console.print(f"  Average time: {health['execution'].get('average_execution_time', 0):.2f}s")
        
        finally:
            await client.disconnect()
    
    asyncio.run(run_async_command(_status))


@cli.command('config')
@click.option('--validate', is_flag=True, help='Validate configuration only')
@click.pass_context
def config_cmd(ctx, validate: bool):
    """Show or validate configuration."""
    config_path = ctx.obj['config_path']
    
    try:
        config = MCPConfig.from_file(config_path)
        
        if validate:
            issues = config.validate_server_configs()
            if issues:
                print_error("Configuration validation failed:")
                for server, server_issues in issues.items():
                    console.print(f"  {server}:")
                    for issue in server_issues:
                        console.print(f"    - {issue}")
            else:
                print_success("Configuration is valid")
        else:
            console.print(format_json(config.dict()))
    
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
