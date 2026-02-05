"""Rich output formatting for NEO-AIOS CLI.

This module provides consistent, formatted output using the Rich library.
All CLI output should go through these functions for consistency.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

# Custom theme for NEO-AIOS
AIOS_THEME = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "agent": "magenta bold",
        "command": "blue",
        "path": "dim cyan",
        "version": "green bold",
    }
)

# Global console instance with custom theme
console = Console(theme=AIOS_THEME)


def info(message: str) -> None:
    """Print an info message.

    Args:
        message: The message to display.
    """
    console.print(f"[info](i)[/info] {message}")


def success(message: str) -> None:
    """Print a success message.

    Args:
        message: The message to display.
    """
    console.print(f"[success][ok][/success] {message}")


def warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: The message to display.
    """
    console.print(f"[warning][!][/warning] {message}")


def error(message: str) -> None:
    """Print an error message.

    Args:
        message: The message to display.
    """
    console.print(f"[error][x][/error] {message}")


def header(title: str, subtitle: str | None = None) -> None:
    """Print a styled header.

    Args:
        title: The main title.
        subtitle: Optional subtitle.
    """
    content = f"[bold]{title}[/bold]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, border_style="cyan"))


def agent_status(
    agent_id: str,
    agent_name: str,
    icon: str,
    status: str,
) -> None:
    """Print agent status information.

    Args:
        agent_id: The agent identifier.
        agent_name: The agent display name.
        icon: The agent's icon emoji.
        status: Current status (active/inactive).
    """
    status_color = "success" if status == "active" else "dim"
    console.print(
        f"[agent]{icon} {agent_name}[/agent] "
        f"([dim]{agent_id}[/dim]) "
        f"[[{status_color}]{status}[/{status_color}]]"
    )


def create_table(
    title: str,
    columns: list[tuple[str, str]],
    rows: list[list[Any]],
) -> Table:
    """Create a styled table.

    Args:
        title: Table title.
        columns: List of (name, style) tuples for columns.
        rows: List of row data.

    Returns:
        A Rich Table object ready for printing.
    """
    table = Table(title=title, border_style="dim")

    for col_name, col_style in columns:
        table.add_column(col_name, style=col_style)

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table


def print_version(version: str, python_version: str) -> None:
    """Print version information in a styled format.

    Args:
        version: NEO-AIOS version.
        python_version: Python version.
    """
    console.print()
    console.print("[bold cyan]NEO-AIOS[/bold cyan] - Agent Intelligence Operating System")
    console.print()
    console.print(f"  [dim]Version:[/dim]  [version]{version}[/version]")
    console.print(f"  [dim]Python:[/dim]   {python_version}")
    console.print()
