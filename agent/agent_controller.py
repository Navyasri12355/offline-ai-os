"""
agent_controller.py — Core agent logic using direct Ollama API calls.
Student 1 owns this file.

This is the main entry point called by server.py at:
    POST /chat  →  run_agent(message) -> AgentResponse

Returns:
    {
        "reply":      str,
        "logs":       list[str],
        "file_ready": bool,
        "file_path":  str | None,
    }
"""

import sys
import os
import re
import time
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.llm_config import check_ollama_running, MODEL_NAME, OLLAMA_BASE_URL
from agent.tools.file_tools import create_file, read_file, list_files
from agent.tools.folder_tools import organize_folder, list_pdfs, get_folder_summary
from agent.tools.pptx_generator import generate_ppt
from agent.tools.python_runner import run_script

# Execution log — appended during agent run, returned in response
_execution_logs: list[str] = []


def _log(msg: str):
    print(f"[AGENT] {msg}")
    _execution_logs.append(msg)


SYSTEM_PROMPT = """You are an offline AI assistant running entirely on the user's local machine.
You have access to tools that let you read files, write files, organize folders, and create presentations.

When the user asks you to do something:
1. Break the task into small steps.
2. Use the right tools in sequence.
3. Always confirm what you did at the end.

Rules:
- Never access the internet.
- Never delete files unless explicitly asked.
- When generating presentations, use clear headings and concise bullet points.
"""


def _call_ollama(prompt: str) -> tuple[str, float]:
    """
    Send a prompt to Ollama and return (response_text, elapsed_seconds).
    """
    start = time.time()
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
        },
        timeout=300,
    )
    response.raise_for_status()
    text = response.json().get("response", "").strip()
    elapsed = round(time.time() - start, 2)
    return text, elapsed


def _load_sample_docs() -> str:
    """
    Read all files from demo/sample_docs and return combined text.
    Used whenever user references 'my research', 'my paper', 'my documents' etc.
    """
    demo_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "demo", "sample_docs")
    )
    file_list = list_files(demo_dir)
    combined = ""
    for fpath in file_list.get("files", []):
        r = read_file(fpath)
        if r["success"] and r["content"]:
            combined += f"\n\n--- {os.path.basename(fpath)} ---\n{r['content']}"
            _log(f"Loaded: {os.path.basename(fpath)}")
    return combined.strip()


def _references_local_docs(message: str) -> bool:
    """Return True if the message refers to the user's own documents."""
    triggers = [
        "my research", "my paper", "my document", "my file",
        "my folder", "my docs", "my pdf", "the paper", "the document",
        "the research", "from my", "about my", "based on my"
    ]
    msg = message.lower()
    return any(t in msg for t in triggers)


def _detect_intent(message: str) -> str:
    """
    Detect what the user wants to do based on keywords.
    Returns one of: "ppt", "summarize_and_ppt", "organize", "list", "read",
                    "create_file", "run_script", "chat"
    """
    msg = message.lower()
    words = set(re.findall(r'\b\w+\b', msg))

    def has_any(*phrases):
        return any(p in msg for p in phrases)

    def has_any_word(*kws):
        return any(k in words for k in kws)

    # ── PPT / Presentation ────────────────────────────────────────────────
    if has_any("presentation", "powerpoint") or has_any_word("ppt", "slides", "slide"):
        if has_any("summarize", "summary", "research folder", "my folder",
                   "my documents", "my files", "from folder", "from docs"):
            return "summarize_and_ppt"
        return "ppt"

    # ── Summarize + PPT (without explicit PPT mention) ────────────────────
    if has_any_word("summarize", "summarise") and has_any(
        "folder", "documents", "docs", "research", "files"
    ):
        return "summarize_and_ppt"

    # ── Organize folder ───────────────────────────────────────────────────
    if has_any_word("organize", "organise", "sort", "arrange", "tidy"):
        return "organize"

    # ── List files ────────────────────────────────────────────────────────
    if has_any("what files", "show files", "list files", "list all files",
               "what's in", "what is in", "show me the files"):
        return "list"
    if has_any_word("list") and has_any_word("files", "folder", "directory", "docs"):
        return "list"

    # ── Read file ─────────────────────────────────────────────────────────
    if has_any("read the file", "open the file", "show me the file",
               "contents of", "what does", "what's in the file"):
        return "read"

    # ── Create / write file ───────────────────────────────────────────────
    if has_any_word("create", "make", "write", "generate", "save") and \
       has_any_word("file", "txt", "document", "doc"):
        return "create_file"

    # ── Run script ────────────────────────────────────────────────────────
    if has_any("run script", "execute script", "run python", "run the script"):
        return "run_script"

    # ── Default: plain chat ───────────────────────────────────────────────
    return "chat"


def _handle_summarize_and_ppt(message: str, memory_context: str) -> dict:
    """Read demo docs, summarize via Ollama, generate a PPT."""

    # 1. Find documents
    demo_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "demo", "sample_docs")
    )
    _log(f"Scanning folder: {demo_dir}")

    result = list_files(demo_dir)
    files = result.get("files", [])
    _log(f"Found {len(files)} files.")

    # 2. Read each file
    combined_text = ""
    max_chars_per_file = 1500 // max(len(files), 1)
    for fpath in files:
        r = read_file(fpath)
        if r["success"] and r["content"]:
            snippet = r["content"][:max_chars_per_file]
            combined_text += f"\n\n--- {os.path.basename(fpath)} ---\n{snippet}"
            _log(f"Read: {os.path.basename(fpath)} ({len(snippet)} chars)")

    if not combined_text and memory_context:
        combined_text = memory_context
        _log("Using memory context as document source.")

    if not combined_text:
        _log("No documents found to summarize.")
        return {
            "reply": "No documents found in the demo/sample_docs folder.",
            "logs": list(_execution_logs),
            "file_ready": False,
            "file_path": None,
        }

    # 3. Ask Ollama to summarize + generate slide content
    _log("Sending documents to Ollama for summarization...")
    summary_prompt = f"""You are summarizing research documents for a presentation.

Documents:
{combined_text[:3000]}

Generate an outline for a 4-slide presentation with this exact format:
Title: <presentation title>
Slide 1 Heading: <heading>
Slide 1 Bullets: <bullet1> | <bullet2> | <bullet3>
Slide 2 Heading: <heading>
Slide 2 Bullets: <bullet1> | <bullet2> | <bullet3>
Slide 3 Heading: <heading>
Slide 3 Bullets: <bullet1> | <bullet2> | <bullet3>
Slide 4 Heading: <heading>
Slide 4 Bullets: <bullet1> | <bullet2> | <bullet3>

Be concise. Each bullet should be one short sentence. Output only the outline, nothing else."""

    llm_output, elapsed = _call_ollama(summary_prompt)
    _log(f"Ollama responded in {elapsed}s")

    # 4. Parse LLM output into slides
    slides = _parse_slide_outline(llm_output)
    title = _extract_title(llm_output) or "Research Summary"
    _log(f"Parsed {len(slides)} slides.")

    # 5. Generate the PPT
    _log("Generating presentation...")
    ppt_result = generate_ppt(
        title=title,
        subtitle="Generated offline · AMD Ryzen · ONNX Runtime",
        slides=slides,
    )

    if ppt_result["success"]:
        _log(f"PPT saved: {ppt_result['path']}")
        return {
            "reply": f"Done! Summarized {len(files)} document(s) and created a {len(slides)}-slide presentation.",
            "logs": list(_execution_logs),
            "file_ready": True,
            "file_path": ppt_result["path"],
        }
    else:
        _log(f"PPT generation failed: {ppt_result['message']}")
        return {
            "reply": f"Summarization complete but PPT generation failed: {ppt_result['message']}",
            "logs": list(_execution_logs),
            "file_ready": False,
            "file_path": None,
        }


def _parse_slide_outline(text: str) -> list[dict]:
    """Parse the LLM's slide outline into a list of slide dicts."""
    slides = []
    lines = text.split("\n")

    current_heading = None
    for line in lines:
        line = line.strip()
        if "Heading:" in line:
            current_heading = line.split("Heading:")[-1].strip()
        elif "Bullets:" in line and current_heading:
            raw_bullets = line.split("Bullets:")[-1].strip()
            bullets = [b.strip() for b in raw_bullets.split("|") if b.strip()]
            if not bullets:
                bullets = [raw_bullets]
            slides.append({"heading": current_heading, "bullets": bullets})
            current_heading = None

    # Fallback if parsing fails
    if not slides:
        slides = [{"heading": "Summary", "bullets": [text[:200]]}]

    return slides


def _extract_title(text: str) -> str | None:
    """Extract the title line from LLM output."""
    for line in text.split("\n"):
        if line.strip().startswith("Title:"):
            return line.split("Title:")[-1].strip()
    return None


def run_agent(message: str, memory_context: str = "") -> dict:
    """
    Main agent entry point.

    Args:
        message:        The user's input message.
        memory_context: Optional RAG context from Student 2's memory_api.

    Returns:
        {
            "reply":      str,
            "logs":       list[str],
            "file_ready": bool,
            "file_path":  str | None,
        }
    """
    global _execution_logs
    _execution_logs = []

    if not check_ollama_running():
        return {
            "reply": "Ollama is not running. Please start it with: ollama serve",
            "logs": ["Ollama connection failed."],
            "file_ready": False,
            "file_path": None,
        }

    try:
        intent = _detect_intent(message)
        _log(f"Intent detected: {intent}")

        # ── Summarize documents + generate PPT (main demo flow) ───────────
        if intent == "summarize_and_ppt":
            return _handle_summarize_and_ppt(message, memory_context)

        # ── Generate PPT from direct request ──────────────────────────────
        if intent == "ppt":
            _log("Generating presentation from user request...")
            # If user references their docs, load them as context
            doc_context = _load_sample_docs() if _references_local_docs(message) else ""
            prompt = f"Context from documents:\n{doc_context[:1500]}\n\nRequest: {message}" \
                     if doc_context else message
            reply, elapsed = _call_ollama(prompt)
            _log(f"Ollama responded in {elapsed}s")
            ppt_result = generate_ppt(
                title="AI Generated Presentation",
                slides=[{"heading": "Key Points", "bullets": reply.split(". ")[:5]}],
            )
            file_path = ppt_result["path"] if ppt_result["success"] else None
            if file_path:
                _log(f"PPT saved: {file_path}")
            return {
                "reply": reply,
                "logs": list(_execution_logs),
                "file_ready": file_path is not None,
                "file_path": file_path,
            }

        # ── Organize folder ────────────────────────────────────────────────
        if intent == "organize":
            demo_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "demo", "sample_docs")
            )
            _log(f"Organizing folder: {demo_dir}")
            result = organize_folder(demo_dir)
            _log(result["message"])
            return {
                "reply": result["message"],
                "logs": list(_execution_logs),
                "file_ready": False,
                "file_path": None,
            }

        # ── List files ─────────────────────────────────────────────────────
        if intent == "list":
            demo_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "demo", "sample_docs")
            )
            _log(f"Listing files in: {demo_dir}")
            result = list_files(demo_dir)
            files = [os.path.basename(f) for f in result.get("files", [])]
            reply = f"Found {len(files)} files: {', '.join(files)}" if files else "No files found."
            _log(reply)
            return {
                "reply": reply,
                "logs": list(_execution_logs),
                "file_ready": False,
                "file_path": None,
            }

        # ── Create file ────────────────────────────────────────────────────
        if intent == "create_file":
            # Extract filename
            words = message.split()
            fname = next(
                (w.strip('"\',') for w in words if "." in w and not w.startswith("http")),
                "output.txt"
            )

            # 1. Try to extract inline content from the message first
            content = ""
            for marker in ["with the content", "with content", "containing",
                           "saying", "with text", "that says"]:
                if marker in message.lower():
                    content = message.split(marker, 1)[-1].strip().strip('"\'')
                    break

            if content:
                _log("Content extracted from message — skipping Ollama.")
            else:
                # 2. Check if user is referring to their local documents
                doc_context = ""
                if _references_local_docs(message):
                    _log("User referenced local documents — loading sample_docs...")
                    doc_context = _load_sample_docs()

                # 3. Call Ollama with or without document context
                if doc_context:
                    _log("Asking Ollama with document context...")
                    content_prompt = (
                        f"Using only the following document as context:\n\n"
                        f"{doc_context[:2000]}\n\n"
                        f"Write the contents for a file called '{fname}'.\n"
                        f"Request: {message}\n\n"
                        f"Respond with ONLY the raw file text. "
                        f"No explanations, no steps, no markdown, no code blocks. "
                        f"Just the plain text that should go inside the file."
                    )
                else:
                    _log("Asking Ollama...")
                    content_prompt = (
                        f"Write the contents for a file called '{fname}'.\n"
                        f"Request: {message}\n\n"
                        f"Respond with ONLY the raw file text. "
                        f"No explanations, no steps, no markdown, no code blocks. "
                        f"Just the plain text that should go inside the file."
                    )

                content, elapsed = _call_ollama(content_prompt)
                _log(f"Ollama responded in {elapsed}s")

            out_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "demo", "outputs", fname)
            )
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            result = create_file(out_path, content)
            _log(result["message"])
            return {
                "reply": f"Created '{fname}' with content: \"{content[:80]}\"",
                "logs": list(_execution_logs),
                "file_ready": False,
                "file_path": None,
            }

        # ── Run script ─────────────────────────────────────────────────────
        if intent == "run_script":
            words = message.split()
            script = next((w for w in words if w.endswith(".py")), None)
            if not script:
                return {
                    "reply": "Please specify a .py script to run.",
                    "logs": list(_execution_logs),
                    "file_ready": False,
                    "file_path": None,
                }
            result = run_script(script)
            _log(result["message"])
            return {
                "reply": result["stdout"] or result["message"],
                "logs": list(_execution_logs),
                "file_ready": False,
                "file_path": None,
            }

        # ── Default: plain chat with Ollama ────────────────────────────────
        _log(f"Sending to Ollama: {message[:80]}...")
        # Inject document context if user references their files
        if _references_local_docs(message):
            _log("Loading local docs for chat context...")
            doc_context = _load_sample_docs()
            prompt = (
                f"Context from the user's local documents:\n{doc_context[:2000]}\n\n"
                f"User: {message}"
            )
        elif memory_context:
            prompt = f"[Context]\n{memory_context}\n\n[User]\n{message}"
        else:
            prompt = message

        reply, elapsed = _call_ollama(prompt)
        _log(f"Ollama responded in {elapsed}s")

        return {
            "reply": reply,
            "logs": list(_execution_logs),
            "file_ready": False,
            "file_path": None,
        }

    except requests.exceptions.Timeout:
        _log("Ollama request timed out.")
        return {
            "reply": "Request timed out. The model may be loading — try again in a moment.",
            "logs": list(_execution_logs),
            "file_ready": False,
            "file_path": None,
        }
    except Exception as e:
        _log(f"Agent error: {e}")
        return {
            "reply": f"Agent encountered an error: {str(e)}",
            "logs": list(_execution_logs),
            "file_ready": False,
            "file_path": None,
        }


# ── CLI test harness ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_msg = input("Enter a command to test the agent:\n> ").strip()
    result = run_agent(test_msg)
    print("\n── Agent Response ──")
    print(f"Reply:      {result['reply']}")
    print(f"File ready: {result['file_ready']} → {result['file_path']}")
    print("Logs:")
    for log in result["logs"]:
        print(f"  {log}")