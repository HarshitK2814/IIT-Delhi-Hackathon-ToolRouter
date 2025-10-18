import os
import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from composio import Composio
try:
    from composio_client import Composio as ComposioV3
except ImportError:
    ComposioV3 = None  # type: ignore
try:
    from composio.client.enums import Action
except ImportError:
    Action = None  # type: ignore
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
            raise ValueError(" GEMINI_API_KEY not found in environment variables.")

        self.gemini_client = genai.Client(api_key=api_key)

        # Initialize Composio with Gemini provider
        self.composio = None
        if GeminiProvider is not None:
            try:
                self.composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"), provider=GeminiProvider())
            except TypeError:
                self.composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))
        else:
            logger.warning("composio_gemini provider not available; initializing Composio without provider")
            self.composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))

        self.composio_v3 = None
        if ComposioV3 is not None:
            try:
                self.composio_v3 = ComposioV3(api_key=os.getenv("COMPOSIO_API_KEY"))
            except Exception:
                logger.debug("Failed to instantiate composio_client.Composio", exc_info=True)
                self.composio_v3 = None

        logger.info(f" Initialized HedgeFundResearchWorkflow for ticker: {self.ticker}")
        self.tool_catalog: List[Dict[str, Any]] = []
        self._gmail_account_id = os.getenv("COMPOSIO_GMAIL_ACCOUNT_ID", "ca_Noajhssf1Q4q")
        self._slack_account_id = os.getenv("COMPOSIO_SLACK_ACCOUNT_ID", "ca_2JwaRAD5S1sG")
        sheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        self.sheet_url = (
            os.getenv("GOOGLE_SHEETS_SHARE_URL")
            or (f"https://docs.google.com/spreadsheets/d/{sheet_id}" if sheet_id else None)
        )
        self.gmail_recipients = [
            addr.strip()
            for addr in os.getenv(
                "GMAIL_RECIPIENTS",
                "harshitfan382@gmail.com,harshitkumawat0910@gmail.com",
            ).split(",")
            if addr.strip()
        ]
        self.slack_channel = os.getenv("SLACK_ALERT_CHANNEL", "C09LMG2NGQ3")
        risk_terms_env = os.getenv(
            "RISK_TERMS",
            "risk,competition,disruption,geopolitical,regulatory,failure,loss,debt,drawdown,negative,decrease,down,decline,crisis,impairment",
        )
        self.risk_terms = [term.strip().lower() for term in risk_terms_env.split(",") if term.strip()]

    def _find_tool(self, toolkit: str, keyword: str) -> Optional[str]:
        keyword = keyword.lower()
        for record in self.tool_catalog:
            if record.get("toolkit") == toolkit:
                slug = (record.get("slug") or "").lower()
                if keyword in slug:
                    return record.get("slug") or record.get("id")
        return None

    def _build_csv_download_url(self) -> Optional[str]:
        sheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        sheet_name = os.getenv("GOOGLE_SHEETS_SHEET_NAME", "Try Out")
        if not sheet_id:
            return None
        return (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
            f"?tqx=out:csv&sheet={sheet_name}"
        )

    def _prepare_gmail_action(self, research_text: str) -> Optional[Dict[str, Any]]:
        if not self._gmail_account_id or not self.gmail_recipients:
            logger.info("Skipping Gmail automation; account or recipients missing")
            return None
        action_slug = self._find_tool("gmail", "send_email")
        if not action_slug:
            action_slug = self._find_tool("gmail", "create_email_draft")
        if not action_slug:
            logger.info("No Gmail send/draft tool available; skipping email automation")
            return None
        csv_url = self._build_csv_download_url()
        attachments: List[Dict[str, Any]] = []
        if csv_url:
            attachments.append(
                {
                    "url": csv_url,
                    "mime_type": "text/csv",
                    "title": f"{self.ticker}_analysis.csv",
                }
            )
        subject = f"{self.ticker} hedge fund research update"
        body_lines = [
            f"Ticker: {self.ticker}",
            "Summary:",
            research_text,
        ]
        if self.sheet_url:
            body_lines.append(f"Google Sheet: {self.sheet_url}")
        primary_recipient = self.gmail_recipients[0]
        extra_recipients = self.gmail_recipients[1:] if len(self.gmail_recipients) > 1 else []

        params: Dict[str, Any] = {
            "connected_account_id": self._gmail_account_id,
            "recipient_email": primary_recipient,
            "subject": subject,
            "body": "\n\n".join(body_lines),
            "is_html": False,
        }
        if extra_recipients:
            params["extra_recipients"] = extra_recipients
        if csv_url:
            params.setdefault("body", "")
        return {"action": action_slug, "params": params}

    def _prepare_slack_action(self, research_text: str) -> Optional[Dict[str, Any]]:
        if not self._slack_account_id or not self.slack_channel:
            logger.info("Skipping Slack automation; account or channel missing")
            return None
        text_lower = research_text.lower()
        if not any(term in text_lower for term in self.risk_terms):
            logger.info("No risk terms detected in research; Slack alert suppressed")
            return None
        action_slug = self._find_tool("slack", "post_message")
        if not action_slug:
            action_slug = self._find_tool("slack", "send_message")
        if not action_slug:
            logger.info("No Slack message action available; skipping alert")
            return None
        base_text = f"Attention required for {self.ticker}"
        slack_body = research_text.strip()
        max_block_chars = 2900
        alert_text = f"*{base_text}*\n{slack_body}" if slack_body else f"*{base_text}*"
        if len(alert_text) > max_block_chars:
            alert_text = alert_text[: max_block_chars - 3] + "..."

        blocks: List[Dict[str, Any]] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert_text,
                },
            }
        ]
        if self.sheet_url:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{self.sheet_url}|View Google Sheet>",
                    },
                }
            )
        params: Dict[str, Any] = {
            "connected_account_id": self._slack_account_id,
            "channel": self.slack_channel,
            "text": base_text,
            "blocks": json.dumps(blocks),
        }
        return {"action": action_slug, "params": params}

    def run_research(self):
        """
        Executes the hedge fund research workflow.
        Uses Gemini for reasoning and Composio for tool execution.
        """
        try:
            # Use Composio SDK to list available toolkits and tools
            # Use a whitelist of toolkit slugs to avoid enumerating all toolkits.
            # The list can be provided via the COMPOSIO_TOOLKIT_WHITELIST env var as a
            # comma-separated list of slugs. If unset, we default to a small demo set.
            whitelist_env = os.getenv("COMPOSIO_TOOLKIT_WHITELIST")
            if whitelist_env:
                desired_toolkits = {s.strip() for s in whitelist_env.split(",") if s.strip()}
            else:
                # Default minimal set for demo / finance research
                desired_toolkits = {
                    "googlesheets",
                    "googledocs",
                    "gmail",
                    "slack",
                    "serpapi",
                    "alpha_vantage",
                }

            # Try cache first. Cache key is the sorted whitelist joined.
            cache_path = os.getenv("COMPOSIO_TOOLKIT_CACHE_PATH", ".composio_toolkit_cache.json")
            cache_ttl = int(os.getenv("COMPOSIO_TOOLKIT_CACHE_TTL", "3600"))
            cache_key = ",".join(sorted(desired_toolkits))

            tool_catalog: List[Dict[str, Any]] = load_cache(cache_path, cache_key, max_age_seconds=cache_ttl) or []
            if tool_catalog:
                logger.info("Loaded %d tools from cache", len(tool_catalog))
            else:
                for slug in desired_toolkits:
                    logger.info("Fetching tools for toolkit: %s", slug)
                    entries: List[Any] = []

                    if self.composio_v3 is not None:
                        try:
                            response = self.composio_v3.tools.list(toolkit_slug=slug)
                            items = getattr(response, "items", None) or []
                            for item in items:
                                if hasattr(item, "model_dump"):
                                    entries.append(item.model_dump())
                                elif hasattr(item, "dict"):
                                    entries.append(item.dict())
                                elif isinstance(item, dict):
                                    entries.append(item)
                        except Exception:
                            logger.debug("composio_client.Composio.tools.list failed for %s", slug, exc_info=True)

                    if not entries and self.composio is not None:
                        tools_api = getattr(self.composio, "tools", None)
                        if tools_api is not None:
                            for method_name in ("list", "get"):
                                method = getattr(tools_api, method_name, None)
                                if not callable(method):
                                    continue
                                try:
                                    if method_name == "list":
                                        payload = method(toolkits=[slug])
                                    else:
                                        payload = method(user_id="system", toolkits=[slug])
                                    if payload:
                                        entries = list(payload)
                                        break
                                except TypeError:
                                    continue
                                except Exception as exc:
                                    logger.debug("composio.tools.%s failed for %s", method_name, slug, exc_info=True)

                    if not entries and self.composio is not None:
                        http_client = getattr(self.composio, "http", None) or getattr(self.composio, "_http_client", None)
                        endpoints = getattr(self.composio, "endpoints", None)
                        if http_client is not None and endpoints is not None:
                            v3 = getattr(endpoints, "v3", None)
                            tools_url = getattr(v3, "tools", None) if v3 is not None else None
                            if tools_url is not None:
                                try:
                                    resp = http_client.get(str(tools_url), params={"toolkit_slug": slug})
                                    data = resp.json()
                                    payload = data.get("items") or data.get("data") or []
                                    if isinstance(payload, list):
                                        entries.extend(payload)
                                except Exception:
                                    logger.debug("HTTP fallback failed for %s", slug, exc_info=True)

                    for entry in entries or []:
                        if hasattr(entry, "model_dump"):
                            source = entry.model_dump()
                        elif hasattr(entry, "dict"):
                            source = entry.dict()
                        elif isinstance(entry, dict):
                            source = entry
                        else:
                            continue
                        if not isinstance(source, dict):
                            continue

                        toolkit_info = source.get("toolkit") or {}
                        record = {
                            "toolkit": slug,
                            "id": source.get("id") or source.get("slug") or source.get("tool_slug"),
                            "slug": source.get("slug") or source.get("tool_slug") or (toolkit_info.get("slug") if isinstance(toolkit_info, dict) else None),
                            "name": source.get("name") or source.get("display_name") or source.get("id"),
                        }

                        if record.get("slug") or record.get("name"):
                            tool_catalog.append(record)
                        else:
                            logger.info("Unable to derive slug/name for tool in %s; keys=%s", slug, list(source.keys()))
                deduped: Dict[str, Dict[str, Any]] = {}
                for record in tool_catalog:
                    key = (
                        (record.get("slug") or "")
                        or (record.get("id") or "")
                        or (record.get("name") or "")
                    ).lower()
                    if key and key not in deduped:
                        deduped[key] = record
                tool_catalog = list(deduped.values())
                try:
                    save_cache(cache_path, cache_key, tool_catalog)
                    logger.info("Saved %d tools to cache", len(tool_catalog))
                except Exception:
                    logger.debug("Failed to save toolkit cache", exc_info=True)

            self.tool_catalog = tool_catalog
            tool_summary = [
                f"{rec.get('toolkit')}::{rec.get('slug') or rec.get('name') or rec.get('id')}"
                for rec in tool_catalog
            ]
            logger.info("Available Composio tools: %s", tool_summary)

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
            gmail_action = self._prepare_gmail_action(research_text)
            slack_action = self._prepare_slack_action(research_text)

            actions: List[Dict[str, Any]] = []
            if gmail_action:
                actions.append(gmail_action)
            if slack_action:
                actions.append(slack_action)

            # Attempt synchronous execution (best-effort). If execution fails or client is unavailable,
            # the action definitions remain in execute_payload for an external agent to run later.
            execution_results: List[Dict[str, Any]] = []
            for action in actions:
                result_payload = self._execute_action(action["action"], action["params"])
                if result_payload is not None:
                    execution_results.append({"action": action["action"], "result": result_payload})

            execute_payload = {
                "ticker": self.ticker,
                "research_summary": research_text,
                "actions": actions,
            }

            result = {
                "ticker": self.ticker,
                "mcp_url": mcp_url,
                "research_plan": research_text,
                "auth_status": "ok",
                "execute_payload": execute_payload,
                "composio_execution": execution_results,
            }

            return result

        except Exception as e:
            logger.error(f"Error in HedgeFundResearchWorkflow: {e}", exc_info=True)
            raise

    def _execute_action(self, action_slug: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("Executing action %s with params %s", action_slug, params)

        # Prefer the composio_client v3 execution API because it accepts raw slugs
        if self.composio_v3 is not None:
            try:
                arguments = dict(params)
                connected_account_id = arguments.pop("connected_account_id", None)
                user_id = arguments.pop("user_id", None)
                allow_tracing = arguments.pop("allow_tracing", None)
                response = self.composio_v3.tools.execute(
                    tool_slug=action_slug,
                    arguments=arguments or None,
                    connected_account_id=connected_account_id,
                    user_id=user_id,
                    allow_tracing=allow_tracing,
                )
                payload = response
                if hasattr(response, "model_dump"):
                    payload = response.model_dump()
                logger.info("Action %s succeeded via composio_client with response %s", action_slug, payload)
                return payload if isinstance(payload, dict) else {"data": payload}
            except Exception:
                logger.error("composio_client.tools.execute failed for %s", action_slug, exc_info=True)

        # Fallback to legacy SDK if available
        if self.composio is None or not hasattr(self.composio, "actions"):
            logger.info("No Composio client available; skipping execution for %s", action_slug)
            return {"error": "composio_client_unavailable"}

        try:
            action_enum = getattr(Action, action_slug, None) if Action is not None else None
            if action_enum is None:
                logger.error("Legacy Composio action enumeration missing for %s", action_slug)
                return {"error": "legacy_action_not_found"}

            arguments = dict(params)
            connected_account_id = arguments.pop("connected_account_id", None)
            allow_tracing = arguments.pop("allow_tracing", False)
            result = self.composio.actions.execute(
                action=action_enum,
                params=arguments,
                connected_account=connected_account_id,
                allow_tracing=allow_tracing,
            )
            if isinstance(result, dict):
                logger.info("Action %s succeeded with response %s", action_slug, result)
                return result
            response_payload = {
                "status": getattr(result, "status", None),
                "data": getattr(result, "data", None),
                "raw": repr(result),
            }
            logger.info("Action %s succeeded with response %s", action_slug, response_payload)
            return response_payload
        except Exception as exc:
            logger.error("Failed to execute action %s: %s", action_slug, exc, exc_info=True)
            return {"error": str(exc)}

if __name__ == "__main__":
    workflow = HedgeFundResearchWorkflow(ticker="GOOGL")
    result = workflow.run_research()
    print("\n✅ Workflow completed successfully.")
