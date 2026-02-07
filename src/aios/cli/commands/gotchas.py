"""Gotchas management commands for NEO-AIOS CLI.

Provides commands for viewing, filtering, and managing tracked gotchas
(recurring issues that have been auto-promoted to rules).
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from aios.memory.gotchas import GotchasMemory

console = Console()

DEFAULT_GOTCHAS_PATH = Path(".aios/memory/gotchas.json")


def _get_memory(storage_path: Path | None = None) -> GotchasMemory:
    """Create a GotchasMemory instance with the given or default path.

    Args:
        storage_path: Optional override for the gotchas JSON storage file.

    Returns:
        A configured GotchasMemory instance.
    """
    return GotchasMemory(storage_path=storage_path or DEFAULT_GOTCHAS_PATH)


@click.group(name="gotchas")
def gotchas_group() -> None:
    """Gerenciamento de gotchas (issues recorrentes promovidas a regras)."""


@gotchas_group.command(name="list")
@click.option(
    "--agent",
    "agent_id",
    default=None,
    help="Filtrar por categoria do agente.",
)
@click.option(
    "--min-count",
    default=1,
    type=int,
    help="Contagem minima de ocorrencias para exibir issues.",
)
def gotchas_list(agent_id: str | None, min_count: int) -> None:
    """Listar gotchas e issues rastreadas."""
    mem = _get_memory()
    gotchas = mem.get_gotchas(category=agent_id)
    issues = mem.get_issues()

    if agent_id:
        issues = [i for i in issues if i.category == agent_id]
    if min_count > 1:
        issues = [i for i in issues if i.count >= min_count]

    if not gotchas and not issues:
        console.print("[dim]Nenhum gotcha ou issue encontrado.[/dim]")
        return

    if gotchas:
        table = Table(title=f"Gotchas Confirmados ({len(gotchas)})")
        table.add_column("Categoria", style="cyan")
        table.add_column("Descricao", max_width=50)
        table.add_column("Contexto", style="dim", max_width=30)
        table.add_column("Ocorrencias", style="green", justify="right")
        table.add_column("Promovido em", style="dim")

        for g in gotchas:
            table.add_row(
                g.category,
                g.description,
                g.context or "-",
                str(g.occurrence_count),
                g.promoted_at.strftime("%Y-%m-%d %H:%M"),
            )
        console.print(table)

    if issues:
        console.print()
        issue_table = Table(title=f"Issues Rastreadas ({len(issues)})")
        issue_table.add_column("Categoria", style="cyan")
        issue_table.add_column("Descricao", max_width=50)
        issue_table.add_column("Contagem", style="yellow", justify="right")
        issue_table.add_column("Primeira vez", style="dim")
        issue_table.add_column("Ultima vez", style="dim")

        for i in issues:
            issue_table.add_row(
                i.category,
                i.description,
                f"{i.count}/{mem.threshold}",
                i.first_seen.strftime("%Y-%m-%d %H:%M"),
                i.last_seen.strftime("%Y-%m-%d %H:%M"),
            )
        console.print(issue_table)


@gotchas_group.command(name="stats")
def gotchas_stats() -> None:
    """Exibir estatisticas de gotchas e issues rastreadas."""
    mem = _get_memory()
    gotchas = mem.get_gotchas()
    issues = mem.get_issues()

    total_issues = len(issues)
    total_gotchas = len(gotchas)

    console.print("[bold]Estatisticas de Gotchas[/bold]")
    console.print()
    console.print(f"  Total de issues rastreadas:  [yellow]{total_issues}[/yellow]")
    console.print(f"  Total de gotchas promovidos: [green]{total_gotchas}[/green]")
    console.print(f"  Threshold para promocao:     [dim]{mem.threshold}[/dim]")

    # Top categories from gotchas
    if gotchas:
        categories: dict[str, int] = {}
        for g in gotchas:
            categories[g.category] = categories.get(g.category, 0) + 1

        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

        console.print()
        console.print("[bold]Top Categorias (Gotchas)[/bold]")
        for cat, count in sorted_cats[:10]:
            console.print(f"  {cat}: [cyan]{count}[/cyan]")

    # Top categories from issues
    if issues:
        issue_cats: dict[str, int] = {}
        for i in issues:
            issue_cats[i.category] = issue_cats.get(i.category, 0) + 1

        sorted_issue_cats = sorted(issue_cats.items(), key=lambda x: x[1], reverse=True)

        console.print()
        console.print("[bold]Top Categorias (Issues Pendentes)[/bold]")
        for cat, count in sorted_issue_cats[:10]:
            console.print(f"  {cat}: [yellow]{count}[/yellow]")


@gotchas_group.command(name="reset")
@click.confirmation_option(
    prompt="Tem certeza que deseja limpar todos os gotchas e issues?",
)
def gotchas_reset() -> None:
    """Limpar todos os gotchas e issues (com confirmacao)."""
    mem = _get_memory()
    storage_path = mem.storage_path

    if storage_path.exists():
        storage_path.unlink()

    md_path = storage_path.with_suffix(".md")
    if md_path.exists():
        md_path.unlink()

    console.print("[green]Todos os gotchas e issues foram removidos.[/green]")
