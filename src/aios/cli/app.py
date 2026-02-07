"""Click application factory for NEO-AIOS CLI.

This module defines the main Click application and command groups.
"""

import sys

import click

import aios
from aios.cli.commands import agent_group
from aios.cli.commands import conflicts_group
from aios.cli.commands import doctor_group
from aios.cli.commands import gate_group
from aios.cli.commands import glue_group
from aios.cli.commands import gotchas_group
from aios.cli.commands import health_group
from aios.cli.commands import ids_group
from aios.cli.commands import mcp_group
from aios.cli.commands import memory_group
from aios.cli.commands import route_group
from aios.cli.commands import scan_group
from aios.cli.commands import waves_group
from aios.cli.output import print_version


class AIOSGroup(click.Group):
    """Custom Click group with enhanced help formatting."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Format help text with NEO-AIOS branding.

        Args:
            ctx: Click context.
            formatter: Help formatter.
        """
        formatter.write_paragraph()
        formatter.write_text(
            "NEO-AIOS - Agent Intelligence Operating System\n"
            "A multi-agent development environment with Big Tech hierarchy."
        )
        formatter.write_paragraph()

        # Commands section
        super().format_help(ctx, formatter)


def create_app() -> click.Group:
    """Create the main CLI application.

    Returns:
        The configured Click group.
    """

    @click.group(cls=AIOSGroup)
    @click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose output.",
    )
    @click.option(
        "--quiet",
        "-q",
        is_flag=True,
        help="Suppress non-essential output.",
    )
    @click.pass_context
    def cli_group(ctx: click.Context, verbose: bool, quiet: bool) -> None:
        """NEO-AIOS: Agent Intelligence Operating System.

        A Python framework that transforms Claude Code into a managed
        multi-agent development environment.
        """
        ctx.ensure_object(dict)
        ctx.obj["verbose"] = verbose
        ctx.obj["quiet"] = quiet

    # Register version command
    @cli_group.command(name="version")
    def version() -> None:
        """Show version information."""
        python_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        print_version(aios.__version__, python_version)

    # Register command groups
    cli_group.add_command(agent_group)
    cli_group.add_command(conflicts_group)
    cli_group.add_command(doctor_group)
    cli_group.add_command(gate_group)
    cli_group.add_command(glue_group)
    cli_group.add_command(gotchas_group)
    cli_group.add_command(health_group)
    cli_group.add_command(ids_group)
    cli_group.add_command(mcp_group)
    cli_group.add_command(memory_group)
    cli_group.add_command(route_group)
    cli_group.add_command(scan_group)
    cli_group.add_command(waves_group)

    return cli_group


# Create the CLI instance for the entry point
cli = create_app()
