"""Memory module for recurring issue tracking and file evolution monitoring.

Provides GotchasMemory for auto-promoting recurring issues to rules,
FileEvolutionTracker for detecting multi-agent file conflicts,
and hook_bridge for CLI integration with bash hooks.
"""

from aios.memory.file_evolution import ConflictInfo
from aios.memory.file_evolution import DriftReport
from aios.memory.file_evolution import FileEvolutionTracker
from aios.memory.file_evolution import FileModification
from aios.memory.gotchas import Gotcha
from aios.memory.gotchas import GotchasMemory
from aios.memory.gotchas import IssueRecord
from aios.memory.hook_bridge import cli as hook_bridge_cli

__all__ = [
    "ConflictInfo",
    "DriftReport",
    "FileEvolutionTracker",
    "FileModification",
    "Gotcha",
    "GotchasMemory",
    "IssueRecord",
    "hook_bridge_cli",
]
