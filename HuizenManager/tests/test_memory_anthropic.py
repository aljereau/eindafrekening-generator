import sys
import os
import json
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import ConversationMemory

def mock_anthropic_callback(messages: List[Dict], system_prompt: str = None) -> Dict:
    """Mock Anthropic API response for summarization"""
    print(f"  [MockAPI] Received {len(messages)} messages for summarization.")
    
    # Return a fake summary in Anthropic format (dict with content list)
    return {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "SUMMARY: User asked about Anthropic. Bot replied it works."
            }
        ],
        "model": "claude-3-sonnet-20240229",
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 10}
    }

def test_memory_anthropic():
    print("🧪 Testing ConversationMemory with Anthropic format...")
    
    memory = ConversationMemory(max_messages=3)
    
    # 1. Add messages
    for i in range(5):
        memory.add_message("user", f"Message {i}")
        memory.add_message("assistant", f"Response {i}")
    
    # 2. Trigger Summarization
    print("\n2. Triggering Summarization...")
    memory.summarize(mock_anthropic_callback)
    
    # Verify results
    print(f"  Summary: {memory.summary}")
    
    assert "Anthropic" in memory.summary, "Summary should be updated from Anthropic response"
    print("\n✅ Anthropic test passed!")

if __name__ == "__main__":
    test_memory_anthropic()
