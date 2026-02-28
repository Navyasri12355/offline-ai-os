# 🏆 Offline AI OS — AMD Ryzen Powered
> 24-Hour Hackathon Build | 3-Person Team

---

## 📁 Project Folder Structure

```
offline-ai-os/
│
├── README.md
├── requirements.txt                  # All Python dependencies (shared)
├── .env.example                      # Environment variable template
│
├── student1_agent/                   # 🧑‍💻 Student 1: Brain & Hands
│   ├── README_S1.md
│   ├── llm_config.py                 # Ollama model config & connection
│   ├── agent_controller.py           # Open Interpreter setup + local mode
│   ├── tool_manager.py               # Wrapper for all callable tools
│   └── tools/
│       ├── file_tools.py             # create/read/write files
│       ├── folder_tools.py           # list/organize folders
│       ├── pptx_generator.py         # generate .pptx via python-pptx
│       └── python_runner.py          # safe subprocess executor
│
├── student2_memory/                  # 💽 Student 2: Memory & AMD Layer
│   ├── README_S2.md
│   ├── onnx_embedder.py              # ONNX Runtime embedding inference
│   ├── chroma_store.py               # ChromaDB init, insert, query
│   ├── document_ingester.py          # PDF/TXT chunking + indexing pipeline
│   ├── memory_api.py                 # Exportable: search_memory(query) -> str
│   ├── benchmark.py                  # AMD CPU inference benchmarking script
│   └── models/
│       └── .gitkeep                  # Place ONNX model files here (not committed)
│
├── student3_ui/                      # 🎨 Student 3: Face & Flow
│   ├── README_S3.md
│   ├── main.py                       # FastAPI app entry point
│   ├── routes/
│   │   ├── chat.py                   # POST /chat endpoint
│   │   ├── memory.py                 # GET /memory/status endpoint
│   │   └── files.py                  # GET /files/download endpoint
│   ├── static/
│   │   ├── index.html                # Main UI shell
│   │   ├── style.css                 # Dashboard styling
│   │   └── app.js                    # Chat + log rendering logic
│   └── mock_responses.py             # Dummy AI responses for UI dev (Phase 1)
│
├── demo/
│   ├── sample_docs/                  # PDFs/TXTs used in live demo
│   │   ├── research_paper_1.pdf
│   │   └── research_notes.txt
│   └── generate_summary_ppt.py       # 🔥 Hardcoded fallback script for demo
│
└── shared/
    ├── schemas.py                    # Shared Pydantic models / JSON formats
    └── logger.py                     # Shared logging utility
```

---

## 👥 Work Division

### 🧑‍💻 Student 1 — `student1_agent/`
**Role: Brain & Hands (Agent + LLM Engineer)**

| File | What to build |
|------|---------------|
| `llm_config.py` | Connect to local Ollama instance (phi3 / llama3) |
| `agent_controller.py` | Set up Open Interpreter in `--local` mode, route to Ollama via LiteLLM |
| `tool_manager.py` | Register all tool functions so the agent can call them |
| `tools/file_tools.py` | `create_file()`, `read_file()`, `list_files()` |
| `tools/folder_tools.py` | `organize_folder()`, `list_pdfs()` |
| `tools/pptx_generator.py` | `generate_ppt(title, bullets[])` using python-pptx |
| `tools/python_runner.py` | `run_script(path)` — safe subprocess wrapper |

**Hour 8 milestone:** Type a command → local LLM writes + executes Python → file appears on disk.

---

### 💽 Student 2 — `student2_memory/`
**Role: Memory & AMD Layer (RAG + ONNX Engineer)**

| File | What to build |
|------|---------------|
| `onnx_embedder.py` | Load pre-converted ONNX model, run `CPUExecutionProvider`, return embeddings |
| `chroma_store.py` | Init ChromaDB, `add_documents()`, `query_documents()` |
| `document_ingester.py` | Walk a folder → chunk text → embed via ONNX → store in Chroma |
| `memory_api.py` | Clean exportable function: `search_memory(query: str) -> str` |
| `benchmark.py` | Time ONNX inference, print: `"Inference: Xms on AMD Ryzen CPU"` |

**Hour 8 milestone:** Run `python memory_api.py` → query demo folder → correct chunks returned using pure ONNX CPU execution.

> **Tip:** Download pre-converted ONNX embedding model from HuggingFace:
> `optimum-cli export onnx --model sentence-transformers/all-MiniLM-L6-v2 models/`

---

### 🎨 Student 3 — `student3_ui/`
**Role: Face & Flow (UI + Integration Lead)**

| File | What to build |
|------|---------------|
| `main.py` | FastAPI server, import routes, serve static files |
| `routes/chat.py` | `POST /chat` → calls agent (or mock in Phase 1) |
| `routes/memory.py` | `GET /memory/status` → returns doc count from ChromaDB |
| `routes/files.py` | `GET /files/download` → serves generated PPT file |
| `static/index.html` | Chat window + Execution Log sidebar + Memory indicator |
| `static/app.js` | Fetch API calls, stream log messages, handle file download button |
| `mock_responses.py` | Hardcoded fake responses so UI works before AI is ready |

**Hour 8 milestone:** UI running at `localhost:8000`, chat sends messages, log sidebar shows mock output, memory indicator shows "0 docs indexed."

---

## ⏱️ 24-Hour Timeline

| Phase | Hours | Who | Goal |
|-------|-------|-----|------|
| **Setup** | 0–1 | All | Clone repo, install dependencies, agree on JSON schemas in `shared/schemas.py` |
| **Siloed Dev** | 1–8 | Separate | Each hits their Hour 8 milestone independently |
| **Integration** | 8–14 | S3 leads | Wire S1 agent + S2 memory into FastAPI; full flow in UI |
| **Demo Hardening** | 14–18 | All | Nail the demo scenario end-to-end; add PPT download button |
| **Polish + Pitch** | 18–22 | S1+S2 debug, S3 slides | Run benchmarks; build pitch deck |
| **Rehearsal** | 22–24 | All | Practice demo 10x. No new code. |

---

## 🔗 Integration Contract
> Agreed in **Hour 0** — do not change without telling the team.

**Chat request (UI → Backend):**
```json
{ "message": "Summarize my research folder and create a presentation." }
```

**Chat response (Backend → UI):**
```json
{
  "reply": "Done! I summarized 3 documents and created a presentation.",
  "logs": ["Reading files...", "Querying memory...", "Generating PPT..."],
  "file_ready": true,
  "file_path": "output_summary.pptx"
}
```

---

## 📦 requirements.txt
```
ollama
open-interpreter
litellm
chromadb
onnxruntime
optimum[exporters]
sentence-transformers
fastapi
uvicorn
python-pptx
pypdf2
pydantic
```

---

## 🎯 Demo Script (Memorize This)

1. Open UI at `localhost:8000`
2. Type: *"Summarize my research folder and create a presentation."*
3. Show execution log filling up in real time
4. Show memory indicator: *"3 documents indexed"*
5. File download button appears → click → PPT opens
6. Say: *"All of this ran offline, on AMD Ryzen, using ONNX Runtime — zero cloud."*

---

## ⭐ AMD Judging Quote
> *"Our Offline AI OS performs all inference locally using ONNX Runtime optimized for AMD Ryzen processors, enabling privacy-preserving AI without cloud dependence."*

Run `student2_memory/benchmark.py` before the demo and screenshot the output.
