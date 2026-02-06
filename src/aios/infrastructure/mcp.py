"""MCP management logic."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from aios.infrastructure.models import MCPCatalogEntry
from aios.infrastructure.models import MCPConfig
from aios.infrastructure.models import MCPServer

# Essential MCP catalog
ESSENTIAL_CATALOG: list[MCPCatalogEntry] = [
    MCPCatalogEntry(
        name="context7",
        description="Up-to-date documentation for any library via Context7",
        command="npx",
        args=["-y", "@upstash/context7-mcp"],
        required=True,
    ),
    MCPCatalogEntry(
        name="desktop-commander",
        description="Desktop automation and file management",
        command="npx",
        args=["-y", "@wonderwhy-er/desktop-commander"],
        required=True,
    ),
    MCPCatalogEntry(
        name="browser",
        description="Browser automation via Puppeteer",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-puppeteer"],
        required=True,
    ),
]


class MCPManager:
    """Manages MCP server installations and configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or Path(".mcp.json")
        self._catalog = {entry.name: entry for entry in ESSENTIAL_CATALOG}

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load_config(self) -> MCPConfig:
        """Load current MCP configuration."""
        if not self._config_path.exists():
            return MCPConfig()
        try:
            data = json.loads(self._config_path.read_text())
            return MCPConfig.model_validate(data)
        except (json.JSONDecodeError, OSError):
            return MCPConfig()

    def save_config(self, config: MCPConfig) -> None:
        """Save MCP configuration to .mcp.json."""
        data = config.model_dump(by_alias=True)
        self._config_path.write_text(json.dumps(data, indent=2) + "\n")

    def list_installed(self) -> dict[str, MCPServer]:
        """List installed MCP servers."""
        config = self.load_config()
        return dict(config.mcp_servers)

    def list_catalog(self) -> list[MCPCatalogEntry]:
        """List all available MCPs in catalog."""
        return list(self._catalog.values())

    def is_installed(self, name: str) -> bool:
        """Check if an MCP is installed."""
        config = self.load_config()
        return name in config.mcp_servers

    def install(self, name: str) -> bool:
        """Install an MCP from catalog."""
        if name not in self._catalog:
            return False

        entry = self._catalog[name]
        config = self.load_config()

        server = MCPServer(
            command=entry.command,
            args=list(entry.args),
        )
        config.mcp_servers[name] = server
        self.save_config(config)
        return True

    def install_all_essential(self) -> list[str]:
        """Install all essential MCPs. Returns list of newly installed."""
        installed: list[str] = []
        for entry in ESSENTIAL_CATALOG:
            if not self.is_installed(entry.name):
                self.install(entry.name)
                installed.append(entry.name)
        return installed

    def has_npx(self) -> bool:
        """Check if npx is available."""
        return shutil.which("npx") is not None

    def get_missing_essential(self) -> list[str]:
        """Get list of essential MCPs not yet installed."""
        config = self.load_config()
        return [
            entry.name
            for entry in ESSENTIAL_CATALOG
            if entry.name not in config.mcp_servers
        ]
