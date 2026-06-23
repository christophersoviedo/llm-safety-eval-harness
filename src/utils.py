import time
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

@contextmanager
def timer():
    """Context manager to measure execution latency in seconds."""
    start = time.perf_counter()
    metrics = {"latency": 0.0}
    yield metrics
    metrics["latency"] = time.perf_counter() - start

def get_api_key(provider: str) -> str:
    """
    Retrieve the API key for the specified provider (anthropic or openai).
    Returns an empty string if not found.
    """
    if provider.lower() == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY", "")
    elif provider.lower() == "openai":
        return os.getenv("OPENAI_API_KEY", "")
    return ""

def parse_bool(val: str) -> bool:
    """Helper to parse boolean strings from CSV."""
    if not val:
        return False
    return val.strip().upper() in ("TRUE", "1", "YES", "T")
