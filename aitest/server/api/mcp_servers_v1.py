"""MCP Server resource API — persistence and lifecycle controls."""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from aitest.platform.mcp_server_manager import get_mcp_server_manager
from aitest.platform.mcp_server_store import MCPServer, MCPServerStore

mcp_servers_router = APIRouter(prefix="/api/v1/mcp-servers", tags=["mcp-servers"])


class CreateMCPServerRequest(BaseModel):
    mcp_server_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    transport_type: Literal["stdio", "http"]
    command: str = ""
    args: list[str] = Field(default_factory=list)
    url: str = ""
    env: dict[str, str] = Field(default_factory=dict)
    description: str = ""
    enabled_by_default: bool = False
    org_id: str = "default-org"
    created_by: str = "admin"

    @model_validator(mode="after")
    def validate_transport(self):
        if self.transport_type == "stdio" and not self.command:
            raise ValueError("command is required for stdio MCP servers")
        if self.transport_type == "http" and not self.url:
            raise ValueError("url is required for http MCP servers")
        return self


class UpdateMCPServerRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    env: Optional[dict[str, str]] = None
    enabled_by_default: Optional[bool] = None


def _serialize(server: MCPServer) -> dict:
    """Return operator-safe configuration without exposing environment values."""
    return {
        "mcp_server_id": server.mcp_server_id,
        "name": server.name,
        "description": server.description,
        "transport_type": server.transport_type,
        "command": server.command,
        "args": server.args,
        "url": server.url,
        "env_keys": sorted(server.env),
        "tools": server.tools,
        "status": server.status,
        "process_id": server.process_id,
        "enabled_by_default": server.enabled_by_default,
        "org_id": server.org_id,
        "created_by": server.created_by,
        "created_at": server.created_at,
        "updated_at": server.updated_at,
        "last_health_check": server.last_health_check,
    }


def _store() -> MCPServerStore:
    return MCPServerStore()


@mcp_servers_router.post("")
async def create_mcp_server(req: CreateMCPServerRequest):
    store = _store()
    if store.get_mcp_server(req.mcp_server_id):
        raise HTTPException(409, f"MCP server already exists: {req.mcp_server_id}")
    server = store.create_mcp_server(**req.model_dump())
    return _serialize(server)


@mcp_servers_router.get("")
async def list_mcp_servers(org_id: str = "", status: str = ""):
    servers = _store().list_mcp_servers(org_id=org_id or None, status=status or None)
    return {"servers": [_serialize(server) for server in servers], "total": len(servers)}


@mcp_servers_router.get("/{mcp_server_id}")
async def get_mcp_server(mcp_server_id: str):
    server = _store().get_mcp_server(mcp_server_id)
    if server is None:
        raise HTTPException(404, "MCP server not found")
    return _serialize(server)


@mcp_servers_router.put("/{mcp_server_id}")
async def update_mcp_server(mcp_server_id: str, req: UpdateMCPServerRequest):
    server = _store().update_mcp_server(mcp_server_id, **req.model_dump(exclude_none=True))
    if server is None:
        raise HTTPException(404, "MCP server not found")
    return _serialize(server)


@mcp_servers_router.delete("/{mcp_server_id}")
async def delete_mcp_server(mcp_server_id: str):
    store = _store()
    server = store.get_mcp_server(mcp_server_id)
    if server is None:
        raise HTTPException(404, "MCP server not found")
    if server.status in {"running", "starting"}:
        raise HTTPException(409, "Stop the MCP server before deleting it")
    store.delete_mcp_server(mcp_server_id)
    return {"deleted": True, "mcp_server_id": mcp_server_id}


@mcp_servers_router.post("/{mcp_server_id}/start")
async def start_mcp_server(mcp_server_id: str):
    manager = get_mcp_server_manager()
    if manager.store.get_mcp_server(mcp_server_id) is None:
        raise HTTPException(404, "MCP server not found")
    return {"mcp_server_id": mcp_server_id, "started": await manager.start_server(mcp_server_id)}


@mcp_servers_router.post("/{mcp_server_id}/stop")
async def stop_mcp_server(mcp_server_id: str):
    manager = get_mcp_server_manager()
    if manager.store.get_mcp_server(mcp_server_id) is None:
        raise HTTPException(404, "MCP server not found")
    return {"mcp_server_id": mcp_server_id, "stopped": await manager.stop_server(mcp_server_id)}


@mcp_servers_router.get("/{mcp_server_id}/status")
async def get_mcp_server_status(mcp_server_id: str):
    status = await get_mcp_server_manager().get_status(mcp_server_id)
    if "error" in status:
        raise HTTPException(404, status["error"])
    return status
