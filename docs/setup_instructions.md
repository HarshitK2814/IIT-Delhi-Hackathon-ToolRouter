# Setup Instructions

## 1. Prerequisites
- Python 3.10+
- Composio CLI installed (`pip install composio-cli`)
- Google Cloud & Yahoo Finance developer accounts

## 2. Environment Setup
```bash
# Clone repo
cd hedge-fund-research

# Create virtual env
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys
```

## 3. Composio Configuration
```bash
# Login to Composio CLI
composio auth login

# Connect apps (repeat for each)
composio apps connect yahoo_finance
composio apps connect google_sheets
```

## 4. Validate Setup
```bash
# Check Gemini
python scripts/test_gemini_litellm.py

# Verify tool access
python scripts/tool_router_demo.py
```
