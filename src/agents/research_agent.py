"""Research agent leveraging Composio Tool Router and Gemini."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from composio import Composio

from ..llm.gemini_client import GeminiLLM
from ..orchestrator.router_session import get_finance_apps, get_meta_tool_identifiers


@dataclass
class ResearchAgent:
    """Handles discovery and planning phases for the workflow."""

    llm: GeminiLLM
    composio: Composio
    meta_tools: List[str] = field(default_factory=get_meta_tool_identifiers)
    # The installed Composio package may expose an App enum or simple strings.
    # Use a generic object type here and normalize when needed to avoid import-time
    # failures across different SDK versions.
    finance_apps: List[object] = field(default_factory=get_finance_apps)

    def __post_init__(self) -> None:
        # Some Composio client versions expose helpers like `add_tool`/`add_app`.
        # Call them only when available to remain compatible with multiple SDKs.
        add_tool_fn = getattr(self.composio, "add_tool", None)
        add_app_fn = getattr(self.composio, "add_app", None)
        for tool_id in self.meta_tools:
            if callable(add_tool_fn):
                try:
                    add_tool_fn(tool_id)
                except Exception:
                    # best-effort: don't let bootstrap failures break the agent
                    pass
        for app in self.finance_apps:
            if callable(add_app_fn):
                try:
                    add_app_fn(app)
                except Exception:
                    pass

    def capability_report(self) -> Dict[str, List[str]]:
        return {
            "model": [self.llm.model],
            "meta_tools": list(self.meta_tools),
            # Apps may be enum values or strings depending on SDK version; coerce to str
            "finance_apps": [str(app) for app in self.finance_apps],
        }

    def draft_research_plan(self, ticker: str) -> str:
        prompt = (
            "You are a hedge fund research analyst working with Composio Tool Router meta-tools. "
            f"Outline a discovery, authentication, and execution plan for ticker {ticker}."
        )
        return self.llm.generate(prompt)
"""Research agent leveraging Composio Tool Router and Gemini."""
