"""List tools from selected Composio toolkits using COMPOSIO_API_KEY from .env.

Usage:
  python scripts/list_composio_tools.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure repo root on path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

load_dotenv()
from composio import Composio
from composio.tools.toolset import ComposioToolSet

def list_tools(toolkits=('googlesheets','yahoo_finance','googledocs','google_search')):
    api_key = os.getenv('COMPOSIO_API_KEY')
    if not api_key:
        print('COMPOSIO_API_KEY not set in environment or .env')
        return
    client = Composio(api_key=api_key)
    for tk in toolkits:
        print(f"\n--- Toolkit: {tk} ---")
        # First try high-level SDK surface
        try:
            tools_api = getattr(client, 'tools', None)
            if tools_api is not None:
                tools = tools_api.get(user_id='system', toolkits=[tk])
            else:
                raise AttributeError('client.tools missing')
        except Exception as exc:
            # Fallback: use the low-level HTTP endpoints via ComposioToolSet
            try:
                print('High-level client.tools failed, trying low-level HTTP via ComposioToolSet')
                toolset = ComposioToolSet(api_key=api_key)
                low_client = toolset.client
                tools_url = str(low_client.endpoints.v1.tools)
                # attempt to GET tools for the toolkit
                resp = low_client.http.get(tools_url, params={'toolkits': tk})
                data = resp.json()
                tools = data.get('data') or data.get('items') or data
            except Exception as exc2:
                print('Failed to fetch toolkit', tk, 'error:', exc2)
                continue

        # Print each tool's metadata (handle dicts or objects)
        for t in tools:
            print('TOOL:')
            if isinstance(t, dict):
                for k in ('id', 'slug', 'tool_slug', 'name'):
                    if k in t:
                        print(f'  {k}: {t[k]}')
                # print top-level keys
                print('  keys:', list(t.keys()))
            else:
                for k in ('id', 'slug', 'tool_slug', 'name'):
                    v = getattr(t, k, None)
                    if v is not None:
                        print(f'  {k}: {v}')
                try:
                    d = dict(t)
                    print('  keys:', list(d.keys()))
                except Exception:
                    pass

if __name__ == '__main__':
    list_tools()
