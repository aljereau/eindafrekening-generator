from ryan_v2.agent import RyanAgent
from ryan_v2.config import MODEL_IDS

def test_init():
    print("🧪 Testing RyanAgent Initialization...")
    
    # TC1: specific model ID
    print("\n1. Testing Composite String: 'openai:gpt-4o'")
    agent1 = RyanAgent("openai:gpt-4o")
    print(f"   Provider: {agent1.provider} (Expected: openai)")
    print(f"   Model ID: {agent1.model_id} (Expected: gpt-4o)")
    
    assert agent1.provider == "openai"
    assert agent1.model_id == "gpt-4o"
    print("   ✅ PASS")

    # TC2: legacy provider name
    print("\n2. Testing Legacy String: 'anthropic'")
    agent2 = RyanAgent("anthropic")
    print(f"   Provider: {agent2.provider} (Expected: anthropic)")
    expected_default = MODEL_IDS["anthropic"]
    print(f"   Model ID: {agent2.model_id} (Expected: {expected_default})")
    
    assert agent2.provider == "anthropic"
    assert agent2.model_id == expected_default
    print("   ✅ PASS")

if __name__ == "__main__":
    try:
        test_init()
        print("\n✨ All Agent Init Tests Passed!")
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
