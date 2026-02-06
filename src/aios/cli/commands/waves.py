"""Wave analysis commands for NEO-AIOS CLI."""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table

from aios.core.waves import CycleDetectedError
from aios.core.waves import WaveAnalyzer
from aios.core.waves_models import Task

console = Console()


def _parse_tasks_from_json(data: str) -> list[Task]:
    """Parse tasks from JSON string."""
    parsed = json.loads(data)
    if isinstance(parsed, list):
        return [Task.model_validate(item) for item in parsed]
    return []


@click.group(name="waves")
def waves_group() -> None:
    """Wave analysis for parallel task execution."""


@waves_group.command(name="analyze")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON.")
def waves_analyze(input_file: str, json_out: bool) -> None:
    """Analyze task dependencies from a JSON file."""
    from pathlib import Path

    data = Path(input_file).read_text()
    try:
        tasks = _parse_tasks_from_json(data)
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise SystemExit(1) from e

    analyzer = WaveAnalyzer()
    try:
        analysis = analyzer.analyze(tasks)
    except CycleDetectedError as e:
        console.print(f"[red]Cycle detected: {e}[/red]")
        raise SystemExit(1) from e

    if json_out:
        console.print(analysis.model_dump_json(indent=2))
        return

    # Rich table output
    for wave in analysis.waves:
        table = Table(title=f"Wave {wave.number}")
        table.add_column("Task ID", min_width=10)
        table.add_column("Name")
        table.add_column("Est. Hours", width=10)

        for task in wave.tasks:
            table.add_row(task.id, task.name, f"{task.estimated_hours:.1f}h")

        console.print(table)
        console.print()

    # Summary
    console.print("[bold]Summary[/bold]")
    console.print(f"  Waves: {analysis.wave_count}")
    console.print(f"  Tasks: {analysis.total_tasks}")
    console.print(f"  Sequential: {analysis.total_sequential_hours:.1f}h")
    console.print(f"  Parallel: {analysis.total_parallel_hours:.1f}h")
    console.print(f"  Speedup: {analysis.parallelism_speedup:.1f}x")

    if analysis.critical_path.tasks:
        console.print(
            f"  Critical path: {' -> '.join(analysis.critical_path.tasks)}"
            f" ({analysis.critical_path.total_hours:.1f}h)"
        )
