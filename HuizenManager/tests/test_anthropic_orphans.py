import sys
import os
import json
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

def test_orphan_tool_handling():
    print("🧪 Testing Anthropic Orphan Tool Handling...")
    
    # Initialize bot with dummy key (we won't make API calls)
    bot = RyanRentBot(api_key="dummy", provider="anthropic")
    
    # Scenario 1: Orphan Tool Result at start
    # This happens if history is truncated and the assistant message is lost
    messages = [
        {
            "role": "tool",
            "tool_call_id": "call_123",
            "content": "Result of tool 123"
        },
        {
            "role": "user",
            "content": "What happened?"
        }
    ]
    
    converted = bot._convert_messages_to_anthropic(messages)
    
    print("\nScenario 1 Result:")
    print(json.dumps(converted, indent=2))
    
    # Check that the first message is a USER message with text content
    assert converted[0]["role"] == "user"
    assert "Result of tool 123" in converted[0]["content"]
    assert isinstance(converted[0]["content"], str) or (isinstance(converted[0]["content"], list) and converted[0]["content"][0]["type"] == "text")
    
    print("✅ Scenario 1 Passed")

    # Scenario 2: Orphan Tool Result after User message
    messages_2 = [
        {
            "role": "user",
            "content": "Do something"
        },
        {
            "role": "tool",
            "tool_call_id": "call_456",
            "content": "Result of tool 456"
        }
    ]
    
    converted_2 = bot._convert_messages_to_anthropic(messages_2)
    
    print("\nScenario 2 Result:")
    print(json.dumps(converted_2, indent=2))
    
    # Check that the tool result was appended to the user message as text
    assert len(converted_2) == 1
    assert converted_2[0]["role"] == "user"
    assert "Result of tool 456" in str(converted_2[0]["content"])
    
    print("✅ Scenario 2 Passed")
    
    # Scenario 3: Valid Tool Result (Control Case)
    messages_3 = [
        {
            "role": "user",
            "content": "Run tool"
        },
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_789",
                    "type": "function",
                    "function": {"name": "test_tool", "arguments": "{}"}
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_789",
            "content": "Valid result"
        }
    ]
    
    converted_3 = bot._convert_messages_to_anthropic(messages_3)
    
    print("\nScenario 3 Result:")
    print(json.dumps(converted_3, indent=2))
    
    # Check structure: User -> Assistant (tool_use) -> User (tool_result)
    assert len(converted_3) == 3
    assert converted_3[1]["role"] == "assistant"
    assert converted_3[1]["content"][0]["type"] == "tool_use"
    assert converted_3[2]["role"] == "user"
    assert converted_3[2]["content"][0]["type"] == "tool_result"
    
    print("✅ Scenario 3 Passed")

if __name__ == "__main__":
    test_orphan_tool_handling()
