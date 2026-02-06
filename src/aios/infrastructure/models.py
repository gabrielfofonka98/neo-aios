"""MCP infrastructure models."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class MCPServer(BaseModel):
    """MCP server configuration entry."""

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class MCPCatalogEntry(BaseModel):
    """Entry in the MCP catalog."""

    name: str
    description: str
    command: str
    args: list[str]
    required: bool = False


class MCPConfig(BaseModel):
    """Root MCP configuration (.mcp.json)."""

    mcp_servers: dict[str, MCPServer] = Field(
        default_factory=dict,
        alias="mcpServers",
    )

    model_config = {"populate_by_name": True}
