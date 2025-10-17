# Friction Log

| Date       | Module                                | Challenge                                             | Resolution                                      |
|------------|---------------------------------------|-------------------------------------------------------|-------------------------------------------------|
| 2025-10-17 | `llm/gemini_client`                   | LiteLLM fallback to OpenAI                            | Forced `provider=gemini`                        |
| 2025-10-17 | `workflow_agent`                      | Multi-execute payload formatting                      | Used template literals                          |
| 2025-10-17 | `orchestrator`                        | Session timeout (300s)                                | Added keepalive ping                            |
| 2025-10-18 | `workflows/hedge_fund_research`       | Missing `composio_gemini` optional dependency         | Guarded import and handled absence              |
| 2025-10-18 | `workflows/hedge_fund_research`       | Google Sheets service-account file path errors        | Switched to `$env:` assignment with full path   |
| 2025-10-18 | `workflows/hedge_fund_research`       | Service account lacked sheet access                   | Shared spreadsheet with service-account email   |
| 2025-10-18 | `workflows/hedge_fund_research`       | Sheet tab mismatch (`Try Out` vs `Sheet1`)            | Auto-created worksheet when missing             |
| 2025-10-18 | `workflows/hedge_fund_research`       | Gemini 503 overload responses                         | Added exponential backoff retry loop            |
| 2025-10-18 | `workflows/hedge_fund_research`       | Needed CSV-structured Gemini output for Sheets upload | Prompted for CSV + parsed rows before appending |
| 2025-10-18 | `repo`                                | Git push rejected due to remote updates               | Rebasing, resolving conflicts, then pushing     |

## Pending Issues
1. **Google Sheets auth**: Requires OAuth dance in demo
2. **Tool Router latency**: MCP URL sometimes delayed
3. **Gemini rate limits**: Need retry logic

## Lessons Learned
- Prefer direct `google-genai` over LiteLLM for control
- Composio SDK better with explicit tool registration
- Mocking auth states speeds up development