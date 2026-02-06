"""Tests for MCP manager."""

from pathlib import Path

from aios.infrastructure.mcp import ESSENTIAL_CATALOG
from aios.infrastructure.mcp import MCPManager
from aios.infrastructure.models import MCPConfig
from aios.infrastructure.models import MCPServer


class TestMCPManager:
    def test_load_config_no_file(self, tmp_path: Path) -> None:
        manager = MCPManager(config_path=tmp_path / ".mcp.json")
        config = manager.load_config()
        assert isinstance(config, MCPConfig)
        assert len(config.mcp_servers) == 0

    def test_save_and_load_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / ".mcp.json"
        manager = MCPManager(config_path=config_path)

        config = MCPConfig()
        config.mcp_servers["test"] = MCPServer(command="npx", args=["-y", "test"])
        manager.save_config(config)

        loaded = manager.load_config()
        assert "test" in loaded.mcp_servers
        assert loaded.mcp_servers["test"].command == "npx"

    def test_install_from_catalog(self, tmp_path: Path) -> None:
        manager = MCPManager(config_path=tmp_path / ".mcp.json")
        result = manager.install("context7")
        assert result is True
        assert manager.is_installed("context7")

    def test_install_unknown(self, tmp_path: Path) -> None:
        manager = MCPManager(config_path=tmp_path / ".mcp.json")
        result = manager.install("nonexistent")
        assert result is False

    def test_install_all_essential(self, tmp_path: Path) -> None:
        manager = MCPManager(config_path=tmp_path / ".mcp.json")
        installed = manager.install_all_essential()
        assert len(installed) == len(ESSENTIAL_CATALOG)

    def test_list_catalog(self) -> None:
        manager = MCPManager()
        catalog = manager.list_catalog()
        assert len(catalog) == 3
        names = [e.name for e in catalog]
        assert "context7" in names

    def test_get_missing_essential(self, tmp_path: Path) -> None:
        manager = MCPManager(config_path=tmp_path / ".mcp.json")
        missing = manager.get_missing_essential()
        assert len(missing) == 3
        manager.install("context7")
        missing = manager.get_missing_essential()
        assert len(missing) == 2


class TestMCPConfig:
    def test_alias_serialization(self) -> None:
        config = MCPConfig()
        config.mcp_servers["test"] = MCPServer(command="npx", args=[])
        data = config.model_dump(by_alias=True)
        assert "mcpServers" in data
