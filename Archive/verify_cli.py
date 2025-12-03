import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src import cli
from HuizenManager.src.manager import HuizenManager

def test_cli_functions():
    print("--- Testing CLI Functions ---")
    manager = HuizenManager()
    
    print("\n1. Testing list_houses...")
    try:
        # Capture stdout to avoid cluttering
        cli.list_houses(manager)
        print("✅ list_houses ran successfully")
    except Exception as e:
        print(f"❌ list_houses failed: {e}")

    print("\n2. Testing list_houses with filter...")
    try:
        cli.list_houses(manager, filter_str="Rotterdam")
        print("✅ list_houses (filtered) ran successfully")
    except Exception as e:
        print(f"❌ list_houses (filtered) failed: {e}")

if __name__ == "__main__":
    test_cli_functions()
