import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

def test_intelligence():
    print("🤖 Initializing RyanRentBot...")
    # Mock API key as we are testing internal tools
    bot = RyanRentBot(api_key="test", db_path="database/ryanrent_mock.db", provider="openai")
    
    print("\n🔍 Testing Audit Controller...")
    audit_result = bot._execute_tool("run_audit", {})
    print(f"Audit Result: {json.dumps(audit_result, indent=2)}")
    
    print("\n📊 Testing Query Analyst (Profitability)...")
    query_result = bot._execute_tool("run_analyst_query", {"query_type": "profitability"})
    print(f"Query Result (First 2): {json.dumps(query_result[:2], indent=2)}")
    
    print("\n✅ Tests Complete!")

if __name__ == "__main__":
    test_intelligence()
