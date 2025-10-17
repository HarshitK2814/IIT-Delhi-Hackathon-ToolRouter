"""Workflow agent coordinating execution via Composio Tool Router."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from composio import Composio

from ..llm.gemini_client import GeminiLLM
from ..orchestrator.router_session import get_finance_apps, get_meta_tool_identifiers
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowAgent:
    """Agent responsible for orchestrating cross-app execution steps."""

    llm: GeminiLLM
    composio: Composio
    meta_tools: List[str] = field(default_factory=get_meta_tool_identifiers)
    # See note in research_agent: some SDKs expose enums, others simple strings.
    target_apps: List[object] = field(default_factory=get_finance_apps)

    def __post_init__(self) -> None:
        self._bootstrap_tools()

    def _bootstrap_tools(self) -> None:
        """Load required meta-tools and domain apps."""
        add_tool_fn = getattr(self.composio, "add_tool", None)
        add_app_fn = getattr(self.composio, "add_app", None)
        for tool_id in self.meta_tools:
            if callable(add_tool_fn):
                try:
                    add_tool_fn(tool_id)
                except Exception:
                    pass
        for app in self.target_apps:
            if callable(add_app_fn):
                try:
                    add_app_fn(app)
                except Exception:
                    pass
        logger.info("Loaded %d meta-tools and %d finance apps", 
                   len(self.meta_tools), len(self.target_apps))

    def summarize_state(self, context: Dict[str, Any]) -> str:
        """Generate a Gemini-summarized workflow status report."""
        prompt = (
            "As a workflow coordinator, analyze this context and:"
            "\n1. Highlight pending authentications"
            "\n2. Identify next execution steps"
            "\n3. Note any errors or required inputs"
            f"\n\nContext: {context}"
        )
        return self.llm.generate(prompt)

    def prepare_multi_execute_payload(self, ticker: str) -> Dict[str, Any]:
        """Build payload demonstrating COMPOSIO_MULTI_EXECUTE_TOOL."""
        return {
            "actions": [
                {
                    "app": "YAHOO_FINANCE",
                    "name": "get_stock_data",
                    "parameters": {"ticker": ticker},
                },
                {
                    "app": "GOOGLE_SHEETS",
                    "name": "append_row",
                    "parameters": {
                        "spreadsheet_id": "demo_sheet",
                        "values": [ticker, "{{stock_price}}", "{{analysis_summary}}"],
                    },
                },
            ],
            "context": {"ticker": ticker},
        }