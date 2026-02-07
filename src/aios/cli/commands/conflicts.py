"""File conflict management commands for NEO-AIOS CLI.

Provides commands for checking, reviewing, and cleaning up
multi-agent file modification conflicts tracked by FileEvolutionTracker.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from aios.memory.file_evolution import FileEvolutionTracker

console = Console()

DEFAULT_EVOLUTION_DIR = Path(".aios/memory/evolution")

_SEVERITY_STYLE: dict[str, str] = {
    "critical": "red bold",
    "high": "red",
    "medium": "yellow",
    "low": "dim",
}


def _get_tracker(storage_dir: Path | None = None) -> FileEvolutionTracker:
    """Create a FileEvolutionTracker instance with the given or default dir.

    Args:
        storage_dir: Optional override for the evolution storage directory.

    Returns:
        A configured FileEvolutionTracker instance.
    """
    return FileEvolutionTracker(storage_dir=storage_dir or DEFAULT_EVOLUTION_DIR)


@click.group(name="conflicts")
def conflicts_group() -> None:
    """Deteccao de conflitos de arquivos entre agentes."""


@conflicts_group.command(name="check")
@click.option(
    "--agent",
    "agent_id",
    default=None,
    help="Filtrar por agente especifico.",
)
def conflicts_check(agent_id: str | None) -> None:
    """Verificar conflitos ativos de arquivos."""
    tracker = _get_tracker()
    reports = tracker.detect_drift(window_minutes=60)

    if agent_id:
        reports = [r for r in reports if agent_id in r.agents]

    if not reports:
        console.print("[green]Nenhum conflito detectado.[/green]")
        return

    table = Table(title=f"Conflitos Ativos ({len(reports)})")
    table.add_column("Arquivo", style="cyan", max_width=40)
    table.add_column("Agentes", max_width=30)
    table.add_column("Modificacoes", justify="right")
    table.add_column("Severidade")
    table.add_column("Primeira", style="dim")
    table.add_column("Ultima", style="dim")

    for report in reports:
        severity_style = _SEVERITY_STYLE.get(report.severity, "")
        table.add_row(
            report.file_path,
            ", ".join(report.agents),
            str(report.total_modifications),
            f"[{severity_style}]{report.severity.upper()}[/{severity_style}]",
            report.first_modification.strftime("%H:%M:%S"),
            report.last_modification.strftime("%H:%M:%S"),
        )

    console.print(table)


@conflicts_group.command(name="history")
@click.option(
    "--days",
    default=7,
    type=int,
    help="Numero de dias para analisar (padrao: 7).",
)
def conflicts_history(days: int) -> None:
    """Exibir historico de modificacoes de arquivos."""
    tracker = _get_tracker()
    reports = tracker.detect_drift(window_minutes=days * 24 * 60)

    if not reports:
        console.print(f"[dim]Nenhum conflito nos ultimos {days} dias.[/dim]")
        return

    table = Table(title=f"Historico de Conflitos ({days} dias)")
    table.add_column("Arquivo", style="cyan", max_width=40)
    table.add_column("Agentes", max_width=30)
    table.add_column("Total", justify="right")
    table.add_column("Severidade")
    table.add_column("Periodo", style="dim")

    for report in reports:
        severity_style = _SEVERITY_STYLE.get(report.severity, "")
        period = (
            f"{report.first_modification.strftime('%m-%d %H:%M')} - "
            f"{report.last_modification.strftime('%m-%d %H:%M')}"
        )
        table.add_row(
            report.file_path,
            ", ".join(report.agents),
            str(report.total_modifications),
            f"[{severity_style}]{report.severity.upper()}[/{severity_style}]",
            period,
        )

    console.print(table)


@conflicts_group.command(name="cleanup")
@click.option(
    "--days",
    default=7,
    type=int,
    help="Remover entradas mais antigas que N dias (padrao: 7).",
)
@click.confirmation_option(
    prompt="Tem certeza que deseja remover entradas antigas?",
)
def conflicts_cleanup(days: int) -> None:
    """Remover entradas antigas do historico de conflitos."""
    tracker = _get_tracker()
    removed = tracker.cleanup(max_age_days=days)

    if removed == 0:
        console.print(f"[dim]Nenhuma entrada com mais de {days} dias encontrada.[/dim]")
    else:
        console.print(
            f"[green]{removed} entrada(s) removida(s) (mais de {days} dias).[/green]"
        )
