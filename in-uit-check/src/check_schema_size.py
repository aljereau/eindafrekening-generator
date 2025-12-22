import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.intelligence_api import IntelligenceAPI

def check_schema_size():
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    api = IntelligenceAPI(db_path)
    schema = api.get_database_schema()
    print(f"Schema Length: {len(schema)} characters")
    print("-" * 20)
    print(schema[:500] + "...")

if __name__ == "__main__":
    check_schema_size()
