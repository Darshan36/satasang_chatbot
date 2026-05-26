"""Shared configuration: loads the Gemini API key from the environment.

The key is read from the GEMINI_API_KEY environment variable. For local use we
also parse a `.env` file in this directory (a tiny parser so no extra dependency
is required). NEVER hardcode the key in source again, and keep `.env` out of git.
"""
import os

_ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def _load_dotenv(path=_ENV_FILE):
    """Minimal .env loader: KEY=VALUE per line, # comments ignored."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Don't override a value already set in the real environment.
            os.environ.setdefault(key, value)


def get_api_key():
    """Return the Gemini API key, raising a clear error if it is missing."""
    _load_dotenv()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Create a .env file next to this script "
            "containing:  GEMINI_API_KEY=your_key_here"
        )
    return key


# Model names used across the project (single source of truth).
# NOTE: the free-tier generate_content quota is very small, so generation is used
# ONLY for building the topic taxonomy (a handful of calls). Story categorization
# is done with the (separately-quota'd, generous) embedding model instead.
GEN_MODEL = "gemini-2.5-flash-lite"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768

# Groq (OpenAI-compatible) — used for high-throughput story categorization.
# Each model has its own daily budget; if one is exhausted, switch to another
# (e.g. openai/gpt-oss-20b, qwen/qwen3-32b, llama-3.1-8b-instant).
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_groq_key():
    _load_dotenv()
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment or .env file.")
    return key
