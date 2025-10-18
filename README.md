# Hedge Fund Research Assistant

> Gemini-driven equity research workflow with Composio Tool Router orchestration and Google Sheets reporting.

---

## 1. Background
This project was built for the **IIT Delhi x Composio Hackathon** to showcase how an LLM-first agent can:
- Discover and authenticate tools dynamically via the Composio Tool Router.
- Run focused financial research using Gemini 2.0 Flash.
- Persist structured output directly into an analyst-friendly Google Sheet.

## 2. High-Level Architecture
```mermaid
graph TD
    %% === STYLES ===
    classDef input fill:#c9f2d0,stroke:#2a9134,stroke-width:2px,color:#000;
    classDef process fill:#d6e0f5,stroke:#334a94,stroke-width:2px,color:#000;
    classDef output fill:#ffe9b5,stroke:#b58b00,stroke-width:2px,color:#000;
    classDef tool fill:#f4c2c2,stroke:#a80000,stroke-width:2px,color:#000;
    classDef service fill:#cce5ff,stroke:#0056b3,stroke-width:2px,color:#000;

    %% === NODES ===
    A[Ticker Input]:::input
    B[Gemini 2.0 Flash - CSV Insights]:::process
    C[CSV Parser - Structured Data]:::process
    D[Sheets Uploader]:::tool
    G[Google Sheets (Data Storage)]:::service
    H[Risk Term Scanner - Financial Risks]:::process
    F[Composio Tool Router - Workflow Manager]:::tool
    I[Gmail Draft - Create Email]:::output
    J[Slack Alert - Post Message]:::output

    %% === CONNECTIONS ===
    A --> B
    B --> C
    C --> D
    D --> G
    C --> H
    H --> F
    F --> I
    F --> J

    %% === GROUPS ===
    subgraph Input_and_AI_Processing
        A
        B
        C
    end

    subgraph Data_Handling
        D
        G
    end

    subgraph Risk_and_Automation
        H
        F
        I
        J
    end


```

### Components
- **`src/workflows/hedge_fund_research.py`**: Orchestrates the end-to-end research flow—Gemini prompting, CSV parsing, Google Sheets ingestion, Gmail draft creation, and Slack alerting.
- **`src/orchestrator/router_session.py`**: Creates/logs a Composio Tool Router MCP session for tool discovery.
- **`src/agents/`**: Explorer agents used in earlier prototypes for orchestrating the workflow.
- **`src/utils/`**: Helpers for caching, HTTP, prompt formatting, etc.
- **`scripts/`**: Utilities for spot-checking Composio tool availability, Sheets execution, and local runs.
- **`friction_log.md`**: Timeline of blockers and fixes to help future contributors.

## 3. Demo Highlights
- **Gemini CSV Insight Generation**: Structured prompting drives Gemini 2.0 Flash to emit CSV rows (`Section`, `Insight`, `DataPoints`, `Risks`, `Opportunities`) ready for post-processing.
- **Risk-Aware Automations**: A lightweight risk-term scanner routes high-signal summaries to Composio, triggering Gmail drafts and Slack alerts only when needed.
- **Sheet Auto-Provisioning**: New worksheet tabs are created and populated automatically, keeping analyst spreadsheets up to date without manual prep.
- **Resilient Execution**: Exponential backoff guards against Gemini 503s while defensive handlers wrap Sheets, Gmail, and Slack calls.
- **Composio Observability**: Tool Router sessions log available toolkits, MCP URLs, and action payloads for downstream agents and debugging.

## 4. Prerequisites
- Python 3.12+
- [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key) API key for Gemini
- Google Cloud service account JSON with Google Sheets edit access
- [Composio](https://composio.dev/) API key with Tool Router access

## 5. Setup Guide
1. **Clone & install**
   ```bash
   git clone https://github.com/HarshitK2814/IIT-Delhi-Hackathon-ToolRouter.git
   cd IIT-Delhi-Hackathon-ToolRouter
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. **Configure environment**
   ```bash
   copy .env.example .env
   ```
   Populate the following keys:
   ```ini
   COMPOSIO_API_KEY=your_composio_api_key
   COMPOSIO_WORKSPACE_ID=your_workspace_id
   COMPOSIO_GMAIL_ACCOUNT_ID=<uuid via composio_client.connected_accounts.list>
   COMPOSIO_SLACK_ACCOUNT_ID=<uuid via composio_client.connected_accounts.list>
   GMAIL_RECIPIENTS="harshitfan382@gmail.com,harshitkumawat0910@gmail.com"
   SLACK_ALERT_CHANNEL=C09LMG2NGQ3
   RISK_TERMS="risk,competition,disruption,geopolitical,regulatory,failure,loss,debt,drawdown,negative,decrease,down,decline,crisis,impairment"
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_SHEETS_SPREADSHEET_ID=spreadsheet_id
   GOOGLE_SHEETS_SHEET_NAME=Try Out
   GOOGLE_SERVICE_ACCOUNT_FILE=C:\secrets\service-account.json
   TOOL_ROUTER_USER_ID=demo-user
   ```
   *PowerShell tip:* use `$env:VAR='value'` for one-off assignments. Retrieve Composio UUIDs programmatically with `composio_client.Composio(api_key).connected_accounts.list()`.
3. **Share the sheet**
   - Share the spreadsheet with the `client_email` from your service-account JSON.
   - Confirm edit access before running the workflow.

## 6. Running the Workflow
```bash
python -m src.main --ticker NVDA
```
### Execution Flow (End-to-End)
1. Loads environment variables and instantiates Gemini + Composio clients.
2. Prompts Gemini for a CSV-formatted research summary.
3. Parses CSV output, enriches rows with the ticker, and uploads data to Google Sheets (creating the tab if required).
4. Logs Composio tool metadata and caches the Tool Router MCP URL.
5. Executes optional Gmail + Slack actions via `_execute_action()`:
   - **Gmail**: `GMAIL_CREATE_EMAIL_DRAFT` with `recipient_email`, `extra_recipients`, `subject`, `body`, `is_html` as needed.
   - **Slack**: `SLACK_CHAT_POST_MESSAGE` with truncated Markdown blocks plus a sheet link.
6. Returns a JSON payload summarizing research results, Sheets status, and automation execution logs.

## 7. Automation Workflows
- **Gmail Drafting (`_prepare_gmail_action`)**
  - Pulls recipients from `GMAIL_RECIPIENTS`.
  - Adds sheet link and research summary to the message body.
  - Uses Composio v3 `tools.execute` to create a draft tied to `COMPOSIO_GMAIL_ACCOUNT_ID`.

- **Slack Alerts (`_prepare_slack_action`)**
  - Scans `research_text` for terms in `RISK_TERMS`.
  - Truncates summary to <3000 characters and posts to `SLACK_ALERT_CHANNEL` if a risk is detected.

- **Tool Discovery**
  - `list_composio_tools.py` provides a CLI snapshot of available toolkits and actions for debugging.

## 8. Supporting Scripts
- `scripts/list_composio_tools.py`
- `scripts/run_with_env.py`
- `scripts/try_sheets_execute.py`

## 9. Troubleshooting & FAQ
- **Sheets 403**: Ensure the service-account email has editor access and `GOOGLE_SERVICE_ACCOUNT_FILE` points to the rotated credential outside the repo.
- **WorksheetNotFound**: The workflow auto-creates tabs; adjust `GOOGLE_SHEETS_SHEET_NAME` if the tab was renamed.
- **Gemini 503 UNAVAILABLE**: Retries are in place—wait a few seconds and rerun.
- **`composio_gemini` missing**: Optional plugin; guarded import prevents crashes.
- **Composio `Invalid uuid`**: Retrieve connected-account UUIDs with the Composio client and update `.env` accordingly.
- **Gmail draft `recipient_email` error**: `GMAIL_RECIPIENTS` must have at least one email; the first becomes `recipient_email`, the rest `extra_recipients`.
- **Slack `invalid_blocks`**: The workflow truncates payloads automatically. Keep downstream blocks concise.
- **Git push rejected**: Use `git pull --rebase origin main`, resolve conflicts (refer to `friction_log.md`), then `git push`.

## 10. Testing & Verification Checklist
- `python -m src.main --ticker NVDA`
- `python scripts/list_composio_tools.py`
- `python scripts/try_sheets_execute.py --ticker NVDA`
- Manual verification: Gmail draft reaches intended recipients; Slack alert posts to `SLACK_ALERT_CHANNEL`.

## 11. Deployment Notes
- Set `COMPOSIO_API_KEY`, `GEMINI_API_KEY`, `COMPOSIO_*_ACCOUNT_ID`, and sheet identifiers as environment variables in CI/CD or secrets store.
- Mount the service-account JSON at the path defined in `GOOGLE_SERVICE_ACCOUNT_FILE`.
- Ensure network access to Composio and Google APIs from the deployment target.

## 12. Contributing
1. `git checkout -b feature/my-update`
2. Implement changes and add tests.
3. Update `friction_log.md` with new hurdles/solutions.
4. Open a PR referencing the affected modules.

## 13. Security Notes
- Store service-account JSON outside the repo; rotate keys immediately if committed.
- `.gitignore` excludes `*.json`, `.env`, logs, and cache files—keep it that way.
- Review `friction_log.md` for credential-related incidents and mitigations.

## 14. Resources
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [Composio Tool Router Overview](https://docs.composio.dev/)
- [gspread Documentation](https://docs.gspread.org/)

## 15. Acknowledgements
- IIT Delhi Hackathon organizers & mentors
- Composio engineering team for Tool Router access
- Google AI Studio for Gemini credits

---

For questions or suggestions, open an issue or ping `@HarshitK2814` on GitHub.


