"""Profiling utilities for NEO-AIOS.

Provides decorators and utilities for performance measurement and debugging.
Designed for development-time profiling with minimal production overhead.

Example:
    >>> from aios.core.profiling import profile, Timer, get_metrics
    >>>
    >>> @profile
    ... def slow_function():
    ...     time.sleep(0.1)
    ...     return "done"
    >>>
    >>> slow_function()
    'done'
    >>>
    >>> metrics = get_metrics()
    >>> print(metrics["slow_function"]["avg_time"])
"""

from __future__ import annotations

import functools
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Generator


@dataclass
class TimingMetrics:
    """Timing metrics for a profiled function or block.

    Attributes:
        name: Name of the profiled item.
        call_count: Number of times called.
        total_time: Total time spent in seconds.
        min_time: Minimum execution time.
        max_time: Maximum execution time.
        last_time: Most recent execution time.
    """

    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    last_time: float = 0.0

    @property
    def avg_time(self) -> float:
        """Average execution time.

        Returns:
            Average time in seconds, or 0 if no calls.
        """
        if self.call_count == 0:
            return 0.0
        return self.total_time / self.call_count

    def record(self, duration: float) -> None:
        """Record a new timing measurement.

        Args:
            duration: Execution time in seconds.
        """
        self.call_count += 1
        self.total_time += duration
        self.last_time = duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.call_count = 0
        self.total_time = 0.0
        self.min_time = float("inf")
        self.max_time = 0.0
        self.last_time = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "name": self.name,
            "call_count": self.call_count,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time if self.call_count > 0 else 0.0,
            "max_time": self.max_time,
            "last_time": self.last_time,
        }


@dataclass
class ProfilerConfig:
    """Configuration for the profiler.

    Attributes:
        enabled: Whether profiling is active.
        log_threshold: Only log calls taking longer than this (seconds).
        log_callback: Optional callback for logging.
    """

    enabled: bool = True
    log_threshold: float = 0.0
    log_callback: Callable[[str, float], None] | None = None


class Profiler:
    """Global profiler for collecting timing metrics.

    Thread-safe singleton that collects timing data from all
    @profile decorated functions and Timer contexts.

    Example:
        >>> profiler = get_profiler()
        >>> with profiler.timer("my_operation"):
        ...     do_something()
        >>> print(profiler.metrics)
    """

    _instance: Profiler | None = None
    _lock = threading.Lock()

    def __new__(cls) -> Profiler:
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize profiler."""
        if getattr(self, "_initialized", False):
            return

        self._metrics: dict[str, TimingMetrics] = {}
        self._metrics_lock = threading.Lock()
        self.config = ProfilerConfig()
        self._initialized = True

    def record(self, name: str, duration: float) -> None:
        """Record a timing measurement.

        Args:
            name: Name of the profiled item.
            duration: Execution time in seconds.
        """
        if not self.config.enabled:
            return

        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = TimingMetrics(name=name)
            self._metrics[name].record(duration)

        # Log if above threshold
        if (
            duration >= self.config.log_threshold
            and self.config.log_callback is not None
        ):
            self.config.log_callback(name, duration)

    def get(self, name: str) -> TimingMetrics | None:
        """Get metrics for a specific name.

        Args:
            name: Name to look up.

        Returns:
            Metrics or None.
        """
        with self._metrics_lock:
            return self._metrics.get(name)

    @contextmanager
    def timer(self, name: str) -> Generator[None, None, None]:
        """Context manager for timing a block.

        Args:
            name: Name for the timing.

        Yields:
            Nothing, just times the block.

        Example:
            >>> with profiler.timer("database_query"):
            ...     results = db.query("SELECT * FROM users")
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.record(name, duration)

    @property
    def metrics(self) -> dict[str, dict[str, Any]]:
        """Get all metrics as dictionaries.

        Returns:
            Dictionary of metric dictionaries.
        """
        with self._metrics_lock:
            return {name: m.to_dict() for name, m in self._metrics.items()}

    def reset(self, name: str | None = None) -> None:
        """Reset metrics.

        Args:
            name: Specific metric to reset, or None for all.
        """
        with self._metrics_lock:
            if name is None:
                self._metrics.clear()
            elif name in self._metrics:
                self._metrics[name].reset()

    def summary(self) -> str:
        """Get a formatted summary of all metrics.

        Returns:
            Human-readable summary string.
        """
        with self._metrics_lock:
            if not self._metrics:
                return "No profiling data collected."

            lines = ["Profiling Summary:", "-" * 60]
            for name, m in sorted(self._metrics.items()):
                lines.append(
                    f"{name}: {m.call_count} calls, "
                    f"avg={m.avg_time*1000:.2f}ms, "
                    f"total={m.total_time*1000:.2f}ms"
                )
            return "\n".join(lines)


def get_profiler() -> Profiler:
    """Get the global profiler instance.

    Returns:
        The singleton Profiler instance.
    """
    return Profiler()


def get_metrics() -> dict[str, dict[str, Any]]:
    """Get all profiling metrics.

    Convenience function to access metrics without getting profiler.

    Returns:
        Dictionary of all metrics.
    """
    return get_profiler().metrics


def reset_metrics(name: str | None = None) -> None:
    """Reset profiling metrics.

    Args:
        name: Specific metric to reset, or None for all.
    """
    get_profiler().reset(name)


def profile[F: Callable[..., Any]](
    func: F | None = None,
    *,
    name: str | None = None,
) -> F | Callable[[F], F]:
    """Decorator to profile function execution time.

    Can be used with or without arguments:

        @profile
        def my_function():
            pass

        @profile(name="custom_name")
        def another_function():
            pass

    Args:
        func: Function to wrap (when used without parens).
        name: Custom name for metrics (defaults to function name).

    Returns:
        Decorated function or decorator.
    """
    def decorator(fn: F) -> F:
        metric_name = name or fn.__qualname__
        profiler = get_profiler()

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not profiler.config.enabled:
                return fn(*args, **kwargs)

            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                profiler.record(metric_name, duration)

        return cast("F", wrapper)

    if func is not None:
        return decorator(func)
    return decorator


class Timer:
    """Standalone timer for measuring execution time.

    Can be used as context manager or manually started/stopped.

    Example:
        >>> # As context manager
        >>> with Timer() as t:
        ...     do_something()
        >>> print(f"Took {t.elapsed:.3f}s")
        >>>
        >>> # Manual control
        >>> timer = Timer()
        >>> timer.start()
        >>> do_something()
        >>> timer.stop()
        >>> print(f"Took {timer.elapsed:.3f}s")
    """

    def __init__(self, name: str | None = None, auto_record: bool = False) -> None:
        """Initialize timer.

        Args:
            name: Optional name for auto-recording to profiler.
            auto_record: Whether to auto-record to profiler on stop.
        """
        self.name = name
        self.auto_record = auto_record
        self._start_time: float | None = None
        self._end_time: float | None = None

    def start(self) -> Timer:
        """Start the timer.

        Returns:
            Self for chaining.
        """
        self._start_time = time.perf_counter()
        self._end_time = None
        return self

    def stop(self) -> float:
        """Stop the timer.

        Returns:
            Elapsed time in seconds.
        """
        self._end_time = time.perf_counter()

        if self.auto_record and self.name:
            get_profiler().record(self.name, self.elapsed)

        return self.elapsed

    @property
    def elapsed(self) -> float:
        """Get elapsed time.

        Returns:
            Elapsed time in seconds.
        """
        if self._start_time is None:
            return 0.0

        end = self._end_time or time.perf_counter()
        return end - self._start_time

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds.

        Returns:
            Elapsed time in milliseconds.
        """
        return self.elapsed * 1000

    @property
    def is_running(self) -> bool:
        """Check if timer is currently running.

        Returns:
            True if started but not stopped.
        """
        return self._start_time is not None and self._end_time is None

    def __enter__(self) -> Timer:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.stop()

    def __repr__(self) -> str:
        """String representation."""
        if self._start_time is None:
            return "Timer(not started)"
        if self.is_running:
            return f"Timer(running, {self.elapsed:.3f}s)"
        return f"Timer(stopped, {self.elapsed:.3f}s)"


@contextmanager
def timed(name: str | None = None) -> Generator[Timer, None, None]:
    """Context manager for timing with optional auto-recording.

    Args:
        name: If provided, records to profiler.

    Yields:
        Timer instance.

    Example:
        >>> with timed("database_query") as t:
        ...     result = db.query(...)
        >>> print(f"Query took {t.elapsed_ms:.2f}ms")
    """
    timer = Timer(name=name, auto_record=name is not None)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()


def configure_profiler(
    *,
    enabled: bool | None = None,
    log_threshold: float | None = None,
    log_callback: Callable[[str, float], None] | None = None,
) -> None:
    """Configure the global profiler.

    Args:
        enabled: Enable/disable profiling.
        log_threshold: Minimum time to log (seconds).
        log_callback: Callback for logging slow operations.
    """
    profiler = get_profiler()

    if enabled is not None:
        profiler.config.enabled = enabled
    if log_threshold is not None:
        profiler.config.log_threshold = log_threshold
    if log_callback is not None:
        profiler.config.log_callback = log_callback
