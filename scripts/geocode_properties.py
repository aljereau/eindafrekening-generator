#!/usr/bin/env python3
"""
Geocode all properties by postcode to get lat/lng coordinates.
Uses Nominatim (OpenStreetMap) API with rate limiting.

Usage:
    python geocode_properties.py
"""

import sqlite3
import time
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Paths
DB_PATH = Path(__file__).parent.parent / "database" / "ryanrent_v2.db"

# Nominatim API (free, 1 req/second)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def geocode_postcode(postcode, country="Netherlands"):
    """Geocode a Dutch postcode using Nominatim."""
    if not postcode:
        return None, None
    
    # Clean postcode (remove spaces)
    postcode = postcode.replace(" ", "").upper()
    
    # Build query
    from urllib.parse import quote
    query = f"{postcode}, {country}"
    url = f"{NOMINATIM_URL}?q={quote(query)}&format=json&limit=1&countrycodes=nl"
    
    headers = {
        "User-Agent": "RyanRent-PropertyManager/1.0 (property geocoding)"
    }
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                return lat, lng
    except (URLError, HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"  ⚠️ Failed to geocode {postcode}: {e}")
    
    return None, None


def add_geocode_columns():
    """Add lat/lng columns to huizen table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(huizen)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "latitude" not in columns:
        cursor.execute("ALTER TABLE huizen ADD COLUMN latitude REAL")
        print("✅ Added latitude column")
    
    if "longitude" not in columns:
        cursor.execute("ALTER TABLE huizen ADD COLUMN longitude REAL")
        print("✅ Added longitude column")
    
    conn.commit()
    conn.close()


def geocode_all_properties():
    """Geocode all properties that don't have coordinates yet."""
    print("🌍 Geocoding properties...")
    
    add_geocode_columns()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get properties without coordinates
    cursor.execute("""
        SELECT object_id, postcode 
        FROM huizen 
        WHERE postcode IS NOT NULL 
          AND postcode != ''
          AND (latitude IS NULL OR longitude IS NULL)
    """)
    
    properties = cursor.fetchall()
    total = len(properties)
    
    if total == 0:
        print("✅ All properties already geocoded!")
        conn.close()
        return
    
    print(f"📍 Found {total} properties to geocode")
    
    geocoded = 0
    failed = 0
    
    for i, (object_id, postcode) in enumerate(properties, 1):
        print(f"[{i}/{total}] Geocoding {object_id} ({postcode})...", end=" ")
        
        lat, lng = geocode_postcode(postcode)
        
        if lat and lng:
            cursor.execute("""
                UPDATE huizen 
                SET latitude = ?, longitude = ?
                WHERE object_id = ?
            """, (lat, lng, object_id))
            print(f"✓ ({lat:.4f}, {lng:.4f})")
            geocoded += 1
        else:
            print("✗ Failed")
            failed += 1
        
        # Rate limit: 1 request per second (Nominatim policy)
        time.sleep(1.1)
        
        # Commit every 10 records
        if i % 10 == 0:
            conn.commit()
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Geocoding complete!")
    print(f"   Success: {geocoded}")
    print(f"   Failed: {failed}")


def get_geocode_stats():
    """Get stats on geocoded properties."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM huizen WHERE latitude IS NOT NULL")
    geocoded = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM huizen WHERE postcode IS NOT NULL AND postcode != ''")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"📊 Geocode stats: {geocoded}/{total} properties have coordinates")
    return geocoded, total


if __name__ == "__main__":
    add_geocode_columns()  # Ensure columns exist first
    get_geocode_stats()
    geocode_all_properties()
    get_geocode_stats()
