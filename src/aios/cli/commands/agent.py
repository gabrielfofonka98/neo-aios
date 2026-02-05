"""Agent management commands for NEO-AIOS CLI.

This module provides commands for managing agents:
- list: List all available agents
- activate: Activate an agent by ID
- deactivate: Deactivate the current agent
- status: Show current agent status
"""

import click

from aios.cli.output import console
from aios.cli.output import create_table
from aios.cli.output import info
from aios.cli.output import success


@click.group(name="agent")
def agent_group() -> None:
    """Manage agents (activate, deactivate, list, status)."""


@agent_group.command(name="list")
def agent_list() -> None:
    """List all available agents."""
    # TODO: Integrate with AgentRegistry when Story 1.1 is complete
    table = create_table(
        title="Available Agents",
        columns=[
            ("ID", "cyan"),
            ("Name", ""),
            ("Tier", "dim"),
            ("Status", ""),
        ],
        rows=[
            ["dev", "Dex", "IC", "[green]available[/green]"],
            ["architect", "Aria", "VP", "[green]available[/green]"],
            ["devops", "Gage", "IC", "[green]available[/green]"],
            ["qa", "Quinn", "IC", "[green]available[/green]"],
            ["qa-code", "Codex", "IC", "[green]available[/green]"],
            ["doc", "Sage", "IC", "[green]available[/green]"],
        ],
    )
    console.print(table)


@agent_group.command(name="activate")
@click.argument("agent_id")
def activate(agent_id: str) -> None:
    """Activate an agent by ID.

    AGENT_ID: The identifier of the agent to activate.
    """
    # TODO: Integrate with Session when Story 2.1 is complete
    info(f"Activating agent: {agent_id}")
    success(f"Agent '{agent_id}' is now active.")


@agent_group.command(name="deactivate")
def deactivate() -> None:
    """Deactivate the current agent."""
    # TODO: Integrate with Session when Story 2.1 is complete
    success("Agent deactivated. Returning to default Claude.")


@agent_group.command(name="status")
def status() -> None:
    """Show current agent status."""
    # TODO: Integrate with Session when Story 2.1 is complete
    info("No agent currently active.")
