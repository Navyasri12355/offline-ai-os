"""
agent_controller.py — Core agent logic using direct Ollama API calls.
Student 1 owns this file.

Entry point called by server.py:
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
    """Read all files from demo/sample_docs and return combined text."""
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
    triggers = [
        "my research", "my paper", "my document", "my file",
        "my folder", "my docs", "my pdf", "the paper", "the document",
        "the research", "from my", "about my", "based on my"
    ]
    return any(t in message.lower() for t in triggers)


def _detect_intent(message: str) -> str:
    msg = message.lower()
    words = set(re.findall(r'\b\w+\b', msg))

    def has_any(*phrases):
        return any(p in msg for p in phrases)

    def has_any_word(*kws):
        return any(k in words for k in kws)

    if has_any("presentation", "powerpoint") or has_any_word("ppt", "slides", "slide"):
        if has_any("summarize", "summary", "research folder", "my folder",
                   "my documents", "my files", "from folder", "from docs"):
            return "summarize_and_ppt"
        return "ppt"

    if has_any_word("summarize", "summarise") and has_any(
        "folder", "documents", "docs", "research", "files"
    ):
        return "summarize_and_ppt"

    if has_any_word("organize", "organise", "sort", "arrange", "tidy"):
        return "organize"

    if has_any("what files", "show files", "list files", "list all files",
               "what's in", "what is in", "show me the files"):
        return "list"
    if has_any_word("list") and has_any_word("files", "folder", "directory", "docs"):
        return "list"

    if has_any("read the file", "open the file", "show me the file",
               "contents of", "what does", "what's in the file"):
        return "read"

    if has_any_word("create", "make", "write", "generate", "save") and \
       has_any_word("file", "txt", "document", "doc"):
        return "create_file"

    if has_any("run script", "execute script", "run python", "run the script"):
        return "run_script"

    return "chat"


def _parse_slide_outline(text: str) -> list[dict]:
    """Parse LLM outline into slides. Pads slides with fewer than 4 bullets."""
    slides = []
    current_heading = None

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "Heading:" in line:
            current_heading = line.split("Heading:", 1)[-1].strip()
        elif "Bullets:" in line and current_heading:
            raw = line.split("Bullets:", 1)[-1].strip()
            bullets = [b.strip() for b in raw.split("|") if b.strip()]
            bullets = [b for b in bullets if len(b) > 5]

            # Pad to at least 4 if Ollama returned fewer
            while len(bullets) < 4:
                bullets.append("Refer to source document for additional details.")

            slides.append({"heading": current_heading, "bullets": bullets})
            current_heading = None

    if not slides:
        chunks = [text[i:i+150].strip() for i in range(0, min(len(text), 900), 150)]
        slides = [{"heading": "Summary", "bullets": [c for c in chunks if c]}]

    return slides


def _extract_title(text: str) -> str | None:
    for line in text.split("\n"):
        if line.strip().startswith("Title:"):
            return line.split("Title:", 1)[-1].strip()
    return None


def _build_prompt(combined_text: str, files: list[str]) -> str:
    """
    Build a fully dynamic prompt that scales to any number of source documents.
    - 1 doc  → 3 slides
    - 2 docs → 5 slides (2 per doc + 1 conclusion)
    - 3 docs → 7 slides (2 per doc + 1 conclusion)
    - N docs → (N*2 + 1) slides
    """
    doc_names = [os.path.basename(f) for f in files]
    slides_per_doc = 2
    total_content_slides = len(files) * slides_per_doc
    conclusion_slide = total_content_slides + 1

    # Build slide template
    slide_template = "\n".join(
        f"Slide {i} Heading: <heading>\n"
        f"Slide {i} Bullets: <bullet> | <bullet> | <bullet> | <bullet> | <bullet> | <bullet> | <bullet> | <bullet>"
        for i in range(1, conclusion_slide + 1)
    )

    # Build per-doc allocation instructions
    if len(files) == 1:
        doc_allocation = (
            f"- All slides 1-{total_content_slides} must cover content from: '{doc_names[0]}'\n"
            f"- Slide {conclusion_slide}: key takeaways and conclusions from the document"
        )
    else:
        allocation_lines = []
        slide_num = 1
        for i, name in enumerate(doc_names):
            end = slide_num + slides_per_doc - 1
            allocation_lines.append(
                f"- Slides {slide_num}-{end}: cover content specifically from '{name}'"
            )
            slide_num = end + 1
        allocation_lines.append(
            f"- Slide {conclusion_slide}: conclusions and comparisons drawn from ALL documents"
        )
        doc_allocation = "\n".join(allocation_lines)

    return f"""You are creating a detailed presentation from the following documents.

Documents:
{combined_text[:4000]}

IMPORTANT: Cover content from ALL documents above. Read them carefully before writing.

Output ONLY in this exact format — no extra text, no preamble, no explanations:

Title: <title based on all documents>
{slide_template}

STRICT RULES — failure to follow these will make the presentation useless:
- EVERY slide MUST have EXACTLY 8 bullets separated by the | character
- Count your bullets before outputting — if you have fewer than 8, add more facts from the document
- Each bullet MUST be a specific fact, finding, method, number, or result taken directly from the documents
- Each bullet should be 10-20 words — a full informative sentence, not a label or heading
- FORBIDDEN phrases: "refer to document", "see source", "novel concept", "performance achieved", "various methods" — these are too vague
- If a slide topic has fewer than 8 obvious points, expand on related context, implications, or supporting details from the documents
- Separate bullets with | only — never use newlines or commas between bullets
{doc_allocation}
- Do not repeat the same point across different slides
- Output ONLY the Title and Slide lines in the exact format shown above, nothing else"""


def _handle_summarize_and_ppt(message: str, memory_context: str) -> dict:
    """Single-pass generation. Scales to any number of source documents."""

    # 1. Find and read documents
    demo_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "demo", "sample_docs")
    )
    _log(f"Scanning folder: {demo_dir}")
    result = list_files(demo_dir)
    files = result.get("files", [])
    _log(f"Found {len(files)} files.")

    combined_text = ""
    max_chars_per_file = 4000 // max(len(files), 1)
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
        return {
            "reply": "No documents found in the demo/sample_docs folder.",
            "logs": list(_execution_logs),
            "file_ready": False,
            "file_path": None,
        }

    # 2. Build dynamic prompt and call Ollama
    prompt = _build_prompt(combined_text, files)
    _log(f"Generating presentation for {len(files)} document(s)...")
    llm_output, elapsed = _call_ollama(prompt)
    _log(f"Ollama responded in {elapsed}s")

    slides = _parse_slide_outline(llm_output)
    title = _extract_title(llm_output) or "Document Summary"
    total_bullets = sum(len(s["bullets"]) for s in slides)
    _log(f"Built {len(slides)} slides with {total_bullets} total bullets.")

    # 3. Generate PPT
    _log("Generating presentation...")
    ppt_result = generate_ppt(
        title=title,
        subtitle="Generated offline · AMD Ryzen · ONNX Runtime",
        slides=slides,
    )

    if ppt_result["success"]:
        _log(f"PPT saved: {ppt_result['path']}")
        return {
            "reply": f"Done! Created a {len(slides)}-slide presentation with {total_bullets} key points across {len(files)} document(s).",
            "logs": list(_execution_logs),
            "file_ready": True,
            "file_path": ppt_result["path"],
        }
    else:
        return {
            "reply": f"Summarization complete but PPT failed: {ppt_result['message']}",
            "logs": list(_execution_logs),
            "file_ready": False,
            "file_path": None,
        }


def run_agent(message: str, memory_context: str = "") -> dict:
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

        # ── Summarize docs + generate PPT ─────────────────────────────────
        if intent == "summarize_and_ppt":
            return _handle_summarize_and_ppt(message, memory_context)

        # ── PPT from direct request ────────────────────────────────────────
        if intent == "ppt":
            _log("Generating presentation from user request...")
            doc_context = _load_sample_docs() if _references_local_docs(message) else ""
            prompt = (
                f"Context from documents:\n{doc_context[:1500]}\n\nRequest: {message}"
                if doc_context else message
            )
            reply, elapsed = _call_ollama(prompt)
            _log(f"Ollama responded in {elapsed}s")
            ppt_result = generate_ppt(
                title="AI Generated Presentation",
                slides=[{"heading": "Key Points",
                         "bullets": [b.strip() for b in reply.split(".")
                                     if len(b.strip()) > 5][:8]}],
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
            words = message.split()
            fname = next(
                (w.strip('"\',') for w in words if "." in w and not w.startswith("http")),
                "output.txt"
            )

            content = ""
            for marker in ["with the content", "with content", "containing",
                           "saying", "with text", "that says"]:
                if marker in message.lower():
                    content = message.split(marker, 1)[-1].strip().strip('"\'')
                    break

            if content:
                _log("Content extracted from message — skipping Ollama.")
            else:
                doc_context = ""
                if _references_local_docs(message):
                    _log("User referenced local documents — loading sample_docs...")
                    doc_context = _load_sample_docs()

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

        # ── Default: plain chat ────────────────────────────────────────────
        _log(f"Sending to Ollama: {message[:80]}...")
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
