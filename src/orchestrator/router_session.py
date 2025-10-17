"""Composio Tool Router session utilities."""
from __future__ import annotations

import os
from typing import Dict, List

from rich.console import Console

try:
    from composio import Composio
    from composio.client.collections import App
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Install 'composio' package to use tool router utilities.") from exc

console = Console()

_META_TOOL_IDS: List[str] = [
    "COMPOSIO_SEARCH_TOOLS",
    "COMPOSIO_CREATE_PLAN",
    "COMPOSIO_MANAGE_CONNECTIONS",
    "COMPOSIO_MULTI_EXECUTE_TOOL",
    "COMPOSIO_REMOTE_WORKBENCH",
    "COMPOSIO_REMOTE_BASH_TOOL",
]

_FINANCE_APPS: List[App] = [
    App.GOOGLE_SHEETS,
    App.GMAIL,
    App.GOOGLE_DRIVE,
    App.YAHOO_FINANCE,
    App.FILETOOL,
]


def _resolve_user_id(user_id: str | None) -> str:
    if user_id:
        return user_id
    env_user = os.getenv("TOOL_ROUTER_USER_ID")
    if env_user:
        return env_user
    return "hackathon-demo-user"


def create_tool_router_session(user_id: str | None = None) -> Dict[str, object]:
    """Create a Tool Router session and log the MCP server URL."""
    resolved_user_id = _resolve_user_id(user_id)
    client = Composio()
    console.log(f"Creating Tool Router session for user '{resolved_user_id}'")
    session = client.experimental.tool_router.create_session(user_id=resolved_user_id)

    mcp_url = session.get("mcp_server_url") or session.get("url") or ""
    if mcp_url:
        console.log(f"Tool Router MCP URL: {mcp_url}")
    else:
        console.log("Tool Router session created but MCP URL was not returned; verify SDK version.")

    return {
        "user_id": resolved_user_id,
        "session": session,
        "mcp_server_url": mcp_url,
        "client": client,
    }


def get_meta_tool_identifiers() -> List[str]:
    """Return the default list of Tool Router meta-tool identifiers."""
    return list(_META_TOOL_IDS)


def get_finance_apps() -> List[App]:
    """Return the default finance app set for the workflow."""
    return list(_FINANCE_APPS)
