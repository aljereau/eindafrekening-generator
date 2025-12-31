"""
RYAN-V2: Agentic Pipeline
Cache Manager Module

Deduplicates requests by caching exports with TTL.
This is pure code - NO LLM calls.
"""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("ryan_cache")

# Cache directory
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_TTL_HOURS = 24


def get_cache_key(intent: str, params: Dict[str, Any], profile: str) -> str:
    """
    Generate a stable cache key from request parameters.
    
    Args:
        intent: The classified intent name
        params: Query parameters (date ranges, filters, etc.)
        profile: Column profile (ops, finance)
        
    Returns:
        MD5 hash string
    """
    # Normalize params for consistent hashing
    normalized = {
        "intent": intent,
        "params": {k: str(v) for k, v in sorted(params.items()) if v is not None},
        "profile": profile
    }
    data = json.dumps(normalized, sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()


def get_cached_export(cache_key: str) -> Optional[Path]:
    """
    Get cached file path if exists and not expired.
    
    Args:
        cache_key: Hash key from get_cache_key()
        
    Returns:
        Path to cached file, or None if not found/expired
    """
    # Check both xlsx and csv
    for ext in [".xlsx", ".csv"]:
        cache_path = CACHE_DIR / f"{cache_key}{ext}"
        if cache_path.exists():
            mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
            age = datetime.now() - mtime
            if age < timedelta(hours=CACHE_TTL_HOURS):
                logger.info(f"Cache hit: {cache_key} (age: {age})")
                return cache_path
            else:
                # Expired, delete it
                cache_path.unlink()
                logger.info(f"Cache expired: {cache_key}")
    
    return None


def save_to_cache(cache_key: str, source_path: Path) -> Path:
    """
    Copy an export to the cache directory.
    
    Args:
        cache_key: Hash key from get_cache_key()
        source_path: Path to the source file
        
    Returns:
        Path to the cached file
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    ext = source_path.suffix
    cache_path = CACHE_DIR / f"{cache_key}{ext}"
    
    shutil.copy(source_path, cache_path)
    logger.info(f"Cached: {source_path.name} → {cache_key}")
    
    return cache_path


def clear_cache(older_than_hours: Optional[int] = None) -> int:
    """
    Clear cached files.
    
    Args:
        older_than_hours: Only clear files older than this. If None, clear all.
        
    Returns:
        Number of files deleted
    """
    if not CACHE_DIR.exists():
        return 0
    
    deleted = 0
    cutoff = datetime.now() - timedelta(hours=older_than_hours) if older_than_hours else None
    
    for cache_file in CACHE_DIR.glob("*"):
        if cache_file.is_file():
            if cutoff:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff:
                    cache_file.unlink()
                    deleted += 1
            else:
                cache_file.unlink()
                deleted += 1
    
    logger.info(f"Cleared {deleted} cached files")
    return deleted


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    if not CACHE_DIR.exists():
        return {"total_files": 0, "total_size_bytes": 0, "oldest_file": None}
    
    files = list(CACHE_DIR.glob("*"))
    if not files:
        return {"total_files": 0, "total_size_bytes": 0, "oldest_file": None}
    
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    oldest = min(files, key=lambda f: f.stat().st_mtime)
    oldest_age = datetime.now() - datetime.fromtimestamp(oldest.stat().st_mtime)
    
    return {
        "total_files": len(files),
        "total_size_bytes": total_size,
        "total_size_human": f"{total_size / 1024:.1f} KB" if total_size < 1024*1024 else f"{total_size / (1024*1024):.1f} MB",
        "oldest_file": oldest.name,
        "oldest_age_hours": oldest_age.total_seconds() / 3600,
        "cache_dir": str(CACHE_DIR)
    }


# =============================================================================
# CLI TEST
# =============================================================================

if __name__ == "__main__":
    # Test cache key generation
    key1 = get_cache_key("checkout_list", {"date_from": "2026-01-01", "date_to": "2026-03-31"}, "ops")
    key2 = get_cache_key("checkout_list", {"date_from": "2026-01-01", "date_to": "2026-03-31"}, "ops")
    key3 = get_cache_key("checkout_list", {"date_from": "2026-01-01", "date_to": "2026-06-30"}, "ops")
    
    print(f"Key 1: {key1}")
    print(f"Key 2: {key2}")
    print(f"Key 3: {key3}")
    print(f"Key 1 == Key 2: {key1 == key2}")  # Should be True
    print(f"Key 1 == Key 3: {key1 == key3}")  # Should be False
    
    print(f"\nCache stats: {get_cache_stats()}")
