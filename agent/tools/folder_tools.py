"""
tools/folder_tools.py — Folder organization and inspection utilities.
Student 1 owns this file.
"""

import os
import shutil
from collections import defaultdict


# Map of file extensions → subfolder names
EXTENSION_MAP = {
    ".pdf":  "PDFs",
    ".docx": "Docs",
    ".doc":  "Docs",
    ".txt":  "Docs",
    ".md":   "Docs",
    ".pptx": "Presentations",
    ".ppt":  "Presentations",
    ".xlsx": "Spreadsheets",
    ".xls":  "Spreadsheets",
    ".csv":  "Spreadsheets",
    ".jpg":  "Images",
    ".jpeg": "Images",
    ".png":  "Images",
    ".gif":  "Images",
    ".py":   "Code",
    ".js":   "Code",
    ".ts":   "Code",
    ".html": "Code",
    ".mp4":  "Videos",
    ".mov":  "Videos",
    ".mp3":  "Audio",
    ".wav":  "Audio",
}


def organize_folder(folder_path: str) -> dict:
    """
    Move files in folder_path into subfolders by file type.
    Does not touch existing subfolders or hidden files.

    Returns:
        {"success": bool, "moved": int, "skipped": int, "details": list[str], "message": str}
    """
    if not os.path.isdir(folder_path):
        return {"success": False, "moved": 0, "skipped": 0, "details": [],
                "message": "Directory not found."}

    moved, skipped = 0, 0
    details = []

    for fname in os.listdir(folder_path):
        src = os.path.join(folder_path, fname)

        # Skip subdirectories and hidden files
        if os.path.isdir(src) or fname.startswith("."):
            skipped += 1
            continue

        ext = os.path.splitext(fname)[1].lower()
        subfolder_name = EXTENSION_MAP.get(ext, "Other")
        dest_dir = os.path.join(folder_path, subfolder_name)
        os.makedirs(dest_dir, exist_ok=True)

        dest = os.path.join(dest_dir, fname)

        # Avoid overwriting existing files — append a counter
        if os.path.exists(dest):
            base, extension = os.path.splitext(fname)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(dest_dir, f"{base}_{counter}{extension}")
                counter += 1

        shutil.move(src, dest)
        details.append(f"{fname} → {subfolder_name}/")
        moved += 1

    return {
        "success": True,
        "moved": moved,
        "skipped": skipped,
        "details": details,
        "message": f"Organized {moved} files into subfolders.",
    }


def list_pdfs(directory: str) -> dict:
    """
    Recursively find all PDF files under a directory.

    Returns:
        {"success": bool, "directory": str, "pdfs": list[str], "count": int}
    """
    if not os.path.isdir(directory):
        return {"success": False, "directory": directory, "pdfs": [], "count": 0}

    pdfs = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, fname))

    return {
        "success": True,
        "directory": directory,
        "pdfs": sorted(pdfs),
        "count": len(pdfs),
    }


def get_folder_summary(folder_path: str) -> dict:
    """
    Return a breakdown of file counts grouped by type in a folder (recursive).

    Returns:
        {"success": bool, "total": int, "by_type": dict, "message": str}
    """
    if not os.path.isdir(folder_path):
        return {"success": False, "total": 0, "by_type": {}, "message": "Directory not found."}

    by_type: dict = defaultdict(int)
    total = 0

    for root, _, files in os.walk(folder_path):
        for fname in files:
            if fname.startswith("."):
                continue
            ext = os.path.splitext(fname)[1].lower() or "no extension"
            by_type[ext] += 1
            total += 1

    return {
        "success": True,
        "total": total,
        "by_type": dict(by_type),
        "message": f"Found {total} files across {len(by_type)} types.",
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile, json

    with tempfile.TemporaryDirectory() as tmp:
        # Create dummy files
        for name in ["notes.txt", "report.pdf", "data.csv", "script.py", "image.png"]:
            open(os.path.join(tmp, name), "w").close()

        print("Before organize:")
        print(json.dumps(get_folder_summary(tmp), indent=2))
        print("\nOrganizing...")
        print(json.dumps(organize_folder(tmp), indent=2))
        print("\nAfter organize:")
        print(json.dumps(get_folder_summary(tmp), indent=2))