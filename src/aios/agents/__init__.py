"""Agent management module.

Provides agent registry, loading, scope enforcement, and delegation rules.
"""

from aios.agents.loader import AgentContextBuilder
from aios.agents.loader import AgentIdentityError
from aios.agents.loader import AgentLoader
from aios.agents.loader import AgentNotFoundError
from aios.agents.models import AgentDefinition
from aios.agents.models import AgentScope
from aios.agents.models import AgentTier
from aios.agents.registry import AgentRegistry

__all__ = [
    "AgentContextBuilder",
    "AgentDefinition",
    "AgentIdentityError",
    "AgentLoader",
    "AgentNotFoundError",
    "AgentRegistry",
    "AgentScope",
    "AgentTier",
]
