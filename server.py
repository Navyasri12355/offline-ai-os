"""
Run with:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
Then open:
    http://localhost:8000
"""

import time
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.agent_controller import run_agent

# ── Try importing Student 2's memory (optional until Hour 14) ──────────────────
try:
    from memory.memory_api import search_memory, get_document_count
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    def search_memory(query: str) -> str:
        return ""
    def get_document_count() -> int:
        return 0

app = FastAPI()


# ── Serve app.html at root ─────────────────────────────────────────────────────
@app.get("/")
def serve_ui():
    return FileResponse("app.html")


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "memory_available": MEMORY_AVAILABLE}


# ── Memory status (Student 2's doc count) ─────────────────────────────────────
@app.get("/memory_status")
def memory_status():
    return {"documents_indexed": get_document_count()}


# ── Chat endpoint ──────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(req: ChatRequest):
    start = time.time()

    # Inject memory context if Student 2 is integrated
    memory_context = search_memory(req.message) if MEMORY_AVAILABLE else ""

    # Run the agent
    result = run_agent(message=req.message, memory_context=memory_context)

    elapsed_ms = round((time.time() - start) * 1000)

    return {
        "response":         result["reply"],
        "execution_log":    "\n".join(result["logs"]),
        "inference_time_ms": elapsed_ms,
        "file_ready":       result["file_ready"],
        "file_path":        result["file_path"],
    }


# ── File download ──────────────────────────────────────────────────────────────
@app.get("/download")
def download_file(path: str):
    if not path or not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=os.path.basename(path),
    )