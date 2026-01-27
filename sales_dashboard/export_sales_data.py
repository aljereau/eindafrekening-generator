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
    
    # Get unique owners and tenants from properties
    owners_from_props = list(set(d.get('eigenaar_naam') for d in data if d.get('eigenaar_naam')))
    tenants_from_props = list(set(d.get('huurder_naam') for d in data if d.get('huurder_naam')))
    cities = list(set(d.get('plaats') for d in data if d.get('plaats')))
    
    # Get ALL relaties from database (including orphans not connected to contracts)
    relaties_cursor = conn.execute("""
        SELECT 
            r.id,
            r.naam,
            r.type,
            r.contactpersoon,
            r.email,
            r.telefoonnummer,
            r.adres,
            r.postcode,
            r.plaats,
            r.land,
            r.kvk_nummer,
            r.btw_nummer,
            r.iban,
            r.marge_max,
            -- Check if this relatie is an eigenaar (has inhuur contracts)
            (SELECT COUNT(*) FROM inhuur_contracten ic WHERE ic.relatie_id = r.id) as inhuur_count,
            -- Check if this relatie is a huurder (has verhuur contracts)
            (SELECT COUNT(*) FROM verhuur_contracten vc WHERE vc.relatie_id = r.id) as verhuur_count
        FROM relaties r
        ORDER BY r.naam
    """)
    
    all_relaties = []
    for row in relaties_cursor.fetchall():
        all_relaties.append({
            "id": row[0],
            "naam": row[1] or "",
            "type": row[2] or "",
            "contactpersoon": row[3] or "",
            "email": row[4] or "",
            "telefoon": row[5] or "",
            "adres": row[6] or "",
            "postcode": row[7] or "",
            "plaats": row[8] or "",
            "land": row[9] or "",
            "kvk": row[10] or "",
            "btw": row[11] or "",
            "iban": row[12] or "",
            "marge_max": row[13],
            "inhuur_count": row[14] or 0,
            "verhuur_count": row[15] or 0,
            "is_eigenaar": (row[14] or 0) > 0,
            "is_huurder": (row[15] or 0) > 0,
        })
    
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
            "num_owners": len([r for r in all_relaties if r['is_eigenaar']]),
            "num_tenants": len([r for r in all_relaties if r['is_huurder']]),
            "num_relaties": len(all_relaties),
        },
        "config": config,
        "owners": sorted(owners_from_props),
        "tenants": sorted(tenants_from_props),
        "cities": sorted(cities),
        "properties": data,
        "relaties": all_relaties,  # All relaties including orphans
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
    print(f"   {len(all_relaties)} relaties ({len([r for r in all_relaties if r['is_eigenaar']])} eigenaren, {len([r for r in all_relaties if r['is_huurder']])} huurders)")
    
    return export


if __name__ == "__main__":
    export_data()
