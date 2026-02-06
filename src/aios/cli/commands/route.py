"""LLM routing commands for NEO-AIOS CLI."""

import click
from rich.console import Console
from rich.table import Table

from aios.intelligence.router import AGENT_EFFORT_MAP
from aios.intelligence.router import COMPLEXITY_MODEL_MAP
from aios.intelligence.router import TaskRouter

console = Console()
router = TaskRouter()


@click.group(name="route")
def route_group() -> None:
    """LLM routing and task classification."""


@route_group.command(name="classify")
@click.argument("description")
def route_classify(description: str) -> None:
    """Classify a task description to determine model tier."""
    decision = router.classify_by_description(description)

    console.print(f"[bold]Task:[/bold] {description}")
    console.print(f"[bold]Complexity:[/bold] {decision.complexity.value}")
    console.print(f"[bold]Model:[/bold] {decision.model_tier}")
    console.print(f"[bold]Reason:[/bold] {decision.reason}")
    console.print(f"[bold]Confidence:[/bold] {decision.confidence:.0%}")


@route_group.command(name="agent")
@click.argument("agent_id")
def route_agent(agent_id: str) -> None:
    """Show routing for a specific agent."""
    decision = router.classify_by_agent(agent_id)

    console.print(f"[bold]Agent:[/bold] {agent_id}")
    console.print(f"[bold]Effort:[/bold] {decision.complexity.value}")
    console.print(f"[bold]Model:[/bold] {decision.model_tier}")


@route_group.command(name="map")
def route_map() -> None:
    """Show full agent-to-model routing map."""
    table = Table(title="Agent Routing Map")
    table.add_column("Agent", min_width=15)
    table.add_column("Effort", width=10)
    table.add_column("Model", width=10)

    # Group by complexity
    for complexity in ["max", "high", "medium", "low"]:
        agents = [
            a for a, c in AGENT_EFFORT_MAP.items() if c.value == complexity
        ]
        for agent in sorted(agents):
            effort_obj = AGENT_EFFORT_MAP[agent]
            model = COMPLEXITY_MODEL_MAP[effort_obj]
            table.add_row(agent, complexity, model)

    console.print(table)
