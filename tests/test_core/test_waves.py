"""Tests for Wave Analyzer."""

import pytest

from aios.core.waves import CycleDetectedError
from aios.core.waves import WaveAnalyzer
from aios.core.waves_models import CriticalPath
from aios.core.waves_models import Task
from aios.core.waves_models import Wave
from aios.core.waves_models import WaveAnalysis


class TestWaveModels:
    def test_wave_task_count(self) -> None:
        wave = Wave(number=1, tasks=[Task(id="a", name="A")])
        assert wave.task_count == 1

    def test_wave_max_hours(self) -> None:
        wave = Wave(
            number=1,
            tasks=[
                Task(id="a", name="A", estimated_hours=2.0),
                Task(id="b", name="B", estimated_hours=5.0),
            ],
        )
        assert wave.max_hours == 5.0

    def test_wave_empty_max_hours(self) -> None:
        wave = Wave(number=1)
        assert wave.max_hours == 0.0

    def test_analysis_speedup(self) -> None:
        analysis = WaveAnalysis(
            total_sequential_hours=10.0,
            total_parallel_hours=5.0,
        )
        assert analysis.parallelism_speedup == 2.0

    def test_critical_path(self) -> None:
        cp = CriticalPath(tasks=["a", "b", "c"], total_hours=6.0)
        assert len(cp.tasks) == 3


class TestWaveAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = WaveAnalyzer()

    def test_empty_tasks(self) -> None:
        result = self.analyzer.analyze([])
        assert result.wave_count == 0
        assert result.total_tasks == 0

    def test_independent_tasks(self) -> None:
        tasks = [
            Task(id="a", name="A"),
            Task(id="b", name="B"),
            Task(id="c", name="C"),
        ]
        result = self.analyzer.analyze(tasks)
        assert result.wave_count == 1
        assert result.waves[0].task_count == 3

    def test_sequential_tasks(self) -> None:
        tasks = [
            Task(id="a", name="A"),
            Task(id="b", name="B", depends_on=["a"]),
            Task(id="c", name="C", depends_on=["b"]),
        ]
        result = self.analyzer.analyze(tasks)
        assert result.wave_count == 3
        assert result.waves[0].task_count == 1
        assert result.waves[0].tasks[0].id == "a"

    def test_diamond_dependency(self) -> None:
        tasks = [
            Task(id="a", name="A"),
            Task(id="b", name="B", depends_on=["a"]),
            Task(id="c", name="C", depends_on=["a"]),
            Task(id="d", name="D", depends_on=["b", "c"]),
        ]
        result = self.analyzer.analyze(tasks)
        assert result.wave_count == 3
        assert result.waves[1].task_count == 2  # b and c in parallel

    def test_cycle_detection(self) -> None:
        tasks = [
            Task(id="a", name="A", depends_on=["b"]),
            Task(id="b", name="B", depends_on=["a"]),
        ]
        with pytest.raises(CycleDetectedError):
            self.analyzer.analyze(tasks)

    def test_parallelism_speedup(self) -> None:
        tasks = [
            Task(id="a", name="A", estimated_hours=3.0),
            Task(id="b", name="B", estimated_hours=2.0),
            Task(id="c", name="C", estimated_hours=4.0),
        ]
        result = self.analyzer.analyze(tasks)
        assert result.total_sequential_hours == 9.0
        assert result.total_parallel_hours == 4.0
        assert result.parallelism_speedup > 2.0

    def test_critical_path(self) -> None:
        tasks = [
            Task(id="a", name="A", estimated_hours=1.0),
            Task(id="b", name="B", depends_on=["a"], estimated_hours=5.0),
            Task(id="c", name="C", depends_on=["a"], estimated_hours=2.0),
        ]
        result = self.analyzer.analyze(tasks)
        assert "b" in result.critical_path.tasks
