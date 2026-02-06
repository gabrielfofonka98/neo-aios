"""MCP management commands for NEO-AIOS CLI."""

import click
from rich.console import Console
from rich.table import Table

from aios.infrastructure.mcp import MCPManager

console = Console()


@click.group(name="mcp")
def mcp_group() -> None:
    """MCP server management."""


@mcp_group.command(name="list")
def mcp_list() -> None:
    """List MCP servers (installed and available)."""
    manager = MCPManager()
    installed = manager.list_installed()
    catalog = manager.list_catalog()

    table = Table(title="MCP Servers")
    table.add_column("Name", min_width=20)
    table.add_column("Status", width=12)
    table.add_column("Description")

    for entry in catalog:
        status = (
            "[green]installed[/green]"
            if entry.name in installed
            else "[dim]available[/dim]"
        )
        table.add_row(entry.name, status, entry.description)

    console.print(table)


@mcp_group.command(name="install")
@click.argument("name")
def mcp_install(name: str) -> None:
    """Install an MCP server from catalog."""
    manager = MCPManager()

    if manager.is_installed(name):
        console.print(f"[yellow]{name} is already installed[/yellow]")
        return

    if not manager.has_npx():
        console.print("[red]npx not found. Install Node.js first.[/red]")
        raise SystemExit(1)

    success = manager.install(name)
    if success:
        console.print(f"[green]Installed {name}[/green]")
    else:
        console.print(f"[red]{name} not found in catalog[/red]")
        raise SystemExit(1)


@mcp_group.command(name="config")
def mcp_config() -> None:
    """Generate/update .mcp.json with essential MCPs."""
    manager = MCPManager()
    newly_installed = manager.install_all_essential()

    if newly_installed:
        console.print(f"[green]Installed: {', '.join(newly_installed)}[/green]")
    else:
        console.print("[green]All essential MCPs already installed[/green]")

    console.print(f"Config: {manager.config_path}")
