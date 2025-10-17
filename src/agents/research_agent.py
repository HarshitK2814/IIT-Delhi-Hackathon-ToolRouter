"""Research agent leveraging Composio Tool Router and Gemini."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from composio.client.collections import App
from composio import Composio

from ..llm.gemini_client import GeminiLLM
from ..orchestrator.router_session import get_finance_apps, get_meta_tool_identifiers


@dataclass
class ResearchAgent:
    """Handles discovery and planning phases for the workflow."""

    llm: GeminiLLM
    composio: Composio
    meta_tools: List[str] = field(default_factory=get_meta_tool_identifiers)
    finance_apps: List[App] = field(default_factory=get_finance_apps)

    def __post_init__(self) -> None:
        for tool_id in self.meta_tools:
            self.composio.add_tool(tool_id)
        for app in self.finance_apps:
            self.composio.add_app(app)

    def capability_report(self) -> Dict[str, List[str]]:
        return {
            "model": [self.llm.model],
            "meta_tools": list(self.meta_tools),
            "finance_apps": [app.value for app in self.finance_apps],
        }

    def draft_research_plan(self, ticker: str) -> str:
        prompt = (
            "You are a hedge fund research analyst working with Composio Tool Router meta-tools. "
            f"Outline a discovery, authentication, and execution plan for ticker {ticker}."
        )
        return self.llm.generate(prompt)
"""Research agent leveraging Composio Tool Router and Gemini."""
