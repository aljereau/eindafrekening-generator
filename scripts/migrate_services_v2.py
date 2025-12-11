import sqlite3
from pathlib import Path

# DB Path (using mock for safety first, user can switch to core later)
DB_PATH = Path("database/ryanrent_mock.db")

def migrate():
    print(f"🔌 Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Update Parameter Names (Rows)
        print("📝 Updating 'parameters' table names...")
        updates = [
            ("Internet", "%Internet Kosten%"),
            ("Meubilering", "%Inventaris & Inrichting%"),
            ("Tuinonderhoud", "%Schades & Onderhoud%"), # Assuming this maps to Tuinonderhoud as per user
            ("Aanschaf inventaris", "%Aanschaf inventaris%"),
            ("Eindschoonmaak", "%schoonmaak%"), # Ensure cleaning maps correctly if exists
            # "Bedlinnen" mapped to "Aanschaf inventaris" logic handled by user instruction, 
            # likely requires row merge or rename if Bedlinnen exists, but sample didn't show Bedlinnen.
        ]
        
        for new_name, pattern in updates:
            cursor.execute("UPDATE parameters SET naam = ? WHERE naam LIKE ?", (new_name, pattern))
            print(f"   - Renamed matches of '{pattern}' to '{new_name}'")

        # 2. Insert Missing Parameters
        print("➕ Checking for missing parameters...")
        missing_params = [
            ("Stoffering", 0.0, "per_week", "Soft furnishings"),
        ]
        for name, price, unit, desc in missing_params:
            # Check if exists
            cursor.execute("SELECT 1 FROM parameters WHERE naam = ?", (name,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO parameters (naam, prijs_pp_pw, eenheid, beschrijving) VALUES (?, ?, ?, ?)",
                    (name, price, unit, desc)
                )
                print(f"   - Added new parameter: '{name}'")

        # 3. Schema Updates (Columns in inhuur_contracten)
        print("🏗️  Updating 'inhuur_contracten' schema...")
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(inhuur_contracten)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 3a. Add new columns
        new_cols = ["tuinonderhoud", "stoffering", "aanschaf_inventaris"]
        for col in new_cols:
            if col not in columns:
                cursor.execute(f"ALTER TABLE inhuur_contracten ADD COLUMN {col} REAL DEFAULT 0")
                print(f"   - Added column: '{col}'")
        
        # 3b. Rename existing columns (SQLite supports this in recent versions)
        renames = {
            "internet_kosten": "internet",
            "inventaris_kosten": "meubilering",
            "schoonmaak_kosten": "eindschoonmaak" # Matching the parameter concept
        }
        
        for old_col, new_col in renames.items():
            if old_col in columns and new_col not in columns:
                cursor.execute(f"ALTER TABLE inhuur_contracten RENAME COLUMN {old_col} TO {new_col}")
                print(f"   - Renamed column: '{old_col}' -> '{new_col}'")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
