#!/usr/bin/env python3
"""
Export sales data to JSON for the web dashboard.
Run this whenever you want to update the dashboard data.

Usage:
    python export_sales_data.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, date

# Paths
DB_PATH = Path(__file__).parent.parent / "database" / "ryanrent_v2.db"
OUTPUT_PATH = Path(__file__).parent / "data.js"


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def export_data():
    """Export v_sales data to JSON."""
    print("📊 Exporting sales data...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM v_sales")
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Convert to list of dicts
    data = []
    for row in rows:
        d = {}
        for i, col in enumerate(columns):
            val = row[i]
            # Handle None values
            d[col] = val if val is not None else ""
        data.append(d)
    
    # Calculate summary stats
    total_props = len(data)
    active = sum(1 for d in data if d.get('huis_actief') == 1)
    available = sum(1 for d in data if d.get('beschikbaarheid_status') == 'Beschikbaar')
    rented = sum(1 for d in data if 'Verhuurd' in str(d.get('beschikbaarheid_status', '')))
    leegstand = sum(1 for d in data if d.get('beschikbaarheid_status') == 'Leegstand')
    
    total_marge = sum(float(d.get('marge_maand_excl_btw') or 0) for d in data)
    avg_marge = total_marge / total_props if total_props > 0 else 0
    
    # Get unique owners and tenants
    owners = list(set(d.get('eigenaar_naam') for d in data if d.get('eigenaar_naam')))
    tenants = list(set(d.get('huurder_naam') for d in data if d.get('huurder_naam')))
    cities = list(set(d.get('plaats') for d in data if d.get('plaats')))
    
    # Get configuratie values
    config_cursor = conn.execute("SELECT key, value FROM configuratie")
    config = {row[0]: row[1] for row in config_cursor.fetchall()}
    
    conn.close()
    
    # Build export object
    export = {
        "generated": datetime.now().isoformat(),
        "stats": {
            "total": total_props,
            "active": active,
            "available": available,
            "rented": rented,
            "leegstand": leegstand,
            "total_marge_maand": round(total_marge, 2),
            "avg_marge": round(avg_marge, 2),
            "total_marge_jaar": round(total_marge * 12, 2),
            "num_owners": len(owners),
            "num_tenants": len(tenants),
        },
        "config": config,
        "owners": sorted(owners),
        "tenants": sorted(tenants),
        "cities": sorted(cities),
        "properties": data,
    }
    
    # Write as JavaScript file (easier to load in HTML)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write("// Auto-generated sales data\n")
        f.write(f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("const SALES_DATA = ")
        json.dump(export, f, indent=2, default=json_serial, ensure_ascii=False)
        f.write(";\n")
    
    print(f"✅ Exported {total_props} properties to: {OUTPUT_PATH}")
    print(f"   Stats: {active} active, {available} available, {rented} rented")
    print(f"   Marge: €{total_marge:,.0f}/maand (€{total_marge*12:,.0f}/jaar)")
    print(f"   {len(owners)} eigenaren, {len(tenants)} huurders")
    
    return export


if __name__ == "__main__":
    export_data()
