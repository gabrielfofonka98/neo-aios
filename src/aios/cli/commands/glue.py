"""Glue script generation commands for NEO-AIOS CLI."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from aios.core.glue import GlueGenerator
from aios.core.glue_models import GlueConfig

console = Console()


@click.group(name="glue")
def glue_group() -> None:
    """Agent prompt composition from project context."""


@glue_group.command(name="compose")
@click.argument("story_path", type=click.Path(exists=True))
@click.option("--output", "-o", "output_path", help="Output file path.")
@click.option("--max-lines", default=1500, help="Maximum output lines.")
@click.option("--no-standards", is_flag=True, help="Exclude STANDARDS.md.")
@click.option("--no-prd", is_flag=True, help="Exclude PRD.")
def glue_compose(
    story_path: str,
    output_path: str | None,
    max_lines: int,
    no_standards: bool,
    no_prd: bool,
) -> None:
    """Compose a glue script from a story file."""
    config = GlueConfig(
        story_path=story_path,
        max_lines=max_lines,
        include_standards=not no_standards,
        include_prd=not no_prd,
    )

    generator = GlueGenerator()
    result = generator.compose(config)

    if result.section_count == 0:
        console.print("[red]No sections found to compose.[/red]")
        raise SystemExit(1)

    markdown = result.to_markdown()

    if output_path:
        Path(output_path).write_text(markdown)
        console.print(f"[green]Written to {output_path}[/green]")
    else:
        console.print(markdown)

    console.print(
        f"\n[dim]Sections: {result.section_count} | "
        f"Lines: {result.total_lines} | "
        f"Truncated: {result.truncated}[/dim]"
    )
