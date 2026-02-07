"""CLI commands submodule.

This module contains individual command implementations organized by domain.
"""

from aios.cli.commands.agent import agent_group
from aios.cli.commands.conflicts import conflicts_group
from aios.cli.commands.doctor import doctor_group
from aios.cli.commands.gate import gate_group
from aios.cli.commands.glue import glue_group
from aios.cli.commands.gotchas import gotchas_group
from aios.cli.commands.health import health_group
from aios.cli.commands.ids import ids_group
from aios.cli.commands.mcp import mcp_group
from aios.cli.commands.memory import memory_group
from aios.cli.commands.route import route_group
from aios.cli.commands.scan import scan_group
from aios.cli.commands.waves import waves_group

__all__ = [
    "agent_group",
    "conflicts_group",
    "doctor_group",
    "gate_group",
    "glue_group",
    "gotchas_group",
    "health_group",
    "ids_group",
    "mcp_group",
    "memory_group",
    "route_group",
    "scan_group",
    "waves_group",
]
