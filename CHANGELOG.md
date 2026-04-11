# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-04-12

### Added
- Initial release of AI Research Agent
- LangGraph-based `StateGraph` workflow with `clarify`, `research`, `write_report`, and `save` nodes
- Human-in-the-loop support using LangGraph `interrupt()` / `Command(resume=)` pattern
- Local LLM integration via Ollama (default model: `llama3.2:3b`)
- DuckDuckGo web search integration retrieving 10+ sources per query
- Source citation in every generated report
- CLI interface (`research_agent.py`) for terminal-based research sessions
- Flask web application (`web_app/app.py`) with Server-Sent Events (SSE) streaming
- Single-page web UI with real-time progress indicators and rendered Markdown output
- SQLite database with SQLAlchemy ORM for research session history (`db.py`)
- Markdown report generation saved to `reports/` directory
- `requirements.txt` with all project dependencies
- `docs/TECHNICAL_DOCUMENTATION.md` — architecture deep-dive and API reference
- `docs/BUSINESS_REPORT.md` — problem analysis, ROI, use cases, and implementation roadmap
- `.gitignore` with Python, SQLite, and environment-specific exclusions
- `README.md` with project overview, features, architecture diagram, and setup instructions

---

## [Unreleased]

### Planned
- Support for additional LLM providers (OpenAI, Anthropic) via environment variable toggle
- Export reports in PDF and DOCX formats
- User authentication for the web application
- Scheduled / automated research runs
- Docker / Docker Compose setup for one-command deployment
- Unit and integration test coverage
