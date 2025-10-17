# Hedge Fund Research Assistant

**Composio Tool Router (Beta) Hackathon Submission**  
Demonstrates discovery → authentication → execution pipeline with Gemini and Composio meta-tools.

## Features
- **Gemini-first LLM**: All agents use `google-genai` with LiteLLM fallback
- **Tool Router integration**:
  - Session initialization with MCP URL logging
  - Meta-tool usage (`COMPOSIO_MULTI_EXECUTE_TOOL` shown)
- **Multi-app orchestration**: Yahoo Finance + Google Sheets coordination

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Configure `.env` from `.env.example`:
```ini
COMPOSIO_API_KEY=your_key
GEMINI_API_KEY=your_key
```
3. Run demo:
```bash
python -m src.main --ticker GOOGL
```

## Tools Demonstrated
- **Meta-tools**: 
  - `COMPOSIO_SEARCH_TOOLS` 
  - `COMPOSIO_MULTI_EXECUTE_TOOL`
- **Finance apps**: 
  - Yahoo Finance (market data) 
  - Google Sheets (logging)

## Demo Script
```bash
# Test Gemini connectivity
python scripts/test_gemini_litellm.py

# List available tools
python scripts/tool_router_demo.py

# Run full workflow
python -m src.main
```