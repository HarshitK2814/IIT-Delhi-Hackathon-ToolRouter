"""Helper to load .env into os.environ then run the project's CLI module.

Usage:
    python scripts/run_with_env.py --ticker GOOGL

This keeps the Powershell invocation simple and avoids here-doc quoting.
"""
import os
import sys
from pathlib import Path
import runpy
import sys
from pathlib import Path

def load_dotenv(path: str = ".env"):
    p = Path(path)
    if not p.exists():
        print(f".env not found at {path}")
        return
    print(f"Loading .env from {path}")
    for ln in p.read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        if '=' not in ln:
            continue
        k, v = ln.split('=', 1)
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v)

if __name__ == '__main__':
    load_dotenv()
    # Print whether COMPOSIO_API_KEY is present
    print('COMPOSIO_API_KEY present:', 'COMPOSIO_API_KEY' in os.environ)
    # Ensure the project root is on sys.path so `src` is importable when run as a module
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    # Delegate to the module CLI
    runpy.run_module('src.main', run_name='__main__')
