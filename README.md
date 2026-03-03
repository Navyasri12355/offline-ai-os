# 🏆 Offline AI OS --- AMD Ryzen Powered

Privacy-First Local AI System \| 24-Hour Hackathon Build

------------------------------------------------------------------------

## 🚀 Overview

Offline AI OS is a fully local, privacy-preserving AI operating system
that runs entirely on your machine --- powered by AMD Ryzen CPUs and
ONNX Runtime.

It combines:

-   🧠 A local LLM (via Ollama)
-   💽 High-performance ONNX-based embedding + memory layer
-   📚 Document indexing & retrieval (RAG)
-   🛠️ Tool-using AI agent (file creation, PPT generation, Python
    execution)
-   🎨 Web-based UI with real-time execution logs

All inference runs **offline**.\
No cloud APIs. No external calls. Zero data leakage.

------------------------------------------------------------------------

## 🏗️ System Architecture

User (Browser UI) │ ▼ FastAPI Backend │ ├── Local LLM (Ollama) ├── Tool
Execution Layer └── Memory Layer (ONNX + ChromaDB) │ ▼ AMD Ryzen CPU
(ONNX Runtime - CPUExecutionProvider)

------------------------------------------------------------------------

## 🧠 Core Capabilities

### 1️⃣ Local AI Agent

-   Runs through Ollama
-   Supports models like Phi-3 and Llama 3
-   Executes Python safely
-   Creates and edits files
-   Generates PowerPoint presentations automatically

### 2️⃣ ONNX Memory Layer (AMD Optimized)

-   Embeddings exported using Optimum
-   Inference runs on ONNX Runtime
-   Embedding model: sentence-transformers/all-MiniLM-L6-v2
-   Vector storage via ChromaDB
-   Uses CPUExecutionProvider for optimized AMD Ryzen execution

### 3️⃣ Retrieval-Augmented Generation (RAG)

-   Ingest PDFs and TXT documents
-   Chunk → Embed → Store
-   Query semantic memory locally
-   Pass retrieved context to LLM
-   Generate summaries and presentations

### 4️⃣ Tool Execution System

The AI agent can: - Create files - Read documents - Organize folders -
Generate .pptx files using python-pptx - Execute Python scripts safely -
Serve files for download

------------------------------------------------------------------------

## 📁 Project Structure

offline-ai-os/ │ ├── README.md ├── requirements.txt ├── .env.example │
├── agent/ ├── memory/ ├── routes/ ├── static/ ├── demo/ └── shared/

------------------------------------------------------------------------

## ⚙️ Installation

### 1️⃣ Clone the Repository

git clone `<your-repo-url>`{=html} cd offline-ai-os

### 2️⃣ Install Dependencies

pip install -r requirements.txt

### 3️⃣ Install & Run Ollama

curl -fsSL https://ollama.com/install.sh \| sh ollama pull phi3 ollama
serve

### 4️⃣ Export ONNX Embedding Model

optimum-cli export onnx --model sentence-transformers/all-MiniLM-L6-v2
memory/models/

### 5️⃣ Start Backend

uvicorn main:app --reload

Open: http://localhost:8000

------------------------------------------------------------------------

## 🧪 Running the Benchmark

python memory/benchmark.py

Example output:

Inference: 12.4ms on AMD Ryzen CPU

------------------------------------------------------------------------

## 🎬 Demo Flow

1.  Open UI at localhost:8000
2.  Type: "Summarize my research folder and create a presentation."
3.  Show execution logs
4.  Show memory indicator (e.g., "3 documents indexed")
5.  Download generated PPT
6.  Highlight that everything ran locally on AMD Ryzen using ONNX
    Runtime.

------------------------------------------------------------------------

## 🔐 Why Offline AI?

-   ✅ Full privacy
-   ✅ No API costs
-   ✅ Works without internet
-   ✅ Secure document handling

Perfect for research labs, healthcare, defense, and rural deployments.

------------------------------------------------------------------------

## 📜 License

MIT License
