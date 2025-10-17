import os
import sys
import json
import argparse
import requests
import traceback
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from composio import Composio
from composio.client import Client

# MCP Configuration
MCP_CONFIG_ID = "8eff889d-9e91-42fb-8f7f-457f6ad2d240"
DEFAULT_USER_ID = "pg-test-adbe256b-58ee-4dd4-b83d-b550435832dd"
AUTH_URL = "https://backend.composio.dev/api/v3/auth_configs"
MCP_BASE_URL = f"https://backend.composio.dev/v3/mcp/{MCP_CONFIG_ID}/mcp"

load_dotenv()


def register_service_account(api_key, json_path):
    """Register Google Sheets service account with Composio."""
    with open(json_path, "r") as f:
        service_account_data = json.load(f)
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "toolkit": {"slug": "GOOGLESHEETS"},
        "auth_config": {
            "type": "use_custom_auth",
            "authScheme": "GOOGLE_SERVICE_ACCOUNT",
            "credentials": {
                "service_account_info": service_account_data,
            },
            "name": "My Google Sheets Service Account",
        },
    }
    response = requests.post(AUTH_URL, headers=headers, json=payload)
    try:
        respj = response.json()
    except Exception:
        respj = {"text": response.text}
    print("\n== Auth Config Registration Result ==")
    print(json.dumps(respj, indent=2))
    return respj


def create_tool_router_session(user_id):
    """Create a Tool Router session and return session_id and MCP URL."""
    composio = Composio()
    print(f"[INFO] Creating Tool Router session for user: {user_id} ...")
    try:
        session_info = composio.experimental.tool_router.create_session(user_id=user_id)
        session_id = session_info.get("session", {}).get("id") or session_info.get("session_id")

        if not session_id:
            raise RuntimeError("Session ID missing from Tool Router response.")

        # Construct the full MCP endpoint URL
        mcp_endpoint_url = f"{MCP_BASE_URL}?user_id={session_id}"

        print("\n" + "=" * 60)
        print("✅ Tool Router Session Created Successfully")
        print("=" * 60)
        print(f"Session ID: {session_id}")
        print(f"MCP Endpoint URL: {mcp_endpoint_url}")
        print(f"MCP Config ID: {MCP_CONFIG_ID}")
        print("=" * 60 + "\n")

        print("📋 Save these credentials for your agent integration:")
        print(f"   export MCP_ENDPOINT_URL='{mcp_endpoint_url}'")
        print(f"   export MCP_CONFIG_ID='{MCP_CONFIG_ID}'")
        print(f"   export SESSION_ID='{session_id}'")
        print()

        return session_id, mcp_endpoint_url
    except Exception as exc:
        print("❌ Error creating Tool Router session:", str(exc))
        traceback.print_exc()
        sys.exit(1)


def _execute_action(client: Client, action: str, params: dict, errors: list[str] | None = None):
    errors = errors or []
    actions_api = getattr(client, "actions", None)
    if actions_api is not None:
        for name in ("execute_action", "execute", "run", "__call__"):
            fn = getattr(actions_api, name, None)
            if not callable(fn):
                continue
            try:
                return fn(action=action, params=params)
            except TypeError:
                pass
            except Exception as exc:
                errors.append(f"actions.{name}(action=..., params=...): {exc}")
    for name in ("execute_action", "execute", "run", "__call__"):
        fn = getattr(client, name, None)
        if not callable(fn):
            continue
        try:
            return fn(action, params)
        except TypeError:
            pass
        except Exception as exc:
            errors.append(f"client.{name}(<action>, <params>): {exc}")
    http_client = getattr(client, "http", None) or getattr(client, "_http_client", None)
    if http_client is not None:
        envelope = {"action": action, "params": params}
        try:
            return http_client.post("/v3/actions", body=envelope, cast_to=dict)
        except Exception as exc:
            errors.append(f"HTTP POST /v3/actions failed: {exc}")
    return {"error": "Unable to execute action via composio client", "details": errors}


def run_append_row(session_id: str):
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError("COMPOSIO_API_KEY is not configured")
    if "COMPOSIO_API_KEY" not in os.environ:
        os.environ.setdefault("COMPOSIO_API_KEY", api_key)
    client = Client()

    params = {
        "connected_account_id": "ca_6-Yb6PMnhQAL",
        "spreadsheet_id": "1rIzF6y4O29yc6INIxpbi5Ny1GJKyAldd5sSg5RCldNg",
        "sheet_name": "Try Out",
        "values": [["GOOGL", "Research summary for GOOGL"]],
        "entity_id": session_id,
        "session_id": session_id,
    }
    errors: list[str] = []
    result = _execute_action(client, "GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND", params, errors)
    if isinstance(result, dict) and result.get("error"):
        print("[WARN] Action execution errors:", errors)
    print("Result:", result)
    return result


def list_v3_tools(api_key, toolkit="GOOGLESHEETS"):
    """List available tools for a toolkit."""
    print("[INFO] Listing tools for toolkit:", toolkit)
    try:
        client = Client(api_key=api_key)
        params = {"toolkits": toolkit}
        tools_api = getattr(client, "tools", None)
        if tools_api:
            for name in ("get", "list"):
                fn = getattr(tools_api, name, None)
                if callable(fn):
                    try:
                        result = fn(**params)
                        print(json.dumps(result, indent=2))
                        return result
                    except Exception:
                        continue
    except Exception as exc:
        print("Error listing tools:", exc)
        traceback.print_exc()
    return {}


def test_direct_mcp_post(mcp_endpoint_url, api_key, connected_account_id, spreadsheet_id, ticker="GOOGL"):
    """
    Direct POST test to MCP endpoint using JSON-RPC 2.0 format.
    """
    print("\n[INFO] Testing direct POST to MCP endpoint...")
    print(f"Endpoint: {mcp_endpoint_url}")

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND",
            "arguments": {
                "connected_account_id": connected_account_id,
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": "Sheet1",
                "values": [[ticker, f"Research summary for {ticker}"]],
            },
        },
        "id": 1,
    }

    print("Payload:", json.dumps(payload, indent=2))

    try:
        response = requests.post(mcp_endpoint_url, json=payload, headers=headers)
        print(f"\n[RESPONSE] Status Code: {response.status_code}")

        try:
            result = response.json()
            print(json.dumps(result, indent=2))

            if "result" in result:
                print("\n✅ Tool execution successful!")
                return result["result"]
            elif "error" in result:
                print(f"\n❌ JSON-RPC Error: {result['error']}")
                return result
            return result
        except Exception:
            print(f"Response text: {response.text}")
            return {"status_code": response.status_code, "text": response.text}

    except Exception as exc:
        print(f"[ERROR] MCP POST failed: {exc}")
        traceback.print_exc()
        return {"error": str(exc)}


def save_config_to_env(session_id, mcp_endpoint_url):
    """Save MCP configuration to .env file."""
    env_file = Path(".env")
    timestamp = datetime.now().isoformat()
    config_lines = [
        f"\n# Composio MCP Configuration (Generated {timestamp})\n",
        f"MCP_ENDPOINT_URL={mcp_endpoint_url}\n",
        f"MCP_CONFIG_ID={MCP_CONFIG_ID}\n",
        f"SESSION_ID={session_id}\n",
    ]

    try:
        with open(env_file, "a") as f:
            f.writelines(config_lines)
        print(f"✅ Configuration saved to {env_file}")
    except Exception as exc:
        print(f"⚠️ Could not save to .env: {exc}")


def main():
    parser = argparse.ArgumentParser(
        description="Composio Tool Router Session Setup & MCP Integration Test"
    )
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help="Composio user/session ID")
    parser.add_argument("--account-id", default=None, help="Connected account ID for Sheets")
    parser.add_argument("--service-account-json", default=None, help="Path to service_account.json")
    parser.add_argument("--register-auth-only", action="store_true", help="Only register auth and exit")
    parser.add_argument("--list-tools", action="store_true", help="List Google Sheets tools")
    parser.add_argument("--test-mcp", action="store_true", help="Test direct POST to MCP endpoint")
    parser.add_argument("--spreadsheet-id", help="Google Sheets ID for test")
    parser.add_argument("--ticker", default="GOOGL", help="Stock ticker for test data")
    parser.add_argument("--save-config", action="store_true", help="Save MCP config to .env file")

    args = parser.parse_args()

    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        print("❌ COMPOSIO_API_KEY is not set in environment or .env")
        sys.exit(1)

    if args.service_account_json:
        register_service_account(api_key, args.service_account_json)
        if args.register_auth_only:
            print("[INFO] Auth registration complete. Exiting.")
            return

    if args.list_tools:
        list_v3_tools(api_key)
        print("[INFO] Tool listing complete. Exiting.")
        return

    session_id, mcp_endpoint_url = create_tool_router_session(args.user_id)

    if args.save_config:
        save_config_to_env(session_id, mcp_endpoint_url)

    if args.test_mcp:
        sdk_result = run_append_row(session_id)
        print("SDK result:", sdk_result)

        if not args.account_id:
            print("❌ --account-id required for MCP test")
            sys.exit(1)
        if not args.spreadsheet_id:
            print("❌ --spreadsheet-id required for MCP test")
            sys.exit(1)

        rpc_result = test_direct_mcp_post(
            mcp_endpoint_url,
            api_key,
            args.account_id,
            args.spreadsheet_id,
            args.ticker,
        )
        if rpc_result.get("error"):
            print("\n❌ MCP test (direct JSON-RPC) failed; this endpoint expects an MCP client.")
        else:
            print("\n✅ MCP JSON-RPC test completed. Check result above.")
    else:
        print("\n" + "=" * 60)
        print("🎯 NEXT STEPS")
        print("=" * 60)
        print("1. Use the MCP endpoint URL in your agent framework:")
        print(f"   {mcp_endpoint_url}")
        print("\n2. Configure OpenAI/Claude/CrewAI to route tool calls through this URL")
        print("\n3. Test with: --test-mcp --account-id <ID> --spreadsheet-id <ID>")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()