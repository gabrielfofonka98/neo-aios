"""Tests for profiling module."""

import time

import pytest

from aios.core.profiling import Profiler
from aios.core.profiling import ProfilerConfig
from aios.core.profiling import Timer
from aios.core.profiling import TimingMetrics
from aios.core.profiling import configure_profiler
from aios.core.profiling import get_metrics
from aios.core.profiling import get_profiler
from aios.core.profiling import profile
from aios.core.profiling import reset_metrics
from aios.core.profiling import timed


class TestTimingMetrics:
    """Tests for TimingMetrics dataclass."""

    def test_initial_state(self) -> None:
        """New metrics should have zero counts."""
        metrics = TimingMetrics(name="test")
        assert metrics.call_count == 0
        assert metrics.total_time == 0.0
        assert metrics.avg_time == 0.0

    def test_record_updates_stats(self) -> None:
        """Record should update all statistics."""
        metrics = TimingMetrics(name="test")
        metrics.record(0.1)
        assert metrics.call_count == 1
        assert metrics.total_time == pytest.approx(0.1, abs=0.001)
        assert metrics.last_time == pytest.approx(0.1, abs=0.001)
        assert metrics.min_time == pytest.approx(0.1, abs=0.001)
        assert metrics.max_time == pytest.approx(0.1, abs=0.001)

    def test_avg_time_calculation(self) -> None:
        """Average should be correctly calculated."""
        metrics = TimingMetrics(name="test")
        metrics.record(0.1)
        metrics.record(0.3)
        assert metrics.avg_time == pytest.approx(0.2, abs=0.001)

    def test_min_max_tracking(self) -> None:
        """Min and max should be tracked correctly."""
        metrics = TimingMetrics(name="test")
        metrics.record(0.2)
        metrics.record(0.1)
        metrics.record(0.3)
        assert metrics.min_time == pytest.approx(0.1, abs=0.001)
        assert metrics.max_time == pytest.approx(0.3, abs=0.001)

    def test_reset(self) -> None:
        """Reset should clear all statistics."""
        metrics = TimingMetrics(name="test")
        metrics.record(0.1)
        metrics.reset()
        assert metrics.call_count == 0
        assert metrics.total_time == 0.0

    def test_to_dict(self) -> None:
        """to_dict should return all fields."""
        metrics = TimingMetrics(name="test")
        metrics.record(0.1)
        data = metrics.to_dict()
        assert data["name"] == "test"
        assert data["call_count"] == 1
        assert "total_time" in data
        assert "avg_time" in data
        assert "min_time" in data
        assert "max_time" in data


class TestTimer:
    """Tests for Timer class."""

    def test_basic_timing(self) -> None:
        """Timer should measure elapsed time."""
        timer = Timer()
        timer.start()
        time.sleep(0.01)
        timer.stop()
        assert timer.elapsed >= 0.01
        assert timer.elapsed < 0.05  # Reasonable upper bound

    def test_elapsed_ms(self) -> None:
        """elapsed_ms should return milliseconds."""
        timer = Timer()
        timer.start()
        time.sleep(0.01)
        timer.stop()
        assert timer.elapsed_ms >= 10
        assert timer.elapsed_ms < 50

    def test_context_manager(self) -> None:
        """Timer should work as context manager."""
        with Timer() as t:
            time.sleep(0.01)
        assert t.elapsed >= 0.01

    def test_is_running(self) -> None:
        """is_running should reflect state."""
        timer = Timer()
        assert not timer.is_running
        timer.start()
        assert timer.is_running
        timer.stop()
        assert not timer.is_running

    def test_elapsed_while_running(self) -> None:
        """elapsed should return current time while running."""
        timer = Timer()
        timer.start()
        time.sleep(0.01)
        assert timer.is_running
        assert timer.elapsed >= 0.01

    def test_auto_record(self) -> None:
        """auto_record should record to profiler."""
        reset_metrics()
        timer = Timer(name="test_timer", auto_record=True)
        timer.start()
        time.sleep(0.01)
        timer.stop()

        metrics = get_metrics()
        assert "test_timer" in metrics
        assert metrics["test_timer"]["call_count"] == 1

    def test_repr(self) -> None:
        """Repr should show state."""
        timer = Timer()
        assert "not started" in repr(timer)
        timer.start()
        assert "running" in repr(timer)
        timer.stop()
        assert "stopped" in repr(timer)


class TestProfiler:
    """Tests for Profiler class."""

    def test_singleton(self) -> None:
        """Profiler should be singleton."""
        p1 = Profiler()
        p2 = Profiler()
        assert p1 is p2

    def test_record_creates_metrics(self) -> None:
        """record should create metrics for new names."""
        profiler = get_profiler()
        reset_metrics()
        profiler.record("new_metric", 0.1)
        assert profiler.get("new_metric") is not None

    def test_record_updates_metrics(self) -> None:
        """record should update existing metrics."""
        profiler = get_profiler()
        reset_metrics()
        profiler.record("metric", 0.1)
        profiler.record("metric", 0.2)
        metrics = profiler.get("metric")
        assert metrics is not None
        assert metrics.call_count == 2

    def test_timer_context_manager(self) -> None:
        """timer should time a block."""
        profiler = get_profiler()
        reset_metrics()

        with profiler.timer("timed_block"):
            time.sleep(0.01)

        metrics = profiler.get("timed_block")
        assert metrics is not None
        assert metrics.total_time >= 0.01

    def test_metrics_property(self) -> None:
        """metrics should return dict of all metrics."""
        profiler = get_profiler()
        reset_metrics()
        profiler.record("a", 0.1)
        profiler.record("b", 0.2)

        metrics = profiler.metrics
        assert "a" in metrics
        assert "b" in metrics

    def test_reset_specific(self) -> None:
        """reset with name should only reset that metric."""
        profiler = get_profiler()
        reset_metrics()
        profiler.record("a", 0.1)
        profiler.record("b", 0.2)
        profiler.reset("a")

        a_metrics = profiler.get("a")
        b_metrics = profiler.get("b")
        assert a_metrics is not None
        assert a_metrics.call_count == 0
        assert b_metrics is not None
        assert b_metrics.call_count == 1

    def test_reset_all(self) -> None:
        """reset without name should clear all."""
        profiler = get_profiler()
        reset_metrics()
        profiler.record("a", 0.1)
        profiler.record("b", 0.2)
        profiler.reset()

        assert len(profiler.metrics) == 0

    def test_summary(self) -> None:
        """summary should return formatted string."""
        profiler = get_profiler()
        reset_metrics()
        profiler.record("test_func", 0.1)

        summary = profiler.summary()
        assert "test_func" in summary
        assert "1 calls" in summary

    def test_disabled_profiler(self) -> None:
        """Disabled profiler should not record."""
        profiler = get_profiler()
        reset_metrics()
        profiler.config.enabled = False
        profiler.record("should_not_record", 0.1)
        profiler.config.enabled = True

        assert profiler.get("should_not_record") is None


class TestProfileDecorator:
    """Tests for @profile decorator."""

    def test_basic_profiling(self) -> None:
        """Decorator should profile function."""
        reset_metrics()

        @profile
        def test_function() -> str:
            time.sleep(0.01)
            return "done"

        result = test_function()
        assert result == "done"

        metrics = get_metrics()
        # Function name includes module
        matching = [k for k in metrics if "test_function" in k]
        assert len(matching) == 1
        assert metrics[matching[0]]["call_count"] == 1

    def test_custom_name(self) -> None:
        """Decorator should use custom name."""
        reset_metrics()

        @profile(name="custom_metric")
        def func() -> None:
            pass

        func()
        metrics = get_metrics()
        assert "custom_metric" in metrics

    def test_preserves_return_value(self) -> None:
        """Decorator should not alter return value."""

        @profile
        def returns_value() -> dict[str, int]:
            return {"a": 1, "b": 2}

        result = returns_value()
        assert result == {"a": 1, "b": 2}

    def test_tracks_multiple_calls(self) -> None:
        """Decorator should track multiple calls."""
        reset_metrics()

        @profile(name="multi_call")
        def func() -> None:
            pass

        func()
        func()
        func()

        metrics = get_metrics()
        assert metrics["multi_call"]["call_count"] == 3

    def test_disabled_profiler_still_runs_function(self) -> None:
        """Function should run even when profiler disabled."""
        profiler = get_profiler()
        profiler.config.enabled = False
        reset_metrics()

        @profile
        def must_run() -> str:
            return "executed"

        result = must_run()
        assert result == "executed"
        profiler.config.enabled = True


class TestTimedContextManager:
    """Tests for timed() context manager."""

    def test_basic_timing(self) -> None:
        """timed should measure block time."""
        with timed() as t:
            time.sleep(0.01)

        assert t.elapsed >= 0.01

    def test_auto_records_when_named(self) -> None:
        """timed with name should record to profiler."""
        reset_metrics()

        with timed("named_block"):
            time.sleep(0.01)

        metrics = get_metrics()
        assert "named_block" in metrics


class TestConfigureProfiler:
    """Tests for configure_profiler function."""

    def test_enable_disable(self) -> None:
        """configure_profiler should set enabled."""
        configure_profiler(enabled=False)
        assert get_profiler().config.enabled is False
        configure_profiler(enabled=True)
        assert get_profiler().config.enabled is True

    def test_log_threshold(self) -> None:
        """configure_profiler should set log_threshold."""
        configure_profiler(log_threshold=0.5)
        assert get_profiler().config.log_threshold == 0.5
        configure_profiler(log_threshold=0.0)

    def test_log_callback(self) -> None:
        """configure_profiler should set log_callback."""
        logged: list[tuple[str, float]] = []

        def callback(name: str, duration: float) -> None:
            logged.append((name, duration))

        configure_profiler(log_threshold=0.0, log_callback=callback)
        get_profiler().record("test", 0.1)

        assert len(logged) == 1
        assert logged[0][0] == "test"

        # Cleanup
        configure_profiler(log_callback=None)


class TestGetMetricsAndResetMetrics:
    """Tests for utility functions."""

    def test_get_metrics(self) -> None:
        """get_metrics should return profiler metrics."""
        reset_metrics()
        get_profiler().record("test", 0.1)
        metrics = get_metrics()
        assert "test" in metrics

    def test_reset_metrics_all(self) -> None:
        """reset_metrics without name should clear all."""
        get_profiler().record("a", 0.1)
        get_profiler().record("b", 0.2)
        reset_metrics()
        assert len(get_metrics()) == 0

    def test_reset_metrics_specific(self) -> None:
        """reset_metrics with name should only reset that."""
        reset_metrics()
        get_profiler().record("a", 0.1)
        get_profiler().record("b", 0.2)
        reset_metrics("a")

        metrics = get_metrics()
        assert "a" in metrics
        assert metrics["a"]["call_count"] == 0
        assert metrics["b"]["call_count"] == 1
