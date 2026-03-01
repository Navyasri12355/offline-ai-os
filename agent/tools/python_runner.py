"""
tools/python_runner.py — Safe subprocess wrapper to execute Python scripts.
Student 1 owns this file.

Used as a fallback: if the agent can't dynamically generate code,
run a pre-written script instead (e.g. demo/generate_summary_ppt.py).
"""

import subprocess
import sys
import os


# ── Safety: only allow scripts within the project directory ───────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TIMEOUT_SECONDS = 60


def run_script(script_path: str, args: list[str] = None) -> dict:
    """
    Execute a Python script and return its output.

    Args:
        script_path: Absolute or relative path to the .py file.
        args:        Optional list of CLI arguments to pass to the script.

    Returns:
        {
            "success":     bool,
            "script":      str,
            "stdout":      str,
            "stderr":      str,
            "returncode":  int,
            "message":     str,
        }
    """
    args = args or []
    script_path = os.path.abspath(script_path)

    # ── Safety checks ──────────────────────────────────────────────────────────
    if not os.path.exists(script_path):
        return _error(script_path, "Script not found.")

    if not script_path.endswith(".py"):
        return _error(script_path, "Only .py scripts are allowed.")

    if not script_path.startswith(PROJECT_ROOT):
        return _error(script_path, "Script must be inside the project directory.")

    # ── Execute ────────────────────────────────────────────────────────────────
    cmd = [sys.executable, script_path] + [str(a) for a in args]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=PROJECT_ROOT,
        )
        success = result.returncode == 0
        return {
            "success": success,
            "script": script_path,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "message": "OK" if success else f"Script exited with code {result.returncode}",
        }

    except subprocess.TimeoutExpired:
        return _error(script_path, f"Script timed out after {TIMEOUT_SECONDS}s.")
    except Exception as e:
        return _error(script_path, str(e))


def _error(script_path: str, message: str) -> dict:
    return {
        "success": False,
        "script": script_path,
        "stdout": "",
        "stderr": "",
        "returncode": -1,
        "message": message,
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, tempfile

    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", dir=PROJECT_ROOT, delete=False
    ) as f:
        f.write('print("Hello from python_runner test!")\n')
        tmp_script = f.name

    try:
        result = run_script(tmp_script)
        print(json.dumps(result, indent=2))
    finally:
        os.unlink(tmp_script)