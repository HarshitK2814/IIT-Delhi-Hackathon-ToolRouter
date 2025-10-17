# Demo Script Outline (90s)

## Phase 1: Discovery (0-30s)
1. **Start session**: Show MCP URL from `create_tool_router_session()`
2. **Research plan**: Display Gemini-generated plan for ticker
3. **Capabilities**: Print `capability_report()` from ResearchAgent

## Phase 2: Authentication (30-60s)
1. **Status check**: Show mock auth status (Yahoo: OK, Sheets: Pending)
2. **Remediation**: Briefly mention Composio CLI auth flow

## Phase 3: Execution (60-90s)
1. **Payload preview**: Display `prepare_multi_execute_payload()` structure
2. **Mock execution**: Simulate Yahoo → Sheets data flow
3. **Output**: Show logged results in terminal

## Backup Slides
- Architecture diagram (agents + workflow)
- Key files: `router_session.py`, `workflow_agent.py`
- Hackathon compliance checklist