"""CLI entrypoint for the hedge fund research workflow."""
import argparse
import os
from typing import Optional

from dotenv import load_dotenv

from src.workflows.hedge_fund_research import HedgeFundResearchWorkflow
from src.utils.logging_utils import configure_logging


def main(ticker: Optional[str] = None) -> None:
    """Run the workflow with optional ticker input."""
    configure_logging()
    load_dotenv()
    
    if not ticker:
        ticker = input("Enter stock ticker (e.g. GOOGL): ").strip()
    
    workflow = HedgeFundResearchWorkflow(ticker=ticker)
    result = workflow.run_research()
    
    def _extract_research_plan(resp):
        # Try to extract human-readable text from a Gemini GenerateContentResponse-like object
        try:
            # candidates -> content -> parts
            candidates = getattr(resp, "candidates", None)
            if candidates and len(candidates) > 0:
                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", None)
                if parts:
                    texts = []
                    for p in parts:
                        # parts may have 'text' attribute
                        text = getattr(p, "text", None)
                        if text:
                            texts.append(text)
                        else:
                            # fallback to string representation
                            texts.append(str(p))
                    return "\n".join(texts)
        except Exception:
            pass
        # Fallback: string conversion
        try:
            return str(resp)
        except Exception:
            return "<no research plan available>"

    print(f"\nWorkflow completed for {ticker}")
    if isinstance(result, dict):
        print(f"Tool Router MCP URL: {result.get('mcp_url')}")
        print(f"Research plan:\n{result.get('research_plan')}")
        exec_payload = result.get('execute_payload')
        if exec_payload and isinstance(exec_payload, dict):
            actions = exec_payload.get('actions') or []
            print(f"Execution payload ready for: {list(actions)}")
        else:
            print("Execution payload: not available")
        # If the workflow attempted execution via Composio, show the response
        composio_exec = result.get('composio_execution')
        if composio_exec is not None:
            print(f"Composio execution result:\n{composio_exec}")
    else:
        # New-style response (Gemini), extract readable plan
        research_plan = _extract_research_plan(result)
        print(f"Research plan:\n{research_plan}")
        print("Tool Router MCP URL: not available for this run")
        print("Execution payload: not available for this run")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hedge Fund Research Workflow")
    parser.add_argument("--ticker", help="Stock ticker symbol")
    args = parser.parse_args()
    
    main(args.ticker)