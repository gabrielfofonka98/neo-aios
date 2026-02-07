"""Memory module for recurring issue tracking and file evolution monitoring.

Provides GotchasMemory for auto-promoting recurring issues to rules,
and FileEvolutionTracker for detecting multi-agent file conflicts.
"""

from aios.memory.file_evolution import ConflictInfo
from aios.memory.file_evolution import DriftReport
from aios.memory.file_evolution import FileEvolutionTracker
from aios.memory.file_evolution import FileModification
from aios.memory.gotchas import Gotcha
from aios.memory.gotchas import GotchasMemory
from aios.memory.gotchas import IssueRecord

__all__ = [
    "ConflictInfo",
    "DriftReport",
    "FileEvolutionTracker",
    "FileModification",
    "Gotcha",
    "GotchasMemory",
    "IssueRecord",
]
