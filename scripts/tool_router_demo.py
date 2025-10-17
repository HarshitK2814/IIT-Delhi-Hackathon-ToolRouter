"""Print discovered tools from Composio Tool Router."""
import os
from dotenv import load_dotenv

from composio import Composio
from src.utils.logging_utils import configure_logging

load_dotenv()
configure_logging()

client = Composio()
session = client.experimental.tool_router.create_session(
    user_id=os.getenv("TOOL_ROUTER_USER_ID", "demo-user")
)

print(f"Tool Router MCP URL: {session.get('mcp_server_url')}")
print("\nAvailable meta-tools:")
for tool in client.experimental.tool_router.list_meta_tools():
    print(f"- {tool['id']}: {tool['description']}")

print("\nAvailable finance apps:")
for app in ["YAHOO_FINANCE", "GOOGLE_SHEETS", "GMAIL"]:
    print(f"- {app}")