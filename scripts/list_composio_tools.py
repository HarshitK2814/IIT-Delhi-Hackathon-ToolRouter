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
try:
    from composio_client import Composio as ComposioV3
except ImportError:
    ComposioV3 = None  # type: ignore

_ATTEMPTS = (
    ('list', {'toolkits': None}),
    ('get', {'user_id': 'system', 'toolkits': None}),
)

def _extract_v3_items(payload):
    if payload is None:
        return []
    items = getattr(payload, "items", None)
    if items is not None:
        return items
    data = getattr(payload, "data", None)
    if data is not None:
        return data
    if isinstance(payload, dict):
        return payload.get("items") or payload.get("data") or payload
    return []

def _try_fetch_tools(client, toolkit: str, v3_client=None):
    if client is None:
        raise RuntimeError('client unavailable')
    tools_api = getattr(client, 'tools', None)
    if tools_api is not None:
        for name, kwargs in _ATTEMPTS:
            method = getattr(tools_api, name, None)
            if not callable(method):
                continue
            params = dict(kwargs)
            if params.get('toolkits') is None:
                params['toolkits'] = [toolkit]
            try:
                result = method(**params)
                if result:
                    return result
            except TypeError:
                continue
            except Exception as exc:
                raise RuntimeError(f"{client.__class__.__name__}.tools.{name} failed: {exc}") from exc
    if v3_client is not None:
        try:
            response = v3_client.tools.list(toolkit_slug=toolkit)
            items = _extract_v3_items(response)
            normalized = []
            for item in items or []:
                if hasattr(item, "model_dump"):
                    normalized.append(item.model_dump())
                elif hasattr(item, "dict"):
                    normalized.append(item.dict())
                elif isinstance(item, dict):
                    normalized.append(item)
                else:
                    normalized.append({"raw": item})
            if normalized:
                return normalized
        except Exception:
            pass
    http_client = getattr(client, 'http', None) or getattr(client, '_http_client', None)
    endpoints = getattr(client, 'endpoints', None)
    if http_client is not None and endpoints is not None:
        v3 = getattr(endpoints, 'v3', None)
        tools_url = getattr(v3, 'tools', None) if v3 is not None else None
        if tools_url is not None:
            resp = http_client.get(str(tools_url), params={'toolkit_slug': toolkit})
            data = resp.json()
            return data.get('items') or data.get('data') or data
    return []

def list_tools(toolkits=('googlesheets','googledocs','gmail','slack','serpapi','alpha_vantage')):
    api_key = os.getenv('COMPOSIO_API_KEY')
    if not api_key:
        print('COMPOSIO_API_KEY not set in environment or .env')
        return
    primary_client = Composio(api_key=api_key)
    v3_client = None
    if ComposioV3 is not None:
        try:
            v3_client = ComposioV3(api_key=api_key)
        except Exception:
            v3_client = None
    for tk in toolkits:
        print(f"\n--- Toolkit: {tk} ---")
        tools = None
        last_error = None
        for client in (v3_client, primary_client):
            if client is None:
                continue
            try:
                candidate = _try_fetch_tools(client, tk, v3_client=v3_client)
                if candidate:
                    tools = candidate
                    break
                if tools is None:
                    tools = candidate
            except Exception as exc:
                last_error = exc
                continue
        if tools is None:
            print('Failed to fetch toolkit', tk, 'error:', last_error or 'tools API unavailable')
            continue

        # Print each tool's metadata (handle dicts or objects)
        for t in tools:
            print('TOOL:')
            data = None
            if isinstance(t, dict):
                data = t
            elif hasattr(t, "model_dump"):
                data = t.model_dump()
            elif hasattr(t, "dict"):
                data = t.dict()
            if data is not None:
                for k in ('id', 'slug', 'tool_slug', 'name'):
                    if data.get(k) is not None:
                        print(f'  {k}: {data[k]}')
                toolkit_info = data.get('toolkit')
                if isinstance(toolkit_info, dict):
                    print('  toolkit.slug:', toolkit_info.get('slug'))
                print('  keys:', list(data.keys()))
            else:
                for k in ('id', 'slug', 'tool_slug', 'name'):
                    v = getattr(t, k, None)
                    if v is not None:
                        print(f'  {k}: {v}')

if __name__ == '__main__':
    list_tools()
