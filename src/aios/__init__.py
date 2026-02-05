"""NEO-AIOS: Agent Intelligence Operating System.

A Python framework that transforms Claude Code into a managed multi-agent
development environment with Big Tech organizational structure.

Example:
    >>> from aios.agents import AgentRegistry
    >>> registry = AgentRegistry.load()
    >>> dev = registry.get("dev")
    >>> dev.name
    'Dex'
"""

__version__ = "0.1.0"
__author__ = "Gabriel Fofonka"

from aios.agents.registry import AgentRegistry
from aios.context.session import Session

__all__ = [
    "AgentRegistry",
    "Session",
    "__version__",
]
