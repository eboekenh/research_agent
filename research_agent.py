import uuid

from dotenv import load_dotenv
from langgraph.types import Command

from db import init_db, save_research
from graph import build_graph

load_dotenv()


def cli_progress(step: str, message: str):
    icons = {
        "clarify": "📋 Before I research, a few clarifying questions:\n",
        "research": "🌐 ",
        "research_done": "✅ ",
        "write_report": "✍️  ",
        "report_done": "✍️  ",
        "saved": "💾 ",
    }
    print(f"\n{icons.get(step, '')}{message}")


def main():
    print("=" * 60)
    print("  📚 Research Report Agent (Ollama + DuckDuckGo)")
    print("=" * 60)

    init_db()
    graph = build_graph(on_progress=cli_progress)

    topic = input("\nEnter a topic to research: ").strip()
    if not topic:
        print("No topic provided. Exiting.")
        return

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "topic": topic,
        "clarifications": "",
        "research_notes": "",
        "sources": [],
        "report": "",
        "report_path": "",
    }
    graph.invoke(initial_state, config)

    print("\nAnswer the questions above (type your answers, then press Enter):\n")
    answers = input("> ").strip()

    result = graph.invoke(Command(resume=answers), config)

    # Save to database
    save_research(
        topic=result["topic"],
        clarifications=result["clarifications"],
        report=result["report"],
        report_path=result["report_path"],
        sources=result.get("sources", []),
    )

    print("\n" + "=" * 60)
    print(f"  ✅ Done! Report saved to: {result['report_path']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
