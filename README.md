# 🔬 AI Research Agent

An autonomous research assistant that generates structured, source-cited reports from any topic — powered by **LangGraph**, **Ollama** (local LLM), and **DuckDuckGo Search**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-green)
![Flask](https://img.shields.io/badge/Flask-Web%20App-lightgrey?logo=flask)

---

## How It Works

```
User enters topic → AI asks clarifying questions → User answers →
AI searches the web (10+ sources) → AI synthesizes findings →
AI writes structured Markdown report → Report saved & archived
```

The agent uses a **human-in-the-loop** pattern: instead of guessing what you need, it pauses to ask clarifying questions about scope, audience, and focus — then delivers a tailored report.

---

## Features

- **Local LLM** — Runs entirely on your machine via Ollama. No API keys, no costs, no data leaves your network.
- **Live Web Search** — DuckDuckGo integration retrieves 10+ real-time sources per query.
- **Source Citations** — Every claim is traceable to a cited source. No hallucinations.
- **Human-in-the-Loop** — LangGraph `interrupt()`/`Command(resume=)` for intelligent clarification before research.
- **Dual Interface** — CLI for power users, Flask web app with SSE streaming for everyone else.
- **Research History** — SQLite database archives every session (topic, sources, full report).
- **Markdown Reports** — Professional, structured output saved to `reports/` directory.

---

## Architecture

```
┌──────────────┐     ┌─────────────────────────┐     ┌──────────────┐
│   CLI / Web  │────▶│   LangGraph StateGraph   │────▶│   Reports    │
│   Interface  │     │                           │     │   (Markdown) │
└──────────────┘     │  clarify ──▶ research     │     └──────────────┘
                     │     │         ──▶ write    │
                     │  interrupt()   ──▶ save    │     ┌──────────────┐
                     │     │                      │────▶│   SQLite DB  │
                     └─────┼──────────────────────┘     └──────────────┘
                           │          │
                     ┌─────▼───┐ ┌────▼────────┐
                     │  Ollama │ │  DuckDuckGo  │
                     │ (local) │ │  (web search)│
                     └─────────┘ └──────────────┘
```

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.ai/)** installed and running

### Installation

```bash
# Clone the repository
git clone https://github.com/eboekenh/research_agent.git
cd research_agent

# Install dependencies
pip install -r requirements.txt

# Pull the default model
ollama pull llama3.2:3b
```

### Run — CLI

```bash
python research_agent.py
```

You'll be prompted to enter a topic, answer clarifying questions, and then the agent researches and generates a report.

### Run — Web App

```bash
python web_app/app.py
```

Open **http://localhost:5000** in your browser. The web UI provides:
- Topic input with real-time clarifying questions
- SSE-streamed progress indicators
- Rendered Markdown report with download option
- Searchable research history sidebar

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2:3b` | Set via environment variable to use a different model (e.g., `llama3.1:8b`, `mistral`) |
| `DATABASE_URL` | `sqlite:///research_agent.db` | SQLAlchemy connection string |

```bash
# Example: use a larger model
OLLAMA_MODEL=llama3.1:8b python research_agent.py
```

---

## Project Structure

```
├── graph.py                 # LangGraph workflow (core engine)
├── db.py                    # SQLAlchemy models + SQLite helpers
├── research_agent.py        # CLI interface
├── requirements.txt         # Python dependencies
├── web_app/
│   ├── app.py               # Flask server (REST API + SSE)
│   ├── templates/
│   │   └── index.html       # Single-page web UI
│   └── static/
│       └── style.css        # Styles
├── reports/                 # Generated Markdown reports
└── docs/
    ├── TECHNICAL_DOCUMENTATION.md
    └── BUSINESS_REPORT.md
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) (StateGraph + human-in-the-loop) |
| Local LLM | [Ollama](https://ollama.ai/) via [LangChain-Ollama](https://python.langchain.com/docs/integrations/llms/ollama/) |
| Web Search | [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/) (free, no API key) |
| Backend | [Flask](https://flask.palletsprojects.com/) with Server-Sent Events |
| Database | [SQLite](https://www.sqlite.org/) + [SQLAlchemy](https://www.sqlalchemy.org/) ORM |
| Frontend | Vanilla JS + [marked.js](https://marked.js.org/) for Markdown rendering |

---

## Documentation

- **[Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md)** — Architecture deep-dive, API reference, design decisions
- **[Business Report](docs/BUSINESS_REPORT.md)** — Problem analysis, ROI calculation, use cases, implementation roadmap

---

## License

This project is for educational and portfolio purposes.
