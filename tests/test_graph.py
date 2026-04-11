"""
Unit tests for the AI Research Agent graph module.

Run with:
    pytest tests/ -v
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# ResearchState tests
# ---------------------------------------------------------------------------

def test_research_state_fields():
    """ResearchState TypedDict should accept all expected fields."""
    from graph import ResearchState

    state: ResearchState = {
        "topic": "Quantum computing",
        "clarifications": "Focus on hardware advances",
        "research_notes": "Some notes here",
        "sources": [{"title": "Example", "url": "https://example.com", "snippet": "..."}],
        "report": "# Report\nContent here",
        "report_path": "reports/quantum_computing.md",
    }

    assert state["topic"] == "Quantum computing"
    assert isinstance(state["sources"], list)
    assert len(state["sources"]) == 1


# ---------------------------------------------------------------------------
# build_graph tests
# ---------------------------------------------------------------------------

def test_build_graph_returns_graph():
    """build_graph() should return a compiled LangGraph StateGraph."""
    from graph import build_graph

    graph = build_graph()
    assert graph is not None


def test_build_graph_accepts_progress_callback():
    """build_graph() should accept an optional on_progress callback."""
    from graph import build_graph

    callback = MagicMock()
    graph = build_graph(on_progress=callback)
    assert graph is not None


# ---------------------------------------------------------------------------
# db module tests
# ---------------------------------------------------------------------------

def test_init_db_creates_tables():
    """init_db() should run without errors and create the database tables."""
    import os
    from db import init_db

    # Use an in-memory / temp DB to avoid polluting the project DB
    with patch("db.DATABASE_URL", "sqlite:///test_temp.db"):
        init_db()

    # Clean up
    if os.path.exists("test_temp.db"):
        os.remove("test_temp.db")


def test_save_research_stores_record():
    """save_research() should persist a record that can be queried back."""
    import os
    from db import init_db, save_research, get_all_research

    with patch("db.DATABASE_URL", "sqlite:///test_save.db"):
        init_db()
        save_research(
            topic="Test Topic",
            clarifications="No clarifications",
            report="# Test Report",
            report_path="reports/test.md",
            sources=[{"title": "Src", "url": "https://src.com", "snippet": "..."}],
        )
        records = get_all_research()

    assert len(records) >= 1
    assert records[0]["topic"] == "Test Topic"

    if os.path.exists("test_save.db"):
        os.remove("test_save.db")


# ---------------------------------------------------------------------------
# CLI progress helper tests
# ---------------------------------------------------------------------------

def test_cli_progress_prints(capsys):
    """cli_progress() should print a message to stdout."""
    from research_agent import cli_progress

    cli_progress("research", "Searching the web...")
    captured = capsys.readouterr()
    assert "Searching the web..." in captured.out


def test_cli_progress_unknown_step(capsys):
    """cli_progress() should handle unknown step keys gracefully."""
    from research_agent import cli_progress

    cli_progress("unknown_step", "Some message")
    captured = capsys.readouterr()
    assert "Some message" in captured.out
