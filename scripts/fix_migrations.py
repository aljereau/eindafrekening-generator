
import sqlite3
import datetime

db_path = "database/ryanrent_mock.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

migrations_to_add = [
    "017_expand_huizen_leveranciers.sql",
    "018_verhuur_details.sql",
    "019_add_vve_kosten.sql"
]

print("🔍 Checking and fixing migration records...")

for migration in migrations_to_add:
    # Check if exists
    cursor.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (migration,))
    if cursor.fetchone():
        print(f"  - {migration} already recorded.")
    else:
        print(f"  - Inserting record for {migration}...")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)", (migration, now))

conn.commit()
print("✅ Done. Schema migrations are now in sync with database structure.")
conn.close()
