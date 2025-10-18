<<<<<<< HEAD
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
| 2025-10-19 | `workflows/hedge_fund_research`       | Composio v3 Gmail action rejected `action_slug` param | Switched to `composio_client.tools.execute` & Action enum fallback |
| 2025-10-19 | `workflows/hedge_fund_research`       | Gmail draft failed: missing `recipient_email` field   | Remapped recipients (`recipient_email`, `extra_recipients`) |
| 2025-10-19 | `workflows/hedge_fund_research`       | Slack `invalid_blocks` due to long Markdown payload   | Truncated to <3000 chars and fixed link syntax  |
| 2025-10-19 | `workflows/hedge_fund_research`       | Composio `Invalid uuid` errors for Gmail/Slack        | Pulled UUIDs via `connected_accounts.list()` and updated `.env` |
| 2025-10-19 | `repo`                                | Service-account JSON checked into repo                | Added `.gitignore`, advised key rotation & removal |

## Pending Issues
1. **Google Sheets auth**: Requires OAuth dance in demo
2. **Tool Router latency**: MCP URL sometimes delayed
3. **Gemini rate limits**: Need retry logic
4. **Credential hygiene**: Remove leaked JSON from Git history and rotate key

## Lessons Learned
- Prefer direct `google-genai` over LiteLLM for control
- Composio SDK better with explicit tool registration
- Mocking auth states speeds up development
- Connected-account UUIDs differ from legacy IDs—always inspect `connected_accounts.list()`
- Slack block payloads must respect schema size limits
>>>>>>> 43ffc59 (Document automation updates and env defaults)
