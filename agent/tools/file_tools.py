"""
tools/file_tools.py — Basic file read/write/delete operations.
Student 1 owns this file.
"""

import os


def create_file(path: str, content: str) -> dict:
    """
    Create a new file at the given path with the given content.
    Creates intermediate directories if they don't exist.

    Returns:
        {"success": bool, "path": str, "message": str}
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path, "message": f"File created: {path}"}
    except Exception as e:
        return {"success": False, "path": path, "message": str(e)}


def read_file(path: str, max_chars: int = 4000) -> dict:
    """
    Read and return the contents of a file.
    Handles PDFs using PyPDF2 (first 5 pages only).
    Truncates content to max_chars to avoid overwhelming the LLM.

    Returns:
        {"success": bool, "path": str, "content": str, "message": str}
    """
    try:
        if not os.path.exists(path):
            return {"success": False, "path": path, "content": "", "message": "File not found."}

        # ── PDF handling ───────────────────────────────────────────────────
        if path.lower().endswith(".pdf"):
            try:
                import PyPDF2
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    content = ""
                    # Only read first 5 pages to keep context manageable
                    for i, page in enumerate(reader.pages):
                        if i >= 5:
                            break
                        extracted = page.extract_text()
                        if extracted:
                            content += extracted + "\n"
                content = content.strip()
                if not content:
                    return {
                        "success": False,
                        "path": path,
                        "content": "",
                        "message": "PDF has no extractable text (may be scanned/image-based).",
                    }
                return {
                    "success": True,
                    "path": path,
                    "content": content[:max_chars],
                    "message": f"OK (PDF, {min(5, len(reader.pages))} pages extracted)",
                }
            except ImportError:
                return {
                    "success": False,
                    "path": path,
                    "content": "",
                    "message": "PyPDF2 not installed. Run: pip install PyPDF2",
                }

        # ── Plain text handling ────────────────────────────────────────────
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {
            "success": True,
            "path": path,
            "content": content[:max_chars],
            "message": "OK",
        }

    except Exception as e:
        return {"success": False, "path": path, "content": "", "message": str(e)}


def list_files(directory: str) -> dict:
    """
    List all files in a directory (non-recursive).

    Returns:
        {"success": bool, "directory": str, "files": list[str], "message": str}
    """
    try:
        if not os.path.isdir(directory):
            return {
                "success": False,
                "directory": directory,
                "files": [],
                "message": "Directory not found.",
            }
        files = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]
        return {
            "success": True,
            "directory": directory,
            "files": sorted(files),
            "message": f"{len(files)} files found.",
        }
    except Exception as e:
        return {"success": False, "directory": directory, "files": [], "message": str(e)}


def delete_file(path: str) -> dict:
    """
    Delete a file at the given path.

    Returns:
        {"success": bool, "path": str, "message": str}
    """
    try:
        if not os.path.exists(path):
            return {"success": False, "path": path, "message": "File not found."}
        os.remove(path)
        return {"success": True, "path": path, "message": f"Deleted: {path}"}
    except Exception as e:
        return {"success": False, "path": path, "message": str(e)}


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile, json, sys

    # Test plain text
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "test.txt")
        print(json.dumps(create_file(p, "Hello, Offline AI OS!"), indent=2))
        print(json.dumps(read_file(p), indent=2))
        print(json.dumps(list_files(tmp), indent=2))
        print(json.dumps(delete_file(p), indent=2))

    # Test PDF if path provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"\nTesting PDF: {pdf_path}")
        result = read_file(pdf_path)
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Content preview:\n{result['content'][:300]}")