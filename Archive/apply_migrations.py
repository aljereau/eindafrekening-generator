import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Shared.database import Database

def apply_migrations():
    print("Initializing database and applying migrations...")
    db = Database()
    print("Done!")

if __name__ == "__main__":
    apply_migrations()
