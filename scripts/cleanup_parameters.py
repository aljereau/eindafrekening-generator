import sqlite3
from pathlib import Path

# DB Path
DB_PATH = Path("database/ryanrent_mock.db")

def cleanup():
    print(f"🧹 Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Remove 'RR Vuilcontainers/Afval'
        print("🗑️  Removing 'RR Vuilcontainers/Afval'...")
        cursor.execute("DELETE FROM parameters WHERE naam LIKE '%Vuilcontainers%' OR naam LIKE '%Afval%'")
        print(f"   - Deleted {cursor.rowcount} rows.")

        # 2. Remove Test IDs (8, 9, 10)
        print("🗑️  Removing Test IDs 8, 9, 10...")
        cursor.execute("DELETE FROM parameters WHERE id IN (8, 9, 10)")
        print(f"   - Deleted {cursor.rowcount} rows.")
        
        # 3. Double check for 'Test Internet' just in case IDs differ
        cursor.execute("DELETE FROM parameters WHERE naam LIKE 'Test Internet%'")
        if cursor.rowcount > 0:
            print(f"   - Deleted {cursor.rowcount} additional 'Test Internet' rows.")

        conn.commit()
        print("\n✅ Cleanup completed successfully!")
        
        # Verify
        print("\n📊 Current Parameters Table:")
        cursor.execute("SELECT id, naam, prijs_pp_pw FROM parameters")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Cleanup failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup()
