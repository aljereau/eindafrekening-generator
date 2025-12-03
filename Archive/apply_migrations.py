import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from Shared.database import Database

def apply_migrations():
    print("Initializing database and applying migrations...")
    db = Database()
    # Database() __init__ automatically calls _init_database(), so we are done.
    print("Done!")

if __name__ == "__main__":
    apply_migrations()
