import sys
import os
import json
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import ConversationMemory

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

def mock_api_callback(messages: List[Dict], system_prompt: str = None) -> Any:
    """Mock API response for summarization"""
    print(f"  [MockAPI] Received {len(messages)} messages for summarization.")
    print(f"  [MockAPI] System Prompt: {system_prompt[:50]}...")
    
    # Return a fake summary wrapped in OpenAI-like structure
    return MockResponse("SUMMARY: User asked about houses. Bot replied with list. User asked for details on House 1.")

def test_memory():
    print("🧪 Testing ConversationMemory...")
    
    # Initialize with small max_messages for testing
    memory = ConversationMemory(max_messages=3)
    
    # 1. Add messages (under limit)
    print("\n1. Adding 5 messages (limit is 3*2 = 6)...")
    for i in range(5):
        memory.add_message("user", f"Message {i}")
        memory.add_message("assistant", f"Response {i}")
    
    # Check status
    print(f"  History length: {len(memory.history)}")
    should_sum = memory.should_summarize()
    print(f"  Should summarize? {should_sum}")
    assert should_sum == True, "Should summarize because 10 > 6"
    
    # 2. Trigger Summarization
    print("\n2. Triggering Summarization...")
    memory.summarize(mock_api_callback)
    
    # Verify results
    print(f"  New History length: {len(memory.history)}")
    print(f"  Summary: {memory.summary}")
    
    assert len(memory.history) == 3, "History should be trimmed to max_messages (3)"
    assert "SUMMARY" in memory.summary, "Summary should be updated"
    
    # 3. Verify Context Construction
    print("\n3. Verifying Context Construction...")
    context = memory.get_context_messages()
    print(f"  Context length: {len(context)}")
    print(f"  First message role: {context[0]['role']}")
    
    # We expect: Summary User Msg + Summary Assistant Msg + 3 History Msgs = 5 messages
    assert len(context) == 5, f"Expected 5 messages in context, got {len(context)}"
    assert "summary" in context[0]['content'], "First message should contain summary"
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_memory()
