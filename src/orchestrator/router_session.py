"""Composio Tool Router session utilities."""
from __future__ import annotations

import os
from typing import Dict, List

from rich.console import Console

console = Console()

# We import composio lazily inside functions so importing this module won't
# fail when the installed composio package has incompatible internals.
# This allows the rest of the app to import modules that don't use the
# tool-router without requiring the composio package at import-time.

_META_TOOL_IDS: List[str] = [
    "COMPOSIO_SEARCH_TOOLS",
    "COMPOSIO_CREATE_PLAN",
    "COMPOSIO_MANAGE_CONNECTIONS",
    "COMPOSIO_MULTI_EXECUTE_TOOL",
    "COMPOSIO_REMOTE_WORKBENCH",
    "COMPOSIO_REMOTE_BASH_TOOL",
]



# Some versions of the composio SDK expose an `App` enum. To avoid import
# time failures, we provide a small fallback and attempt to resolve the real
# enum at runtime when needed.
class _FallbackApp:
    GOOGLE_SHEETS = "GOOGLE_SHEETS"
    GMAIL = "GMAIL"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    YAHOO_FINANCE = "YAHOO_FINANCE"
    FILETOOL = "FILETOOL"


def _get_app_enum():
    try:
        from composio.client.collections import App as AppEnum  # type: ignore
        return AppEnum
    except Exception:
        return _FallbackApp


_FINANCE_APPS: List[object] = [
    _get_app_enum().GOOGLE_SHEETS,
    _get_app_enum().GMAIL,
    _get_app_enum().GOOGLE_DRIVE,
    _get_app_enum().YAHOO_FINANCE,
    _get_app_enum().FILETOOL,
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
    try:
        from composio import Composio  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime environment may vary
        raise RuntimeError(
            "The 'composio' package is required to create a Tool Router session. "
            "Install the package in your environment or disable tool-router features."
        ) from exc

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



def get_finance_apps() -> List[object]:
    """Return the default finance app set for the workflow."""
    return list(_FINANCE_APPS)
