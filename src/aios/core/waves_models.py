"""Models for wave analysis and parallel task execution."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class Task(BaseModel):
    """A task in the dependency graph."""

    id: str
    name: str
    depends_on: list[str] = Field(default_factory=list)
    estimated_hours: float = 1.0


class Wave(BaseModel):
    """A group of tasks that can execute in parallel."""

    number: int
    tasks: list[Task] = Field(default_factory=list)

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def max_hours(self) -> float:
        if not self.tasks:
            return 0.0
        return max(t.estimated_hours for t in self.tasks)


class CriticalPath(BaseModel):
    """The longest path through the dependency graph."""

    tasks: list[str] = Field(default_factory=list)
    total_hours: float = 0.0


class WaveAnalysis(BaseModel):
    """Complete wave analysis result."""

    waves: list[Wave] = Field(default_factory=list)
    critical_path: CriticalPath = Field(default_factory=CriticalPath)
    total_tasks: int = 0
    total_sequential_hours: float = 0.0
    total_parallel_hours: float = 0.0

    @property
    def parallelism_speedup(self) -> float:
        if self.total_parallel_hours == 0:
            return 0.0
        return self.total_sequential_hours / self.total_parallel_hours

    @property
    def wave_count(self) -> int:
        return len(self.waves)
