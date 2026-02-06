"""Wave Analyzer -- topological sort with Kahn's algorithm."""

from __future__ import annotations

from collections import defaultdict
from collections import deque

from aios.core.waves_models import CriticalPath
from aios.core.waves_models import Task
from aios.core.waves_models import Wave
from aios.core.waves_models import WaveAnalysis


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the dependency graph."""


class WaveAnalyzer:
    """Analyzes task dependencies and groups into parallel waves using Kahn's algorithm."""

    def analyze(self, tasks: list[Task]) -> WaveAnalysis:
        """Analyze tasks and produce wave groupings."""
        if not tasks:
            return WaveAnalysis()

        task_map = {t.id: t for t in tasks}
        waves = self._topological_waves(tasks, task_map)
        critical_path = self._find_critical_path(tasks, task_map)

        total_sequential = sum(t.estimated_hours for t in tasks)
        total_parallel = sum(w.max_hours for w in waves)

        return WaveAnalysis(
            waves=waves,
            critical_path=critical_path,
            total_tasks=len(tasks),
            total_sequential_hours=total_sequential,
            total_parallel_hours=total_parallel,
        )

    def _topological_waves(
        self,
        tasks: list[Task],
        task_map: dict[str, Task],
    ) -> list[Wave]:
        """Group tasks into waves using Kahn's algorithm."""
        # Build adjacency and in-degree
        in_degree: dict[str, int] = {t.id: 0 for t in tasks}
        dependents: dict[str, list[str]] = defaultdict(list)

        for task in tasks:
            for dep in task.depends_on:
                if dep in task_map:
                    dependents[dep].append(task.id)
                    in_degree[task.id] += 1

        # Kahn's algorithm with wave grouping
        waves: list[Wave] = []
        queue: deque[str] = deque(
            tid for tid, deg in in_degree.items() if deg == 0
        )
        processed = 0
        wave_num = 1

        while queue:
            # All items in current queue form one wave
            current_wave_ids = list(queue)
            queue.clear()

            wave_tasks = [task_map[tid] for tid in current_wave_ids]
            waves.append(Wave(number=wave_num, tasks=wave_tasks))
            wave_num += 1
            processed += len(current_wave_ids)

            # Process dependents
            for tid in current_wave_ids:
                for dep_id in dependents[tid]:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        queue.append(dep_id)

        if processed != len(tasks):
            raise CycleDetectedError(
                f"Cycle detected: processed {processed}/{len(tasks)} tasks"
            )

        return waves

    def _find_critical_path(
        self,
        tasks: list[Task],
        task_map: dict[str, Task],
    ) -> CriticalPath:
        """Find the longest path through the dependency graph."""
        # Longest path using dynamic programming
        dist: dict[str, float] = {t.id: 0.0 for t in tasks}
        predecessor: dict[str, str | None] = {t.id: None for t in tasks}

        # Process in topological order
        order = self._topological_order(tasks, task_map)

        for tid in order:
            task = task_map[tid]
            new_dist = dist[tid] + task.estimated_hours
            for dep_id in self._get_dependents(tid, tasks):
                if new_dist > dist[dep_id]:
                    dist[dep_id] = new_dist
                    predecessor[dep_id] = tid

        # Find end of critical path
        if not dist:
            return CriticalPath()

        end_id = max(dist, key=lambda k: dist[k] + task_map[k].estimated_hours)
        total = dist[end_id] + task_map[end_id].estimated_hours

        # Trace back
        path: list[str] = [end_id]
        current: str | None = predecessor[end_id]
        while current is not None:
            path.append(current)
            current = predecessor[current]
        path.reverse()

        return CriticalPath(tasks=path, total_hours=total)

    def _topological_order(
        self,
        tasks: list[Task],
        task_map: dict[str, Task],
    ) -> list[str]:
        """Get topological order of tasks."""
        in_degree: dict[str, int] = {t.id: 0 for t in tasks}
        dependents: dict[str, list[str]] = defaultdict(list)

        for task in tasks:
            for dep in task.depends_on:
                if dep in task_map:
                    dependents[dep].append(task.id)
                    in_degree[task.id] += 1

        queue: deque[str] = deque(
            tid for tid, deg in in_degree.items() if deg == 0
        )
        order: list[str] = []

        while queue:
            tid = queue.popleft()
            order.append(tid)
            for dep_id in dependents[tid]:
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    queue.append(dep_id)

        return order

    @staticmethod
    def _get_dependents(task_id: str, tasks: list[Task]) -> list[str]:
        """Get tasks that depend on the given task."""
        return [t.id for t in tasks if task_id in t.depends_on]
