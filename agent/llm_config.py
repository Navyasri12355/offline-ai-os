"""
llm_config.py — Ollama connection config and model selection.
Student 1 owns this file.
"""

import requests

# ── Model selection ────────────────────────────────────────────────────────────
# Change MODEL_NAME to whichever model you have pulled locally.
# Recommended order: phi3 (fastest) > llama3 (smarter) > tinyllama (lightest)
MODEL_NAME = "phi3"

# ── Ollama base URL ────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"

# LiteLLM-compatible model string (used by Open Interpreter)
LITELLM_MODEL = f"ollama/{MODEL_NAME}"
LITELLM_API_BASE = OLLAMA_BASE_URL


def check_ollama_running() -> bool:
    """Ping Ollama to confirm it's live before starting the agent."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def get_available_models() -> list[str]:
    """Return list of locally pulled model names."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        data = r.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


if __name__ == "__main__":
    if check_ollama_running():
        print(f"✅ Ollama is running. Available models: {get_available_models()}")
    else:
        print("❌ Ollama not running. Start it with: ollama serve")
        print(f"   Then pull a model: ollama pull {MODEL_NAME}")