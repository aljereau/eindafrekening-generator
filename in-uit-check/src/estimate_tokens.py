import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

def estimate_tokens():
    # Initialize bot with dummy key
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'ryanrent_core.db')
    bot = RyanRentBot(api_key="dummy", db_path=db_path, provider="openai")
    
    # 1. System Prompt (including Schema)
    sys_prompt = bot._get_default_system_prompt()
    sys_chars = len(sys_prompt)
    sys_tokens = sys_chars / 4
    
    # 2. Tool Definitions
    tools_json = json.dumps(bot.tools)
    tools_chars = len(tools_json)
    tools_tokens = tools_chars / 4
    
    # 3. Empty Request Total
    total_base_tokens = sys_tokens + tools_tokens
    
    print(f"--- Token Usage Breakdown (Estimated) ---")
    print(f"1. System Prompt (Persona + Schema):")
    print(f"   - Characters: {sys_chars}")
    print(f"   - Tokens:     ~{int(sys_tokens)}")
    print(f"")
    print(f"2. Tool Definitions (18 tools):")
    print(f"   - Characters: {tools_chars}")
    print(f"   - Tokens:     ~{int(tools_tokens)}")
    print(f"")
    print(f"--- BASE COST PER REQUEST: ~{int(total_base_tokens)} tokens ---")
    print(f"")
    print(f"Note: This base cost is sent with EVERY message.")
    print(f"History and new user input are added on top of this.")

if __name__ == "__main__":
    estimate_tokens()
