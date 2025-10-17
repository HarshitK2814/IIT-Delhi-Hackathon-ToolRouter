import os
import logging
from composio import Composio
try:
    from composio_gemini import GeminiProvider
except Exception:
    GeminiProvider = None
from google import genai
from google.genai import types
from ..utils.cache_utils import load_cache, save_cache
from ..orchestrator.router_session import create_tool_router_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HedgeFundResearchWorkflow:
    """
    A workflow that performs hedge fund research using Gemini and Composio tools.
    """

    def __init__(self, ticker: str):
        self.ticker = ticker

        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in environment variables.")

        self.gemini_client = genai.Client(api_key=api_key)

        # Initialize Composio with Gemini provider
        if GeminiProvider is not None:
            self.composio = Composio(provider=GeminiProvider())
        else:
            logger.warning("composio_gemini provider not available; initializing Composio without provider")
            self.composio = Composio()

        logger.info(f"✅ Initialized HedgeFundResearchWorkflow for ticker: {self.ticker}")

    def run_research(self):
        """
        Executes the hedge fund research workflow.
        Uses Gemini for reasoning and Composio for tool execution.
        """
        try:
            # ✅ Use Composio SDK to list available toolkits and tools
            # Use a whitelist of toolkit slugs to avoid enumerating all toolkits.
            # The list can be provided via the COMPOSIO_TOOLKIT_WHITELIST env var as a
            # comma-separated list of slugs. If unset, we default to a small demo set.
            whitelist_env = os.getenv("COMPOSIO_TOOLKIT_WHITELIST")
            if whitelist_env:
                desired_toolkits = {s.strip() for s in whitelist_env.split(",") if s.strip()}
            else:
                # Default minimal set for demo / finance research
                desired_toolkits = {
                    "yahoo_finance",
                    "googlesheets",
                    "googledocs",
                    "google_search",
                }

            # Try cache first. Cache key is the sorted whitelist joined.
            cache_path = os.getenv("COMPOSIO_TOOLKIT_CACHE_PATH", ".composio_toolkit_cache.json")
            cache_ttl = int(os.getenv("COMPOSIO_TOOLKIT_CACHE_TTL", "3600"))
            cache_key = ",".join(sorted(desired_toolkits))

            tool_names = load_cache(cache_path, cache_key, max_age_seconds=cache_ttl)
            if tool_names is not None:
                logger.info("Loaded %d tool names from cache", len(tool_names))
            else:
                tool_names = []
                for slug in desired_toolkits:
                    try:
                        logger.info("Fetching tools for toolkit: %s", slug)
                        tools = self.composio.tools.get(user_id="system", toolkits=[slug])
                        for t in tools:
                            tool_names.append(getattr(t, "name", getattr(t, "slug", None)))
                    except Exception:
                        logger.debug("Could not fetch tools for toolkit %s", slug, exc_info=True)

                # persist to cache
                try:
                    save_cache(cache_path, cache_key, tool_names)
                    logger.info("Saved %d tool names to cache", len(tool_names))
                except Exception:
                    logger.debug("Failed to save toolkit cache", exc_info=True)

            logger.info(f"Available Composio tools: {tool_names}")

            # Create a chat interface using Gemini
            config = types.GenerateContentConfig()
            chat = self.gemini_client.chats.create(
                model="gemini-2.0-flash",
                config=config
            )

            # Ask Gemini about the ticker
            query = f"Give me a detailed financial and strategic analysis of {self.ticker}."
            logger.info(f"Sending query to Gemini: {query}")

            response = chat.send_message(query)

            # Print full Gemini response for debugging
            logger.debug(f"Full Gemini API Response: {response}")

            # Extract and handle function_call parts if any (guarding nested attributes)
            try:
                first_candidate = None
                if response.candidates:
                    first_candidate = response.candidates[0]

                content = getattr(first_candidate, "content", None)
                parts = getattr(content, "parts", None)

                if parts:
                    for part in parts:
                        function_call = getattr(part, "function_call", None)
                        if function_call:
                            logger.info(f"Function Call Name: {getattr(function_call, 'name', None)}")
                            logger.info(f"Function Call Arguments: {getattr(function_call, 'args', None)}")
                else:
                    logger.info("No function call found in the response.")
            except Exception:
                logger.debug("Error while parsing Gemini response function call parts", exc_info=True)

            # Normalize/flatten Gemini response into a human-readable string
            research_text = None
            try:
                candidates = getattr(response, "candidates", None)
                if candidates and len(candidates) > 0:
                    content = getattr(candidates[0], "content", None)
                    parts = getattr(content, "parts", None)
                    if parts:
                        texts = []
                        for p in parts:
                            text = getattr(p, "text", None)
                            if text:
                                texts.append(text)
                            else:
                                texts.append(str(p))
                        research_text = "\n".join(texts)
            except Exception:
                logger.debug("Failed to normalize Gemini response to text", exc_info=True)

            if not research_text:
                try:
                    research_text = str(response)
                except Exception:
                    research_text = "<no research plan available>"

            # Try to create a Tool Router session; if composio or tool-router isn't
            # installed this will raise a RuntimeError from router_session.create_tool_router_session
            mcp_url = None
            session_info = None
            try:
                session_info = create_tool_router_session()
                mcp_url = session_info.get("mcp_server_url")
            except Exception:
                logger.debug("Tool Router session not available in this environment", exc_info=True)

            # Build a minimal execution payload (placeholder) referencing available tools
            execute_payload = {
                "ticker": self.ticker,
                "tools": tool_names,
                "actions": [
                    {
                        "name": "research_summary",
                        "params": {"ticker": self.ticker},
                    }
                ],
            }

            result = {
                "ticker": self.ticker,
                "mcp_url": mcp_url,
                "research_plan": research_text,
                "auth_status": "ok",
                "execute_payload": execute_payload,
            }

            return result

        except Exception as e:
            logger.error(f"Error in HedgeFundResearchWorkflow: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    workflow = HedgeFundResearchWorkflow(ticker="GOOGL")
    result = workflow.run_research()
    print("\n✅ Workflow completed successfully.")
