"""Hook bridge: CLI interface for bash hooks to interact with memory modules.

Provides Click subcommands that hooks can call to record file changes,
check conflicts, record gotchas, and retrieve gotchas for prompt injection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from aios.memory.file_evolution import ConflictInfo
from aios.memory.file_evolution import FileEvolutionTracker
from aios.memory.gotchas import GotchasMemory

# Default storage paths (relative to project root)
_DEFAULT_GOTCHAS_PATH = ".aios/memory/gotchas.json"
_DEFAULT_EVOLUTION_DIR = ".aios/memory/file-evolution"
_DEFAULT_THRESHOLD = 3


def _resolve_project_root(project_dir: str | None) -> Path:
    """Resolve the project root directory.

    Uses the provided path, or falls back to CWD.
    """
    if project_dir:
        return Path(project_dir).resolve()
    return Path.cwd()


def _build_gotchas_memory(project_root: Path) -> GotchasMemory:
    """Build a GotchasMemory instance from project root."""
    storage_path = project_root / _DEFAULT_GOTCHAS_PATH
    return GotchasMemory(
        storage_path=storage_path,
        threshold=_DEFAULT_THRESHOLD,
    )


def _build_evolution_tracker(project_root: Path) -> FileEvolutionTracker:
    """Build a FileEvolutionTracker instance from project root."""
    storage_dir = project_root / _DEFAULT_EVOLUTION_DIR
    return FileEvolutionTracker(storage_dir=storage_dir)


def _conflicts_to_json(conflicts: list[ConflictInfo]) -> str:
    """Serialize a list of ConflictInfo to JSON string."""
    items: list[dict[str, Any]] = []
    for conflict in conflicts:
        items.append({
            "file_path": conflict.file_path,
            "agents": conflict.agents,
            "severity": conflict.severity,
            "modification_count": len(conflict.modifications),
        })
    return json.dumps(items, indent=2, ensure_ascii=False)


@click.group()
@click.option(
    "--project-dir",
    envvar="CLAUDE_PROJECT_DIR",
    default=None,
    help="Project root directory. Defaults to CLAUDE_PROJECT_DIR or CWD.",
)
@click.pass_context
def cli(ctx: click.Context, project_dir: str | None) -> None:
    """Hook bridge for NEO-AIOS memory modules.

    Called by bash hooks to integrate with GotchasMemory and
    FileEvolutionTracker.
    """
    ctx.ensure_object(dict)
    ctx.obj["project_root"] = _resolve_project_root(project_dir)


@cli.command("record-file-change")
@click.option("--agent", required=True, help="Agent ID that made the change.")
@click.option("--file", "file_path", required=True, help="Path of the changed file.")
@click.option(
    "--action",
    required=True,
    type=click.Choice(["create", "modify", "delete"]),
    help="Type of file action.",
)
@click.pass_context
def record_file_change(
    ctx: click.Context,
    agent: str,
    file_path: str,
    action: str,
) -> None:
    """Record a file modification in FileEvolutionTracker."""
    project_root: Path = ctx.obj["project_root"]
    tracker = _build_evolution_tracker(project_root)
    tracker.record_modification(
        file_path=file_path,
        agent_id=agent,
        task_id=action,
    )
    click.echo(json.dumps({
        "status": "ok",
        "agent": agent,
        "file": file_path,
        "action": action,
    }))


@cli.command("check-conflicts")
@click.option("--agent", required=True, help="Agent ID to check conflicts for.")
@click.pass_context
def check_conflicts(ctx: click.Context, agent: str) -> None:
    """Return active conflicts for an agent (JSON output).

    Checks all files the agent has modified and reports any conflicts
    where other agents also modified the same files.
    """
    project_root: Path = ctx.obj["project_root"]
    tracker = _build_evolution_tracker(project_root)

    agent_files = tracker.get_agent_files(agent)
    all_conflicts: list[ConflictInfo] = []
    for fpath in agent_files:
        conflicts = tracker.check_conflicts(fpath)
        all_conflicts.extend(conflicts)

    click.echo(_conflicts_to_json(all_conflicts))


@cli.command("record-gotcha")
@click.option("--agent", required=True, help="Agent ID reporting the issue.")
@click.option("--category", required=True, help="Issue category (e.g. auth, db, deploy).")
@click.option("--description", required=True, help="Description of the recurring issue.")
@click.option("--file", "file_path", default=None, help="Related file path (optional context).")
@click.pass_context
def record_gotcha(
    ctx: click.Context,
    agent: str,
    category: str,
    description: str,
    file_path: str | None,
) -> None:
    """Record an issue in GotchasMemory.

    The context is built from the agent ID and optional file path.
    If the issue reaches the threshold, it is auto-promoted to a gotcha.
    """
    project_root: Path = ctx.obj["project_root"]
    memory = _build_gotchas_memory(project_root)

    # Build context from agent and optional file path
    context_parts: list[str] = [f"agent:{agent}"]
    if file_path:
        context_parts.append(f"file:{file_path}")
    context = ", ".join(context_parts)

    memory.record_issue(
        category=category,
        description=description,
        context=context,
    )

    # Report current state of this issue
    issues = memory.get_issues()
    gotchas = memory.get_gotchas()

    # Check if this specific issue was just promoted
    promoted = any(
        g.description == description and g.category == category
        for g in gotchas
    )

    click.echo(json.dumps({
        "status": "ok",
        "agent": agent,
        "category": category,
        "description": description,
        "promoted": promoted,
        "total_issues": len(issues),
        "total_gotchas": len(gotchas),
    }))


@cli.command("get-gotchas")
@click.option("--agent", required=True, help="Agent ID requesting gotchas.")
@click.option(
    "--min-severity",
    default=None,
    type=click.Choice(["info", "warning", "error"]),
    help="Minimum severity filter (currently filters by occurrence count).",
)
@click.option("--category", default=None, help="Filter by category.")
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Output format: text (for prompt injection) or json.",
)
@click.pass_context
def get_gotchas(
    ctx: click.Context,
    agent: str,
    min_severity: str | None,
    category: str | None,
    output_format: str,
) -> None:
    """Return gotchas for prompt injection.

    In text mode (default), outputs compact markdown suitable for
    injection into agent context. In json mode, outputs structured data.
    The agent parameter identifies who is requesting (used for logging context).
    """
    _ = agent  # Used for CLI consistency; logged in future audit trail
    project_root: Path = ctx.obj["project_root"]
    memory = _build_gotchas_memory(project_root)

    gotchas = memory.get_gotchas(category=category)

    # Apply min-severity filter based on occurrence count
    if min_severity == "warning":
        gotchas = [g for g in gotchas if g.occurrence_count >= 3]
    elif min_severity == "error":
        gotchas = [g for g in gotchas if g.occurrence_count >= 5]
    # "info" = no filtering

    if output_format == "json":
        items: list[dict[str, Any]] = []
        for g in gotchas:
            items.append({
                "category": g.category,
                "description": g.description,
                "context": g.context,
                "occurrence_count": g.occurrence_count,
                "promoted_at": g.promoted_at.isoformat(),
            })
        click.echo(json.dumps(items, indent=2, ensure_ascii=False))
    else:
        # Text mode: use format_for_prompt
        text = memory.format_for_prompt()
        if text:
            click.echo(text)
        else:
            click.echo("")


def main() -> None:
    """Entry point for CLI execution."""
    cli(auto_envvar_prefix="AIOS")  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    main()
