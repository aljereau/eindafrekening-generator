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
MAX_ITERATIONS = 20  # Safety limit for agent loop
MAX_RETRIES = 3      # Auto-correction attempts on SQL errors

# Model Configuration (provider, model_id)
DEFAULT_PROVIDER = "anthropic"  # Default fallback

# Legacy mapping (Internal defaults)
MODEL_IDS = {
    "anthropic": "claude-sonnet-4-5-20250929", # Dec 2025 Standard
    "openai": "gpt-5.1",
    "google": "gemini-1.5-pro"
}

# New Expanded Selection for TUI (Validated for Dec 2025)
# Format: (Display Name, "provider:model_id")
AVAILABLE_MODELS = [
    # Anthropic (4.5 Series)
    ("Claude 4.5 Sonnet", "anthropic:claude-sonnet-4-5-20250929"), # Released Sept 2025
    ("Claude 4.5 Opus", "anthropic:claude-opus-4-5-20251101"),     # Released Nov 2025
    ("Claude 4.5 Haiku", "anthropic:claude-haiku-4-5-20251001"),   # Released Oct 2025
    
    # OpenAI (GPT-5 & o3 Series)
    ("GPT-5.1 (Flagship)", "openai:gpt-5.1"),
    ("GPT-5 Mini", "openai:gpt-5-mini"),
    ("o3 (Listening/Reasoning)", "openai:o3"),
    ("o3-mini", "openai:o3-mini"),
    ("GPT-4o (Legacy)", "openai:gpt-4o"), # Maintained for compatibility
    
    # Google
    ("Gemini 1.5 Pro", "google:gemini-1.5-pro"),
    
    # Local
    ("SQLCoder 7B", "ollama:sqlcoder:7b"),
]

# Output Settings
DEFAULT_LANGUAGE = "nl"  # Dutch
MAX_ROWS_IN_CHAT = 10    # Show top N, export rest to Excel
