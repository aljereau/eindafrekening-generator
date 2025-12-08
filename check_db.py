import sqlite3
import os

db_path = 'database/ryanrent_core.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Checking for properties with 'Rooseveltlaan' in address:")
cursor.execute("SELECT id, adres, postcode, plaats FROM huizen WHERE adres LIKE '%Rooseveltlaan%'")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\nChecking for properties with '4624DM' in postcode:")
cursor.execute("SELECT id, adres, postcode, plaats FROM huizen WHERE postcode LIKE '%4624DM%'")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
