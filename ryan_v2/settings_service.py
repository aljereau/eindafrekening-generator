"""
Settings Service for RyanRent V2
Manages persistent user settings (active model, preferences, etc.)
"""
from pathlib import Path
import json
from typing import Dict, Any

# Settings file location (in database directory for Docker persistence)
SETTINGS_FILE = Path(__file__).parent.parent / "database" / "settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "active_model": "anthropic:claude-sonnet-4-5-20250929",
    "active_model_display": "Claude 4.5 Sonnet"
}

def load_settings() -> Dict[str, Any]:
    """Load settings from file, or return defaults if file doesn't exist"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, return defaults
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to file"""
    try:
        # Ensure config directory exists
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write settings
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except IOError:
        return False

def get_active_model() -> Dict[str, str]:
    """Get active model ID and display name"""
    settings = load_settings()
    return {
        "id": settings.get("active_model", DEFAULT_SETTINGS["active_model"]),
        "display": settings.get("active_model_display", DEFAULT_SETTINGS["active_model_display"])
    }

def set_active_model(model_id: str, display_name: str) -> bool:
    """Set the active model"""
    settings = load_settings()
    settings["active_model"] = model_id
    settings["active_model_display"] = display_name
    return save_settings(settings)
