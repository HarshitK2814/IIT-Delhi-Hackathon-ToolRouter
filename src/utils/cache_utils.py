"""Very small JSON file cache with TTL for simple metadata caching."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Optional


def _safe_makedirs(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def load_cache(path: str, key: str, max_age_seconds: Optional[int] = None) -> Optional[Any]:
    """Load a key from a JSON cache file if not expired.

    Returns None when cache is missing or expired.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return None

    entry = payload.get(key)
    if not entry:
        return None

    ts = entry.get("ts")
    if ts is None:
        return None

    if max_age_seconds is not None and (time.time() - ts) > max_age_seconds:
        return None

    return entry.get("value")


def save_cache(path: str, key: str, value: Any) -> None:
    """Save a key into a JSON cache file with current timestamp."""
    _safe_makedirs(path)
    payload = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            payload = {}

    payload[key] = {"ts": time.time(), "value": value}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
