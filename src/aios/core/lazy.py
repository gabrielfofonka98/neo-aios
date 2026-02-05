"""Lazy loading utilities for NEO-AIOS.

Provides lazy import and initialization utilities to defer expensive
operations until they are actually needed, improving startup time.

Example:
    >>> from aios.core.lazy import LazyLoader, lazy_import
    >>>
    >>> # Lazy import heavy modules
    >>> tree_sitter = lazy_import("tree_sitter")
    >>> # Module not loaded yet...
    >>> tree_sitter.Parser()  # Now it loads
    >>>
    >>> # Lazy initialization
    >>> loader = LazyLoader(lambda: expensive_init())
    >>> loader.value  # Initializes on first access
"""

from __future__ import annotations

import importlib
import sys
import threading
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType


class LazyLoader[T]:
    """Lazy loader that defers initialization until first access.

    Thread-safe lazy initialization wrapper. The factory function
    is called exactly once, on first access to the value.

    Attributes:
        _factory: Function that creates the value.
        _value: Cached value after initialization.
        _initialized: Whether value has been created.

    Example:
        >>> def expensive_init():
        ...     print("Initializing...")
        ...     return {"data": 123}
        >>>
        >>> loader = LazyLoader(expensive_init)
        >>> # Nothing printed yet
        >>> print(loader.value)  # Now prints "Initializing..."
        {'data': 123}
        >>> print(loader.value)  # Uses cached value
        {'data': 123}
    """

    def __init__(self, factory: Callable[[], T]) -> None:
        """Initialize lazy loader.

        Args:
            factory: Callable that creates the value when needed.
        """
        self._factory = factory
        self._value: T | None = None
        self._initialized = False
        self._lock = threading.Lock()

    @property
    def value(self) -> T:
        """Get the value, initializing if needed.

        Thread-safe lazy initialization using double-checked locking.

        Returns:
            The initialized value.
        """
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._value = self._factory()
                    self._initialized = True
        # _value is guaranteed to be set after _initialized is True
        return self._value  # type: ignore[return-value]

    @property
    def is_initialized(self) -> bool:
        """Check if value has been initialized.

        Returns:
            True if value has been created.
        """
        return self._initialized

    def reset(self) -> None:
        """Reset loader to uninitialized state.

        The next access to value will re-run the factory.
        """
        with self._lock:
            self._value = None
            self._initialized = False

    def __repr__(self) -> str:
        """String representation."""
        status = "initialized" if self._initialized else "pending"
        return f"LazyLoader({status})"


class LazyModule:
    """Lazy module wrapper that imports on first attribute access.

    Provides transparent lazy loading of Python modules. The actual
    import only happens when an attribute is accessed.

    Attributes:
        _module_name: Full module name to import.
        _module: Cached module after import.
        _package: Optional package for relative imports.

    Example:
        >>> numpy = LazyModule("numpy")
        >>> # numpy not imported yet
        >>> numpy.array([1, 2, 3])  # Now imports and uses
        array([1, 2, 3])
    """

    def __init__(self, module_name: str, package: str | None = None) -> None:
        """Initialize lazy module.

        Args:
            module_name: Name of module to import.
            package: Package for relative imports.
        """
        # Use object.__setattr__ to avoid triggering __setattr__
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_module", None)
        object.__setattr__(self, "_package", package)
        object.__setattr__(self, "_lock", threading.Lock())

    def _load_module(self) -> ModuleType:
        """Load the module if not already loaded.

        Returns:
            The loaded module.
        """
        module: ModuleType | None = object.__getattribute__(self, "_module")
        if module is not None:
            return module

        lock: threading.Lock = object.__getattribute__(self, "_lock")
        with lock:
            # Double-check after acquiring lock
            module = object.__getattribute__(self, "_module")
            if module is not None:
                return module

            module_name: str = object.__getattribute__(self, "_module_name")
            package: str | None = object.__getattribute__(self, "_package")
            module = importlib.import_module(module_name, package)
            object.__setattr__(self, "_module", module)
            return module

    def __getattr__(self, name: str) -> Any:
        """Get attribute from the lazily loaded module.

        Args:
            name: Attribute name.

        Returns:
            Attribute from the module.
        """
        module = self._load_module()
        return getattr(module, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute on the lazily loaded module.

        Args:
            name: Attribute name.
            value: Value to set.
        """
        module = self._load_module()
        setattr(module, name, value)

    def __dir__(self) -> list[str]:
        """List attributes of the lazily loaded module.

        Returns:
            List of attribute names.
        """
        module = self._load_module()
        return dir(module)

    def __repr__(self) -> str:
        """String representation."""
        module_name = object.__getattribute__(self, "_module_name")
        module = object.__getattribute__(self, "_module")
        status = "loaded" if module is not None else "pending"
        return f"LazyModule({module_name!r}, {status})"


def lazy_import(module_name: str, package: str | None = None) -> LazyModule:
    """Create a lazy module import.

    The module is not actually imported until an attribute is accessed.
    This can significantly improve startup time for heavy modules.

    Args:
        module_name: Name of module to import.
        package: Package for relative imports.

    Returns:
        LazyModule wrapper that imports on first use.

    Example:
        >>> pandas = lazy_import("pandas")
        >>> # pandas not loaded yet
        >>> df = pandas.DataFrame({"a": [1, 2, 3]})  # Now imports
    """
    return LazyModule(module_name, package)


def lazy_import_from(
    module_name: str,
    attribute: str,
    package: str | None = None,
) -> LazyLoader[Any]:
    """Lazily import a specific attribute from a module.

    Args:
        module_name: Name of module containing the attribute.
        attribute: Name of attribute to import.
        package: Package for relative imports.

    Returns:
        LazyLoader that imports and returns the attribute.

    Example:
        >>> DataFrame = lazy_import_from("pandas", "DataFrame")
        >>> # pandas not loaded yet
        >>> df = DataFrame.value({"a": [1, 2, 3]})  # Now imports
    """
    def factory() -> Any:
        module = importlib.import_module(module_name, package)
        return getattr(module, attribute)

    return LazyLoader(factory)


class LazyRegistry[T]:
    """Registry with lazy initialization of entries.

    Values are computed lazily when first requested. Useful for
    registries where computing all values upfront is expensive.

    Example:
        >>> def make_validator(vid):
        ...     print(f"Creating {vid}")
        ...     return Validator(vid)
        >>>
        >>> registry = LazyRegistry()
        >>> registry.register("v1", lambda: make_validator("v1"))
        >>> registry.register("v2", lambda: make_validator("v2"))
        >>> # Nothing created yet
        >>> registry.get("v1")  # Creates v1
        Creating v1
        >>> registry.get("v1")  # Uses cached
    """

    def __init__(self) -> None:
        """Initialize empty lazy registry."""
        self._factories: dict[str, Callable[[], T]] = {}
        self._values: dict[str, T] = {}
        self._lock = threading.Lock()

    def register(self, key: str, factory: Callable[[], T]) -> None:
        """Register a lazy value.

        Args:
            key: Unique key for the value.
            factory: Callable that creates the value.
        """
        with self._lock:
            self._factories[key] = factory
            # Clear cached value if re-registering
            self._values.pop(key, None)

    def get(self, key: str) -> T | None:
        """Get value by key, initializing if needed.

        Args:
            key: Key to look up.

        Returns:
            The value, or None if key not found.
        """
        with self._lock:
            # Check cached values first
            if key in self._values:
                return self._values[key]

            # Check if factory exists
            factory = self._factories.get(key)
            if factory is None:
                return None

            # Initialize and cache
            value = factory()
            self._values[key] = value
            return value

    def get_all(self) -> dict[str, T]:
        """Get all values, initializing all that haven't been.

        Returns:
            Dictionary of all key-value pairs.
        """
        with self._lock:
            for key in self._factories:
                if key not in self._values:
                    self._values[key] = self._factories[key]()
            return dict(self._values)

    def get_initialized(self) -> dict[str, T]:
        """Get only already-initialized values.

        Returns:
            Dictionary of initialized key-value pairs.
        """
        with self._lock:
            return dict(self._values)

    def is_initialized(self, key: str) -> bool:
        """Check if a key's value has been initialized.

        Args:
            key: Key to check.

        Returns:
            True if value has been created.
        """
        with self._lock:
            return key in self._values

    def has(self, key: str) -> bool:
        """Check if key is registered (not necessarily initialized).

        Args:
            key: Key to check.

        Returns:
            True if key has a factory registered.
        """
        with self._lock:
            return key in self._factories

    def keys(self) -> list[str]:
        """Get all registered keys.

        Returns:
            List of keys.
        """
        with self._lock:
            return list(self._factories.keys())

    def clear(self) -> None:
        """Clear all registrations and cached values."""
        with self._lock:
            self._factories.clear()
            self._values.clear()

    def reset(self, key: str | None = None) -> None:
        """Reset cached value(s) without removing registration.

        Args:
            key: Specific key to reset, or None for all.
        """
        with self._lock:
            if key is None:
                self._values.clear()
            else:
                self._values.pop(key, None)

    @property
    def size(self) -> int:
        """Number of registered keys."""
        with self._lock:
            return len(self._factories)

    @property
    def initialized_count(self) -> int:
        """Number of initialized values."""
        with self._lock:
            return len(self._values)

    def __contains__(self, key: str) -> bool:
        """Check if key is registered."""
        return self.has(key)

    def __len__(self) -> int:
        """Number of registered keys."""
        return self.size

    def __repr__(self) -> str:
        """String representation."""
        return f"LazyRegistry(registered={self.size}, initialized={self.initialized_count})"


def install_lazy_module(module_name: str, package: str | None = None) -> None:
    """Install a lazy module in sys.modules.

    This makes the lazy module available for regular import statements.
    Use with caution as it modifies sys.modules.

    Args:
        module_name: Name of module to install lazily.
        package: Package for relative imports.

    Example:
        >>> install_lazy_module("heavy_module")
        >>> import heavy_module  # Won't actually load yet
        >>> heavy_module.function()  # Now loads
    """
    if module_name not in sys.modules:
        sys.modules[module_name] = LazyModule(module_name, package)  # type: ignore[assignment]
