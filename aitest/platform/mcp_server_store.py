"""MCP Server Store — backward compatibility re-export.

MCPServerStore has been moved to aitest.mcp.database to eliminate circular dependencies.
This file re-exports it for backward compatibility.

Moved: 2026-07-14 (Step 1.1b - circular dependency refactoring)
"""

from aitest.mcp.database import MCPServerStore, register_env_resolvers
from aitest.mcp.types import AgentMCPMapping, MCPServer

__all__ = ["AgentMCPMapping", "MCPServer", "MCPServerStore"]


def _resolve_secret(session, secret_id: str) -> str:
    from aitest.platform.secret_store import SecretStore

    secret = SecretStore(session).get_secret(secret_id)
    return secret.value if secret else ""


def _resolve_environment(session, var_name: str) -> str:
    import os

    from aitest.platform.environment_store import EnvironmentStore

    env_id = os.getenv("AITEST_ENVIRONMENT", "dev")
    store = EnvironmentStore(session)
    if not store.get_environment(env_id):
        return ""
    return store.resolve_variables(env_id).get(var_name, "")


# The platform compatibility facade is the composition root for optional
# secret/environment services; the MCP database layer stays platform-neutral.
register_env_resolvers(_resolve_secret, _resolve_environment)
