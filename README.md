# 🏆 Offline AI OS — Improved README

**Privacy-First Local AI System | AMD Ryzen Optimized**

---

## 🚀 Quick overview

Offline AI OS runs fully locally (no cloud) and is optimized for AMD Ryzen CPUs using ONNX Runtime. It provides a local LLM interface (Ollama), an ONNX-based embedding + memory layer, document indexing (RAG), and a small tool-using agent with file/PPT and Python execution capabilities.

---

## 🏗️ System architecture (visual)

```mermaid
flowchart LR
  Browser[Browser UI (app.html)] -->|HTTP/WebSocket| Backend[FastAPI Backend (server.py)]
  Backend --> LLM[Local LLM (Ollama)]
  Backend --> Tools[Tool Execution Layer]
  Backend --> Memory[Memory Layer (ONNX + ChromaDB)]
  Memory --> ONNX[ONNX Embedding Model (ONNX Runtime)]
  Tools -->|file ops / exec| PythonRunner[python_runner.py]
  Tools --> PPT[pptx_generator.py]
  Tools --> FileTools[file_tools.py]
  classDef infra fill:#f9f,stroke:#333,stroke-width:1px
  class Backend,LLM,Tools,Memory,ONNX,PythonRunner,PPT,FileTools infra
```

---

## 📁 Project structure (root-level)

```
offline-ai-os/
├── agent/
│   ├── tools/
│   │   ├── file_tools.py
│   │   ├── folder_tools.py
│   │   ├── pptx_generator.py
│   │   └── python_runner.py
│   ├── agent_controller.py
│   ├── llm_config.py
│   └── tool_manager.py
├── memory/
│   ├── models/
│   ├── benchmark.py
│   ├── chroma_store.py
│   ├── document_ingester.py
│   ├── memory_api.py
│   ├── ollama_llm.py
│   └── onnx_embedder.py
├── demo/
│   └── sample_docs/
├── app.html
├── requirements.txt
├── server.py
└── .gitignore
```

---

## ⚙️ Installation & setup (concise)

1. Clone:

```bash
git clone <your-repo-url>
cd offline-ai-os
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install & run Ollama (example):

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3
ollama serve
```

4. Export ONNX embedding model (example):

```bash
optimum-cli export onnx --model sentence-transformers/all-MiniLM-L6-v2 memory/models/
```

5. Start backend:

```bash
uvicorn main:app --reload
# or
python server.py
```

Open the UI: `http://localhost:8000` (or where your `app.html` points)

---

## 🧪 Running the benchmark

```bash
python memory/benchmark.py
```

Expect example output such as: `Inference: 12.4ms on AMD Ryzen CPU`.

---

## 🎬 Demo flow (UI)

1. Open UI at `localhost:8000`.
2. Enter: "Summarize my research folder and create a presentation."
3. Watch execution logs in real time.
4. Confirm "N documents indexed" memory indicator.
5. Download generated PPTX.

---

## 🔐 Why Offline AI?

* Full privacy
* No API costs
* Works offline
* Secure document handling

---

## 📜 License

MIT License
