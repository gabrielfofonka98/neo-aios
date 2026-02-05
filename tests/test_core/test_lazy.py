"""Tests for lazy loading module."""

import sys
from unittest.mock import MagicMock

import pytest

from aios.core.lazy import LazyLoader
from aios.core.lazy import LazyModule
from aios.core.lazy import LazyRegistry
from aios.core.lazy import install_lazy_module
from aios.core.lazy import lazy_import
from aios.core.lazy import lazy_import_from


class TestLazyLoader:
    """Tests for LazyLoader class."""

    def test_defers_initialization(self) -> None:
        """Factory should not be called until value accessed."""
        called = False

        def factory() -> str:
            nonlocal called
            called = True
            return "result"

        loader = LazyLoader(factory)
        assert not called
        assert not loader.is_initialized
        _ = loader.value
        assert called
        assert loader.is_initialized

    def test_returns_correct_value(self) -> None:
        """Value should be result of factory."""
        loader = LazyLoader(lambda: {"data": 123})
        assert loader.value == {"data": 123}

    def test_caches_value(self) -> None:
        """Factory should be called only once."""
        call_count = 0

        def factory() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        loader = LazyLoader(factory)
        assert loader.value == 1
        assert loader.value == 1
        assert loader.value == 1
        assert call_count == 1

    def test_reset_allows_reinit(self) -> None:
        """Reset should allow re-initialization."""
        call_count = 0

        def factory() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        loader = LazyLoader(factory)
        assert loader.value == 1
        loader.reset()
        assert not loader.is_initialized
        assert loader.value == 2

    def test_repr(self) -> None:
        """Repr should show initialization status."""
        loader = LazyLoader(lambda: None)
        assert "pending" in repr(loader)
        _ = loader.value
        assert "initialized" in repr(loader)


class TestLazyModule:
    """Tests for LazyModule class."""

    def test_defers_import(self) -> None:
        """Module should not be imported until attribute access."""
        # Use a stdlib module that's definitely available
        lazy_mod = LazyModule("json")
        # Module not loaded yet (in this wrapper)
        assert object.__getattribute__(lazy_mod, "_module") is None

    def test_loads_on_attribute_access(self) -> None:
        """Module should load when attribute accessed."""
        lazy_mod = LazyModule("json")
        # Access an attribute
        dumps = lazy_mod.dumps
        assert callable(dumps)
        # Now module is loaded
        assert object.__getattribute__(lazy_mod, "_module") is not None

    def test_attribute_access_works(self) -> None:
        """Should be able to use module attributes normally."""
        lazy_mod = LazyModule("json")
        result = lazy_mod.dumps({"a": 1})
        assert result == '{"a": 1}'

    def test_dir_returns_module_attrs(self) -> None:
        """dir() should return module's attributes."""
        lazy_mod = LazyModule("json")
        attrs = dir(lazy_mod)
        assert "dumps" in attrs
        assert "loads" in attrs

    def test_repr(self) -> None:
        """Repr should show module name and status."""
        lazy_mod = LazyModule("json")
        assert "json" in repr(lazy_mod)
        assert "pending" in repr(lazy_mod)
        _ = lazy_mod.dumps
        assert "loaded" in repr(lazy_mod)


class TestLazyImport:
    """Tests for lazy_import function."""

    def test_returns_lazy_module(self) -> None:
        """lazy_import should return LazyModule."""
        result = lazy_import("json")
        assert isinstance(result, LazyModule)

    def test_module_works(self) -> None:
        """Lazy imported module should work."""
        json_mod = lazy_import("json")
        data = json_mod.loads('{"key": "value"}')
        assert data == {"key": "value"}


class TestLazyImportFrom:
    """Tests for lazy_import_from function."""

    def test_returns_lazy_loader(self) -> None:
        """lazy_import_from should return LazyLoader."""
        result = lazy_import_from("json", "dumps")
        assert isinstance(result, LazyLoader)

    def test_defers_import(self) -> None:
        """Import should be deferred."""
        loader = lazy_import_from("json", "dumps")
        assert not loader.is_initialized

    def test_gets_correct_attribute(self) -> None:
        """Should get the correct attribute from module."""
        loader = lazy_import_from("json", "dumps")
        dumps = loader.value
        assert callable(dumps)
        result = dumps({"a": 1})
        assert result == '{"a": 1}'


class TestLazyRegistry:
    """Tests for LazyRegistry class."""

    def test_register_and_get(self) -> None:
        """Should register and retrieve values lazily."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("key1", lambda: "value1")
        assert registry.has("key1")
        assert registry.get("key1") == "value1"

    def test_defers_creation(self) -> None:
        """Factory should not be called until get."""
        called = False

        def factory() -> str:
            nonlocal called
            called = True
            return "value"

        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("key", factory)
        assert not called
        registry.get("key")
        assert called

    def test_caches_value(self) -> None:
        """Factory should be called only once."""
        call_count = 0

        def factory() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        registry: LazyRegistry[int] = LazyRegistry()
        registry.register("key", factory)
        assert registry.get("key") == 1
        assert registry.get("key") == 1
        assert call_count == 1

    def test_get_returns_none_for_missing(self) -> None:
        """Get should return None for unregistered key."""
        registry: LazyRegistry[str] = LazyRegistry()
        assert registry.get("missing") is None

    def test_get_all_initializes_all(self) -> None:
        """get_all should initialize and return all values."""
        call_count = 0

        def make_factory(val: str) -> str:
            nonlocal call_count
            call_count += 1
            return val

        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("a", lambda: make_factory("A"))
        registry.register("b", lambda: make_factory("B"))

        result = registry.get_all()
        assert result == {"a": "A", "b": "B"}
        assert call_count == 2

    def test_get_initialized_only_returns_initialized(self) -> None:
        """get_initialized should only return already-initialized values."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("a", lambda: "A")
        registry.register("b", lambda: "B")
        registry.get("a")  # Initialize only 'a'

        result = registry.get_initialized()
        assert result == {"a": "A"}

    def test_is_initialized(self) -> None:
        """is_initialized should return correct status."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("key", lambda: "value")
        assert not registry.is_initialized("key")
        registry.get("key")
        assert registry.is_initialized("key")

    def test_has(self) -> None:
        """has should check if key is registered."""
        registry: LazyRegistry[str] = LazyRegistry()
        assert not registry.has("key")
        registry.register("key", lambda: "value")
        assert registry.has("key")

    def test_keys(self) -> None:
        """keys should return all registered keys."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("a", lambda: "A")
        registry.register("b", lambda: "B")
        assert sorted(registry.keys()) == ["a", "b"]

    def test_clear(self) -> None:
        """clear should remove all registrations."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("key", lambda: "value")
        registry.get("key")
        registry.clear()
        assert registry.size == 0
        assert registry.initialized_count == 0

    def test_reset_specific_key(self) -> None:
        """reset with key should only reset that key."""
        call_count = 0

        def factory() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        registry: LazyRegistry[int] = LazyRegistry()
        registry.register("key", factory)
        assert registry.get("key") == 1
        registry.reset("key")
        assert not registry.is_initialized("key")
        assert registry.get("key") == 2

    def test_reset_all(self) -> None:
        """reset without key should reset all."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("a", lambda: "A")
        registry.register("b", lambda: "B")
        registry.get("a")
        registry.get("b")
        assert registry.initialized_count == 2
        registry.reset()
        assert registry.initialized_count == 0
        assert registry.size == 2  # Still registered

    def test_size_property(self) -> None:
        """size should return number of registered keys."""
        registry: LazyRegistry[str] = LazyRegistry()
        assert registry.size == 0
        registry.register("key", lambda: "value")
        assert registry.size == 1

    def test_initialized_count_property(self) -> None:
        """initialized_count should return number of initialized values."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("a", lambda: "A")
        registry.register("b", lambda: "B")
        assert registry.initialized_count == 0
        registry.get("a")
        assert registry.initialized_count == 1

    def test_contains_operator(self) -> None:
        """Test 'in' operator."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("key", lambda: "value")
        assert "key" in registry
        assert "missing" not in registry

    def test_len_operator(self) -> None:
        """Test len() function."""
        registry: LazyRegistry[str] = LazyRegistry()
        assert len(registry) == 0
        registry.register("key", lambda: "value")
        assert len(registry) == 1

    def test_repr(self) -> None:
        """Repr should show counts."""
        registry: LazyRegistry[str] = LazyRegistry()
        registry.register("key", lambda: "value")
        assert "registered=1" in repr(registry)
        assert "initialized=0" in repr(registry)


class TestInstallLazyModule:
    """Tests for install_lazy_module function."""

    def test_installs_in_sys_modules(self) -> None:
        """Should install LazyModule in sys.modules."""
        # Use a fake module name that doesn't exist
        fake_name = "_test_lazy_module_12345"

        # Make sure it's not already there
        if fake_name in sys.modules:
            del sys.modules[fake_name]

        install_lazy_module(fake_name)

        assert fake_name in sys.modules
        assert isinstance(sys.modules[fake_name], LazyModule)

        # Cleanup
        del sys.modules[fake_name]

    def test_does_not_override_existing(self) -> None:
        """Should not override already loaded modules."""
        # json is already loaded
        original = sys.modules.get("json")
        install_lazy_module("json")
        assert sys.modules["json"] is original
