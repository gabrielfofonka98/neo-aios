"""CLI commands submodule.

This module contains individual command implementations organized by domain.
"""

from aios.cli.commands.agent import agent_group
from aios.cli.commands.gate import gate_group
from aios.cli.commands.health import health_group
from aios.cli.commands.scan import scan_group

__all__ = [
    "agent_group",
    "gate_group",
    "health_group",
    "scan_group",
]
