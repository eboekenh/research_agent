# AI Research Agent — Technical Documentation

> An autonomous research workflow powered by LangGraph, Ollama, and DuckDuckGo Search with a human-in-the-loop interaction pattern.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Graph Workflow Design](#graph-workflow-design)
6. [Data Model](#data-model)
7. [API Reference](#api-reference)
8. [Frontend Architecture](#frontend-architecture)
9. [Setup & Installation](#setup--installation)
10. [Configuration](#configuration)
11. [Project Structure](#project-structure)
12. [Design Decisions & Trade-offs](#design-decisions--trade-offs)
13. [Future Improvements](#future-improvements)

---

## System Overview

The AI Research Agent is a full-stack application that automates the research report generation process. Given a topic, the system:

1. **Asks clarifying questions** to understand scope, audience, and constraints
2. **Waits for human input** (human-in-the-loop via LangGraph interrupts)
3. **Searches the web** using DuckDuckGo to gather real-time sources
4. **Synthesizes findings** through a local LLM (Ollama)
5. **Generates a structured Markdown report** with citations
6. **Persists results** to a SQLite database and the filesystem

The system is accessible via both a **CLI interface** and a **Flask web application** with Server-Sent Events (SSE) for real-time progress streaming.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  ┌──────────────────┐       ┌────────────────────────────┐  │
│  │  CLI (terminal)  │       │  Web UI (HTML/CSS/JS)      │  │
│  │  research_agent  │       │  SSE streaming + marked.js │  │
│  └────────┬─────────┘       └──────────┬─────────────────┘  │
│           │                            │                    │
├───────────┼────────────────────────────┼────────────────────┤
│           │        Application Layer   │                    │
│           │   ┌────────────────────────┴──────┐             │
│           │   │  Flask Server (web_app/app.py) │             │
│           │   │  REST API + SSE endpoints      │             │
│           │   └────────────────┬───────────────┘             │
│           │                    │                            │
│           └────────┬───────────┘                            │
│                    │                                        │
│           ┌────────▼────────────────────────┐               │
│           │  LangGraph StateGraph (graph.py)│               │
│           │  ┌────────┐  ┌─────────┐        │               │
│           │  │Clarify │→ │Research │        │               │
│           │  │(+inter-│  │(DDG +   │        │               │
│           │  │ rupt)  │  │ LLM)    │        │               │
│           │  └────────┘  └────┬────┘        │               │
│           │  ┌────────────────▼────┐        │               │
│           │  │ Write Report (LLM)  │        │               │
│           │  └─────────┬──────────┘         │               │
│           │  ┌─────────▼──────────┐         │               │
│           │  │ Save Report (I/O)  │         │               │
│           │  └────────────────────┘         │               │
│           └─────────────────────────────────┘               │
│                    │            │                            │
├────────────────────┼────────────┼────────────────────────────┤
│           Infrastructure Layer │                            │
│  ┌─────────────────┐  ┌───────▼────────┐  ┌─────────────┐  │
│  │  Ollama (local)  │  │  SQLite (db.py)│  │  DuckDuckGo │  │
│  │  llama3.2:3b     │  │  SQLAlchemy    │  │  DDGS API   │  │
│  └──────────────────┘  └────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM Runtime** | Ollama + llama3.2:3b | Local inference, zero API cost, privacy-preserving |
| **LLM Framework** | LangChain + LangChain-Ollama | Standardized LLM interface and prompt management |
| **Orchestration** | LangGraph | Stateful, graph-based workflow with checkpointing and human-in-the-loop |
| **Web Search** | DuckDuckGo Search (DDGS) | Free, no-API-key web search for real-time information |
| **Backend** | Flask | Lightweight HTTP server with SSE support |
| **Database** | SQLite + SQLAlchemy ORM | Zero-config persistence for research history |
| **Frontend** | Vanilla HTML/CSS/JS + marked.js | Single-page app with Markdown rendering |
| **Environment** | Python 3.10+, python-dotenv | Configuration management |

---

## Core Components

### 1. `graph.py` — LangGraph Workflow Engine

The heart of the system. Defines the research workflow as a directed acyclic graph (DAG) using LangGraph's `StateGraph`.

**State Schema:**

```python
class ResearchState(TypedDict):
    topic: str            # User's research topic
    clarifications: str   # User's answers to clarifying questions
    research_notes: str   # LLM-synthesized research notes
    sources: list[dict]   # List of {url, title} from web search
    report: str           # Final Markdown report
    report_path: str      # Filesystem path to saved report
```

**Key Functions:**

| Function | Description |
|----------|-------------|
| `_invoke_with_retry(llm, prompt, max_retries=5, initial_wait=2)` | Exponential backoff wrapper for LLM calls (handles 429/rate-limit errors) |
| `make_clarify_node(llm, on_progress)` | Factory: generates clarifying questions, then calls `interrupt()` for human input |
| `make_research_node(llm, on_progress)` | Factory: DuckDuckGo search → LLM synthesis of 10 web sources |
| `make_write_report_node(llm, on_progress)` | Factory: generates structured Markdown report from research notes |
| `make_save_report_node(on_progress)` | Factory: saves report to `reports/` directory with sanitized filename |
| `build_graph(on_progress=None)` | Compiles the full StateGraph with `InMemorySaver` checkpointer |

**Human-in-the-Loop Pattern:**

```python
# In the clarify node:
answers = interrupt(questions)   # Pauses graph execution
return {"clarifications": answers}

# Resumed by caller:
graph.invoke(Command(resume=user_answers), config)
```

LangGraph's `interrupt()` halts execution and yields control back to the caller. The caller collects user input and resumes with `Command(resume=...)`. The `InMemorySaver` checkpointer preserves graph state between invocations.

### 2. `db.py` — Persistence Layer

SQLAlchemy ORM over SQLite for zero-configuration storage.

**Schema:**

```
researches
├── id            VARCHAR(36)  PK  (UUID v4)
├── topic         TEXT         NOT NULL
├── clarifications TEXT
├── report        TEXT
├── report_path   VARCHAR(255)
├── sources       JSON         (list of {url, title})
└── created_at    DATETIME     (UTC, auto-generated)
```

**API:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `init_db()` | `() → None` | Creates tables if not exist |
| `save_research()` | `(topic, clarifications, report, report_path, sources) → str` | Persists a research record, returns UUID |
| `get_all_researches()` | `() → list[dict]` | Returns all records (id, topic, created_at), newest first |
| `get_research()` | `(research_id) → dict \| None` | Returns full record by ID |

### 3. `research_agent.py` — CLI Interface

Interactive command-line runner that:
1. Prompts for a topic
2. Invokes the graph (pauses at clarify interrupt)
3. Displays clarifying questions
4. Collects user answers via `input()`
5. Resumes the graph to completion
6. Saves to database

### 4. `web_app/app.py` — Flask Web Server

REST API with SSE streaming for the web interface.

**Session Management:**

Active research sessions are stored in-memory (`sessions: dict[str, dict]`). Each session holds a reference to the compiled graph instance, LangGraph config, and topic. Sessions are created on `/api/start` and consumed (popped) on `/api/continue`.

---

## Graph Workflow Design

```
START → clarify → research → write_report → save_report → END
            │
            └─── interrupt() ←── human answers ──→ resume
```

### Node Details

**1. Clarify Node**
- Prompts the LLM to generate 3–5 topic-specific clarifying questions
- Calls `interrupt(questions)` to pause and return questions to the caller
- On resume, stores user answers in `state.clarifications`

**2. Research Node**
- Constructs a search query from topic + clarifications
- Executes `DDGS().text(query, max_results=10)` for web search
- Extracts title, URL, and body snippet from each result
- Feeds all 10 results to the LLM with a synthesis prompt
- Returns structured research notes with source references

**3. Write Report Node**
- Takes research notes and user requirements
- Prompts the LLM to produce a structured Markdown report
- Required sections: title, executive summary, main sections, key takeaways, sources

**4. Save Report Node**
- Creates `reports/` directory if needed
- Sanitizes topic into a filesystem-safe filename (lowercase, underscores, max 80 chars)
- Writes the Markdown report to disk

### Checkpointing

The graph uses `InMemorySaver` as its checkpointer. This enables:
- **Interrupt/Resume**: Graph state persists across the `interrupt()` boundary
- **Thread Isolation**: Each research session uses a unique `thread_id` for independent state

---

## API Reference

### `POST /api/start`

Initiates a new research session. Runs the graph until the clarify interrupt.

**Request:**
```json
{
  "topic": "AI in healthcare"
}
```

**Response:**
```json
{
  "session_id": "uuid-v4",
  "questions": "1. What scope do you want?\n2. Who is the target audience?..."
}
```

### `POST /api/continue`

Resumes the graph with user answers. Returns an SSE stream.

**Request:**
```json
{
  "session_id": "uuid-v4",
  "answers": "Focus on diagnostics. Technical audience. 1000 words."
}
```

**Response (SSE stream):**
```
data: {"step": "research", "message": "Searching with DuckDuckGo + Ollama..."}
data: {"step": "research_done", "message": "Research complete (10 sources found)"}
data: {"step": "write_report", "message": "Writing report..."}
data: {"step": "report_done", "message": "Report drafted"}
data: {"step": "saved", "message": "Report saved to: reports/ai_in_healthcare.md"}
data: {"step": "done", "report": "# AI in Healthcare...", "report_path": "reports/ai_in_healthcare.md", "research_id": "uuid-v4"}
```

### `GET /api/history`

Returns all past research records.

**Response:**
```json
[
  { "id": "uuid", "topic": "AI in healthcare", "created_at": "2026-04-12T..." }
]
```

### `GET /api/history/<id>`

Returns a single research record with full report content.

### `GET /api/reports/<filename>`

Downloads a saved Markdown report file.

---

## Frontend Architecture

The web UI is a single-page application with four states managed by JavaScript:

| State | Section | Trigger |
|-------|---------|---------|
| **Input** | Topic text field + Start button | Page load, "New Research" |
| **Questions** | Rendered Markdown questions + answer textarea | Successful `/api/start` response |
| **Progress** | Three-step progress indicator with icons (⏳/🔄/✅) | Answer submission |
| **Report** | Rendered Markdown report + download button | SSE `done` event |

**Key Features:**
- **SSE Streaming**: `ReadableStream` reader processes server-sent events in real time
- **Markdown Rendering**: `marked.js` converts LLM-generated Markdown to HTML
- **History Sidebar**: Dark sidebar listing all past researches, clickable to reload
- **XSS Protection**: `escapeHtml()` sanitizes user-generated content before DOM insertion

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- A pulled model (default: `llama3.2:3b`)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/genai_bootcamp_udemy.git
cd genai_bootcamp_udemy

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Pull the Ollama model
ollama pull llama3.2:3b

# 4a. Run the CLI version
python research_agent.py

# 4b. Run the Web version
python web_app/app.py
# Open http://localhost:5000
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model name. Set via environment variable to use a different model (e.g., `llama3.1:8b`, `mistral`) |
| `DATABASE_URL` | `sqlite:///research_agent.db` | SQLAlchemy connection string. Supports any SQLAlchemy-compatible backend |

---

## Project Structure

```
genai_bootcamp_udemy/
├── graph.py                  # LangGraph workflow definition (core engine)
├── db.py                     # SQLAlchemy models and database helpers
├── research_agent.py         # CLI interface
├── requirements.txt          # Python dependencies
├── research_agent.db         # SQLite database (auto-created)
├── reports/                  # Generated Markdown reports
│   └── ai_in_education.md
├── web_app/
│   ├── app.py               # Flask server with REST API + SSE
│   ├── templates/
│   │   └── index.html        # Single-page web UI
│   └── static/
│       └── style.css         # UI styles
└── docs/
    ├── TECHNICAL_DOCUMENTATION.md   # This file
    └── BUSINESS_REPORT.md           # Business perspective report
```

---

## Design Decisions & Trade-offs

### 1. Local LLM (Ollama) vs. Cloud API

**Decision:** Use Ollama with locally-running models instead of cloud APIs (OpenAI, Gemini).

| Factor | Local (Ollama) | Cloud API |
|--------|---------------|-----------|
| Cost | Free | Pay-per-token |
| Privacy | Data stays local | Data sent to third party |
| Latency | Higher (CPU inference) | Lower (GPU clusters) |
| Quality | Good (3B model) | Better (larger models) |
| Availability | Always available | Rate limits, outages |

**Rationale:** Zero cost, zero rate limits, complete data privacy. Acceptable trade-off for a research tool where response time is secondary to output quality.

### 2. DuckDuckGo vs. Google Search API

**Decision:** DuckDuckGo Search (free, no API key) over Google Custom Search API (paid, requires setup).

**Rationale:** Eliminates API key management and costs. DuckDuckGo provides sufficient search quality for research synthesis tasks.

### 3. LangGraph interrupt() vs. Polling

**Decision:** Use LangGraph's native `interrupt()`/`Command(resume=)` pattern for human-in-the-loop.

**Rationale:** Clean separation of concerns. The graph defines *when* human input is needed; the caller defines *how* to collect it (CLI `input()` or web form). Same graph works for both interfaces.

### 4. In-Memory Checkpointer vs. Persistent

**Decision:** `InMemorySaver` instead of a persistent checkpointer.

**Rationale:** Research sessions are short-lived (minutes). In-memory is simpler and sufficient. If the server restarts, incomplete sessions are lost — acceptable for this use case.

### 5. SSE vs. WebSocket

**Decision:** Server-Sent Events for progress streaming.

**Rationale:** Unidirectional (server → client) is sufficient. SSE is simpler than WebSocket, works through proxies, and auto-reconnects. No need for bidirectional communication during the research phase.

---

## Future Improvements

- **Persistent Checkpointer**: Use `SqliteSaver` to survive server restarts
- **Multi-step Research**: Allow iterative refinement — user can request changes to the draft
- **PDF Export**: Generate PDF reports alongside Markdown
- **Concurrent Research**: Support multiple parallel research sessions per user
- **Model Selection UI**: Let users pick the Ollama model from the web interface
- **Source Verification**: Cross-reference claims across multiple sources for accuracy
- **GPU Acceleration**: Ollama with CUDA for significantly faster inference
