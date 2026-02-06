"""Core utilities for NEO-AIOS.

Provides caching, lazy loading, and profiling utilities for
performance optimization across the framework.

Example:
    >>> from aios.core import Cache, cached, LazyLoader, profile
    >>>
    >>> # Caching
    >>> cache = Cache(default_ttl=300)
    >>> cache.set("key", "value")
    >>>
    >>> # Cached function
    >>> @cached(ttl=60)
    ... def expensive_function(x):
    ...     return x * 2
    >>>
    >>> # Lazy loading
    >>> loader = LazyLoader(lambda: heavy_initialization())
    >>> loader.value  # Initializes on first access
    >>>
    >>> # Profiling
    >>> @profile
    ... def slow_function():
    ...     pass
"""

from aios.core.cache import Cache
from aios.core.cache import CacheEntry
from aios.core.cache import FileCache
from aios.core.cache import cached
from aios.core.cache import clear_default_cache
from aios.core.cache import get_default_cache
from aios.core.glue import GlueGenerator
from aios.core.glue_models import GlueConfig
from aios.core.glue_models import GlueOutput
from aios.core.glue_models import GlueSection
from aios.core.lazy import LazyLoader
from aios.core.lazy import LazyModule
from aios.core.lazy import LazyRegistry
from aios.core.lazy import install_lazy_module
from aios.core.lazy import lazy_import
from aios.core.lazy import lazy_import_from
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
from aios.core.waves import CycleDetectedError
from aios.core.waves import WaveAnalyzer
from aios.core.waves_models import CriticalPath
from aios.core.waves_models import Task
from aios.core.waves_models import Wave
from aios.core.waves_models import WaveAnalysis

__all__ = [
    "Cache",
    "CacheEntry",
    "CriticalPath",
    "CycleDetectedError",
    "FileCache",
    "GlueConfig",
    "GlueGenerator",
    "GlueOutput",
    "GlueSection",
    "LazyLoader",
    "LazyModule",
    "LazyRegistry",
    "Profiler",
    "ProfilerConfig",
    "Task",
    "Timer",
    "TimingMetrics",
    "Wave",
    "WaveAnalysis",
    "WaveAnalyzer",
    "cached",
    "clear_default_cache",
    "configure_profiler",
    "get_default_cache",
    "get_metrics",
    "get_profiler",
    "install_lazy_module",
    "lazy_import",
    "lazy_import_from",
    "profile",
    "reset_metrics",
    "timed",
]
