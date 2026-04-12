import json
import os
import sys
import uuid
from queue import Empty, Queue
from threading import Thread

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from langgraph.types import Command

# Allow imports from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import get_all_researches, get_research, init_db, save_research
from graph import build_graph

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

# In-memory store for active research sessions
sessions: dict[str, dict] = {}

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


# ── Routes ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_research():
    """Accept a topic, run the graph until the clarify interrupt, return questions."""
    data = request.get_json()
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    session_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Build a graph with no progress callback (we just need the questions)
    graph = build_graph()

    initial_state = {
        "topic": topic,
        "clarifications": "",
        "research_notes": "",
        "sources": [],
        "report": "",
        "report_path": "",
    }

    # This will run until the interrupt() in the clarify node
    result = graph.invoke(initial_state, config)

    # Extract the questions from the interrupt
    snapshot = graph.get_state(config)
    questions = ""
    if snapshot.tasks:
        for task in snapshot.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                questions = task.interrupts[0].value
                break

    # Store session for resumption
    sessions[session_id] = {
        "graph": graph,
        "config": config,
        "topic": topic,
    }

    return jsonify({
        "session_id": session_id,
        "questions": questions,
    })


@app.route("/api/continue", methods=["POST"])
def continue_research():
    """Resume the graph with user answers, stream progress via SSE."""
    data = request.get_json()
    session_id = data.get("session_id", "")
    answers = (data.get("answers") or "").strip()

    if session_id not in sessions:
        return jsonify({"error": "Session not found or expired"}), 404

    session = sessions.pop(session_id)
    graph_instance = session["graph"]
    config = session["config"]
    topic = session["topic"]

    progress_queue: Queue = Queue()

    def run_graph():
        try:
            # Build a new graph with progress callback that pushes to the queue
            def on_progress(step, message):
                progress_queue.put({"step": step, "message": message})

            # Rebuild graph with progress callback, reusing the same checkpointer
            graph_with_progress = build_graph(on_progress=on_progress)
            # Copy over the checkpoint state from the original graph
            graph_with_progress.checkpointer = graph_instance.checkpointer
            result = graph_with_progress.invoke(Command(resume=answers), config)

            # Save to DB
            research_id = save_research(
                topic=result["topic"],
                clarifications=result["clarifications"],
                report=result["report"],
                report_path=result["report_path"],
                sources=result.get("sources", []),
            )

            progress_queue.put({
                "step": "done",
                "report": result["report"],
                "report_path": result["report_path"],
                "research_id": research_id,
            })
        except Exception as e:
            progress_queue.put({"step": "error", "message": str(e)})

    # Start graph in background thread
    thread = Thread(target=run_graph, daemon=True)
    thread.start()

    def event_stream():
        # Send initial progress event
        yield f"data: {json.dumps({'step': 'research', 'message': 'Searching with DuckDuckGo + Ollama...'})}\n\n"

        while True:
            try:
                event = progress_queue.get(timeout=600)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("step") in ("done", "error"):
                    break
            except Empty:
                yield f"data: {json.dumps({'step': 'error', 'message': 'Timeout waiting for results (10 min)'})}\n\n"
                break

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/api/history")
def history():
    """Return list of all past researches."""
    return jsonify(get_all_researches())


@app.route("/api/history/<research_id>")
def history_detail(research_id):
    """Return a single research by ID."""
    result = get_research(research_id)
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@app.route("/api/reports/<filename>")
def download_report(filename):
    """Serve a saved .md report file for download."""
    return send_from_directory(
        os.path.abspath(REPORTS_DIR),
        filename,
        as_attachment=True,
        mimetype="text/markdown",
    )


if __name__ == "__main__":
    init_db()
    print("🚀 Research Agent Web App running at http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
