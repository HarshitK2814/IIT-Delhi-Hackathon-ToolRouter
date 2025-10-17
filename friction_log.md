# Friction Log

| Date       | Module               | Challenge                              | Resolution                     |
|------------|----------------------|----------------------------------------|--------------------------------|
| 2025-10-17 | `llm/gemini_client`  | LiteLLM fallback to OpenAI             | Forced `provider=gemini`       |
| 2025-10-17 | `workflow_agent`     | Multi-execute payload formatting       | Used template literals         |
| 2025-10-17 | `orchestrator`       | Session timeout (300s)                 | Added keepalive ping           |

## Pending Issues
1. **Google Sheets auth**: Requires OAuth dance in demo
2. **Tool Router latency**: MCP URL sometimes delayed
3. **Gemini rate limits**: Need retry logic

## Lessons Learned
- Prefer direct `google-genai` over LiteLLM for control
- Composio SDK better with explicit tool registration
- Mocking auth states speeds up development