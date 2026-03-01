"""
tool_manager.py — Registry of all tools the agent can call.
Student 1 owns this file.

Each tool is a plain Python function. The agent_controller imports
TOOLS_REGISTRY so Open Interpreter knows what's available.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools.file_tools import (
    create_file,
    read_file,
    list_files,
    delete_file,
)
from agent.tools.folder_tools import (
    organize_folder,
    list_pdfs,
    get_folder_summary,
)
from agent.tools.pptx_generator import generate_ppt
from agent.tools.python_runner import run_script


# ── Tool registry ──────────────────────────────────────────────────────────────
# Each entry describes a callable tool for the agent.
# "fn"          : the actual function to call
# "description" : what the agent sees when deciding which tool to use

TOOLS_REGISTRY = [
    {
        "name": "create_file",
        "fn": create_file,
        "description": "Create a new file with given content. Args: path (str), content (str)",
    },
    {
        "name": "read_file",
        "fn": read_file,
        "description": "Read and return the contents of a file. Args: path (str)",
    },
    {
        "name": "list_files",
        "fn": list_files,
        "description": "List all files in a directory. Args: directory (str)",
    },
    {
        "name": "delete_file",
        "fn": delete_file,
        "description": "Delete a file at the given path. Args: path (str)",
    },
    {
        "name": "organize_folder",
        "fn": organize_folder,
        "description": (
            "Organize files in a folder into subfolders by extension. "
            "Args: folder_path (str)"
        ),
    },
    {
        "name": "list_pdfs",
        "fn": list_pdfs,
        "description": "List all PDF files in a directory recursively. Args: directory (str)",
    },
    {
        "name": "get_folder_summary",
        "fn": get_folder_summary,
        "description": (
            "Return a summary dict of file counts and types in a folder. "
            "Args: folder_path (str)"
        ),
    },
    {
        "name": "generate_ppt",
        "fn": generate_ppt,
        "description": (
            "Generate a .pptx presentation. "
            "Args: title (str), slides (list of dicts with 'heading' and 'bullets' keys), "
            "output_path (str)"
        ),
    },
    {
        "name": "run_script",
        "fn": run_script,
        "description": (
            "Run a Python script file and return its stdout output. "
            "Args: script_path (str), args (list of str, optional)"
        ),
    },
]


def get_tool(name: str):
    """Look up a tool function by name."""
    for tool in TOOLS_REGISTRY:
        if tool["name"] == name:
            return tool["fn"]
    raise ValueError(f"Tool '{name}' not found in registry.")


def list_tool_names() -> list[str]:
    return [t["name"] for t in TOOLS_REGISTRY]


if __name__ == "__main__":
    print("📦 Registered tools:")
    for t in TOOLS_REGISTRY:
        print(f"  • {t['name']}: {t['description'][:60]}...")