"""IDS commands for NEO-AIOS CLI."""

import click
from rich.console import Console
from rich.table import Table

from aios.quality.ids import IDSEngine
from aios.quality.ids_models import IDSAction

console = Console()


def _action_style(action: IDSAction) -> str:
    styles: dict[IDSAction, str] = {
        IDSAction.REUSE: "[green]REUSE[/green]",
        IDSAction.ADAPT: "[yellow]ADAPT[/yellow]",
        IDSAction.CREATE: "[red]CREATE[/red]",
    }
    return styles.get(action, str(action))


@click.group(name="ids")
def ids_group() -> None:
    """Incremental Development System — REUSE > ADAPT > CREATE."""


@ids_group.command(name="check")
@click.argument("path")
def ids_check(path: str) -> None:
    """Check if a file/module already exists or has similar matches."""
    engine = IDSEngine()
    decision = engine.check(path)

    console.print(f"[bold]Target:[/bold] {path}")
    console.print(f"[bold]Action:[/bold] {_action_style(decision.action)}")
    console.print(f"[bold]Reason:[/bold] {decision.reason}")

    if decision.matches:
        table = Table(title="Similar Files")
        table.add_column("Path")
        table.add_column("Similarity", width=12)
        table.add_column("Type", width=12)

        for match in decision.matches:
            table.add_row(match.path, f"{match.similarity:.0%}", match.match_type)

        console.print(table)


@ids_group.command(name="stats")
def ids_stats() -> None:
    """Show IDS tracking statistics."""
    engine = IDSEngine()
    stats = engine.get_stats()

    console.print("[bold]IDS Statistics[/bold]")
    console.print(f"  Total checks: {stats.total_checks}")
    console.print(f"  REUSE: {stats.reuse_count}")
    console.print(f"  ADAPT: {stats.adapt_count}")
    console.print(f"  CREATE: {stats.create_count}")
    console.print(f"  CREATE rate: {stats.create_rate:.0%}")
    if stats.total_checks > 0:
        console.print(f"  Last updated: {stats.last_updated.isoformat()}")
