# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

NotionAgent — a Python project intended to build an agent that interacts with the Notion API. The project is in its initial setup stage; `main.py` currently contains only the PyCharm template placeholder.

## Environment

- Python 3.14, virtual environment at `.venv/`
- Activate: `.venv\Scripts\activate` (PowerShell) or `.venv/Scripts/activate` (bash)
- Install deps: `pip install -r requirements.txt` (file does not exist yet — create it when adding dependencies)

## Running

```powershell
python main.py
```

## Dependencies to add

When building the Notion integration, the expected core packages are:
- `notion-client` — official Notion API SDK
- `anthropic` — Claude API for agent logic

Pin all dependencies in `requirements.txt`.
