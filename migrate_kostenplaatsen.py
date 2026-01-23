#!/usr/bin/env python3
"""
Kostenplaatsen Migration Script
- Updates huizen.object_id in ryanrent_v2.db to match Exact CSV
- Normalizes A-codes in huizen_archief (ryanrent_mock.db) from A-XXXX to A-XXXXX

IMPORTANT: Run backup first! This script modifies the database.
Backup location: database/backups/ryanrent_v2_backup_20260123_0958.db
"""
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DB_V2_PATH = BASE_DIR / "database" / "ryanrent_v2.db"
DB_MOCK_PATH = BASE_DIR / "database" / "ryanrent_mock.db"
CSV_PATH = BASE_DIR / "Shared/Sources/csv_data/1-CoHousingNL_B.V.-23-01-2026-HRMCostCenters.csv"
LOG_PATH = BASE_DIR / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def log(msg: str, log_file):
    """Log to both console and file."""
    print(msg)
    log_file.write(msg + "\n")

def normalize_address(addr: str) -> str:
    """Normalize address for fuzzy matching."""
    if not addr:
        return ""
    return (addr.lower()
            .replace(",", "")
            .replace("'s-", "s-")
            .replace("'s ", "s ")
            .replace("-", " ")
            .strip())

def load_csv_data() -> dict:
    """Load and parse the Exact CSV file."""
    csv_data = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            code = row['Code'].strip()
            desc = row['Omschrijving'].strip()
            csv_data[code] = desc
    return csv_data

def find_csv_match(db_addr: str, csv_data: dict) -> str | None:
    """Find matching CSV code for a database address."""
    norm_db = normalize_address(db_addr)
    for code, csv_addr in csv_data.items():
        norm_csv = normalize_address(csv_addr)
        # Check if one contains the other (fuzzy match)
        if norm_db and norm_csv:
            if norm_db in norm_csv or norm_csv in norm_db:
                return code
    return None

def migrate_huizen(log_file):
    """Migrate huizen object_ids to match Exact CSV."""
    log("\n" + "="*60, log_file)
    log("PHASE 1: Migrating huizen object_ids (ryanrent_v2.db)", log_file)
    log("="*60, log_file)
    
    csv_data = load_csv_data()
    conn = sqlite3.connect(DB_V2_PATH)
    cursor = conn.cursor()
    
    # Get all huizen
    cursor.execute("SELECT id, object_id, adres, plaats FROM huizen ORDER BY id")
    huizen = cursor.fetchall()
    
    updates = []
    skipped = []
    
    for db_id, obj_id, adres, plaats in huizen:
        full_addr = f"{adres} {plaats or ''}".strip()
        padded_id = obj_id.zfill(4)
        
        # Check if current object_id matches CSV
        if padded_id in csv_data:
            csv_addr = csv_data[padded_id]
            norm_db = normalize_address(full_addr)
            norm_csv = normalize_address(csv_addr)
            
            if norm_db in norm_csv or norm_csv in norm_db:
                # Already matches, skip
                continue
            else:
                # Mismatch - try to find correct code
                correct_code = find_csv_match(full_addr, csv_data)
                if correct_code:
                    updates.append((db_id, obj_id, correct_code, full_addr, csv_data[correct_code]))
                else:
                    skipped.append((db_id, obj_id, full_addr, "No matching code found in CSV"))
        else:
            # Object ID not in CSV - try to find match
            correct_code = find_csv_match(full_addr, csv_data)
            if correct_code:
                updates.append((db_id, obj_id, correct_code, full_addr, csv_data[correct_code]))
            else:
                skipped.append((db_id, obj_id, full_addr, "No matching code found in CSV"))
    
    log(f"\nFound {len(updates)} object_ids to update", log_file)
    log(f"Skipped {len(skipped)} (no CSV match found)", log_file)
    
    if updates:
        log("\nUpdates to apply:", log_file)
        for db_id, old_id, new_id, db_addr, csv_addr in updates[:20]:
            log(f"  [{old_id}] → [{new_id}]: {db_addr[:40]}", log_file)
        if len(updates) > 20:
            log(f"  ...and {len(updates) - 20} more", log_file)
        
        # Apply updates
        log("\nApplying updates...", log_file)
        for db_id, old_id, new_id, _, _ in updates:
            try:
                cursor.execute("UPDATE huizen SET object_id = ? WHERE id = ?", (new_id, db_id))
            except sqlite3.IntegrityError as e:
                log(f"  ERROR updating {old_id} → {new_id}: {e}", log_file)
        
        conn.commit()
        log(f"✅ Applied {len(updates)} updates to huizen", log_file)
    
    conn.close()
    return len(updates)

def migrate_archief(log_file):
    """Normalize A-codes in huizen_archief from A-XXXX to A-XXXXX."""
    log("\n" + "="*60, log_file)
    log("PHASE 2: Normalizing A-codes in huizen_archief (ryanrent_mock.db)", log_file)
    log("="*60, log_file)
    
    conn = sqlite3.connect(DB_MOCK_PATH)
    cursor = conn.cursor()
    
    # Get all A-code entries
    cursor.execute("SELECT object_id FROM huizen_archief WHERE object_id LIKE 'A-%'")
    a_codes = cursor.fetchall()
    
    updates = []
    for (old_code,) in a_codes:
        # A-0001 → A-00001 (add leading zero after A-)
        if old_code.startswith('A-') and len(old_code) == 6:  # A-XXXX format
            new_code = f"A-{old_code[2:].zfill(5)}"  # A-XXXXX format
            updates.append((old_code, new_code))
    
    log(f"\nFound {len(updates)} A-codes to normalize", log_file)
    
    if updates:
        log("\nExamples:", log_file)
        for old, new in updates[:10]:
            log(f"  {old} → {new}", log_file)
        
        log("\nApplying updates...", log_file)
        for old_code, new_code in updates:
            try:
                cursor.execute("UPDATE huizen_archief SET object_id = ? WHERE object_id = ?", 
                             (new_code, old_code))
            except sqlite3.IntegrityError as e:
                log(f"  ERROR: {old_code} → {new_code}: {e}", log_file)
        
        conn.commit()
        log(f"✅ Normalized {len(updates)} A-codes", log_file)
    
    conn.close()
    return len(updates)

def main():
    with open(LOG_PATH, 'w', encoding='utf-8') as log_file:
        log("="*60, log_file)
        log("KOSTENPLAATSEN MIGRATION", log_file)
        log(f"Started: {datetime.now().isoformat()}", log_file)
        log("="*60, log_file)
        
        huizen_count = migrate_huizen(log_file)
        archief_count = migrate_archief(log_file)
        
        log("\n" + "="*60, log_file)
        log("MIGRATION COMPLETE", log_file)
        log("="*60, log_file)
        log(f"  Huizen updated: {huizen_count}", log_file)
        log(f"  A-codes normalized: {archief_count}", log_file)
        log(f"\nLog saved to: {LOG_PATH}", log_file)

if __name__ == "__main__":
    main()
