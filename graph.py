import os
import re
import time
from typing import TypedDict

from duckduckgo_search import DDGS
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


# ── State ───────────────────────────────────────────────────────────────────────
class ResearchState(TypedDict):
    topic: str
    clarifications: str
    research_notes: str
    sources: list[dict]
    report: str
    report_path: str


# ── Retry helper ────────────────────────────────────────────────────────────────

def _invoke_with_retry(llm, prompt, max_retries=5, initial_wait=2):
    """Invoke LLM with exponential backoff on rate-limit (429) errors."""
    for attempt in range(max_retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = initial_wait * (2 ** attempt)
                print(f"⏳ Rate limited, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    return llm.invoke(prompt)


# ── Node factories ──────────────────────────────────────────────────────────────

def make_clarify_node(llm, on_progress=None):
    def clarify(state: ResearchState) -> dict:
        response = _invoke_with_retry(llm,
            f"""The user wants a research report on: "{state["topic"]}"

Before researching, generate 3-5 clarifying questions to understand:
- The scope and depth they want
- The target audience (technical, business, general public, etc.)
- Specific aspects or angles they care about
- Any constraints (time period, geography, industry, etc.)

Format the questions as a numbered list. Be concise and specific to the topic."""
        )

        questions = response.content
        if on_progress:
            on_progress("clarify", questions)

        answers = interrupt(questions)
        return {"clarifications": answers}

    return clarify


def make_research_node(llm, on_progress=None):
    def research(state: ResearchState) -> dict:
        if on_progress:
            on_progress("research", "Searching the web with DuckDuckGo...")

        # Step 1: Use DuckDuckGo to gather web results
        ddgs = DDGS()
        query = f"{state['topic']} {state['clarifications'][:100]}"
        search_results = ddgs.text(query, max_results=10)

        sources = []
        search_context = ""
        for i, r in enumerate(search_results, 1):
            url = r.get("href", "")
            title = r.get("title", "")
            body = r.get("body", "")
            sources.append({"url": url, "title": title})
            search_context += f"\n[{i}] {title}\nURL: {url}\n{body}\n"

        if on_progress:
            on_progress("research", f"Found {len(sources)} sources. Analyzing with LLM...")

        # Step 2: Have the LLM synthesize the search results
        response = _invoke_with_retry(llm,
            f"""You are a thorough research assistant. Analyze the following web search results
and create comprehensive research notes.

**Topic:** {state["topic"]}
**User requirements:** {state["clarifications"]}

**Web search results:**
{search_context}

Based on these search results, provide detailed research notes covering all relevant aspects.
Synthesize the information, identify key themes, extract specific facts, data, and statistics.
Reference the source numbers [1], [2], etc. when citing information."""
        )

        notes = response.content
        if sources:
            notes += "\n\n### Sources Found\n"
            for s in sources:
                notes += f"- [{s['title']}]({s['url']})\n"

        if on_progress:
            on_progress("research_done", f"Research complete ({len(sources)} sources found)")

        return {"research_notes": notes, "sources": sources}

    return research


def make_write_report_node(llm, on_progress=None):
    def write_report(state: ResearchState) -> dict:
        if on_progress:
            on_progress("write_report", "Writing report...")

        response = _invoke_with_retry(llm,
            f"""You are an expert research analyst. Write a comprehensive, well-structured
Markdown report based on the research below.

**Topic:** {state["topic"]}
**User requirements:** {state["clarifications"]}

**Research notes:**
{state["research_notes"]}

Your report MUST include:
1. A clear title (# heading)
2. An executive summary (2-3 paragraphs)
3. Multiple main sections (## headings) covering different aspects
4. Key takeaways / conclusions
5. A Sources section listing the URLs referenced

Write in a professional, clear style. Use bullet points, tables, or sub-headings
where they improve readability. Cite sources inline where relevant."""
        )

        if on_progress:
            on_progress("report_done", "Report drafted")

        return {"report": response.content}

    return write_report


def make_save_report_node(on_progress=None):
    def save_report(state: ResearchState) -> dict:
        os.makedirs("reports", exist_ok=True)

        safe_name = re.sub(r"[^\w\s-]", "", state["topic"].lower())
        safe_name = re.sub(r"[\s]+", "_", safe_name).strip("_")[:80]
        filepath = os.path.join("reports", f"{safe_name}.md")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["report"])

        if on_progress:
            on_progress("saved", f"Report saved to: {filepath}")

        return {"report_path": filepath}

    return save_report


# ── Build the Graph ─────────────────────────────────────────────────────────────

def build_graph(on_progress=None):
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.7)

    builder = StateGraph(ResearchState)

    builder.add_node("clarify", make_clarify_node(llm, on_progress))
    builder.add_node("research", make_research_node(llm, on_progress))
    builder.add_node("write_report", make_write_report_node(llm, on_progress))
    builder.add_node("save_report", make_save_report_node(on_progress))

    builder.add_edge(START, "clarify")
    builder.add_edge("clarify", "research")
    builder.add_edge("research", "write_report")
    builder.add_edge("write_report", "save_report")
    builder.add_edge("save_report", END)

    return builder.compile(checkpointer=InMemorySaver())
