"""
RYAN-V2: RyanRent Intelligent Agent
Configuration Module
"""
import os
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on system env vars

# Database
DB_PATH = Path(__file__).parent.parent / "database" / "ryanrent_mock.db"

# Agent Settings
MAX_ITERATIONS = 10  # Safety limit for agent loop
MAX_RETRIES = 3      # Auto-correction attempts on SQL errors

# Model Configuration (provider, model_id)
DEFAULT_PROVIDER = "anthropic"  # Options: "anthropic", "openai", "google"
MODEL_IDS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "google": "gemini-1.5-flash"
}

# Output Settings
DEFAULT_LANGUAGE = "nl"  # Dutch
MAX_ROWS_IN_CHAT = 10    # Show top N, export rest to Excel
