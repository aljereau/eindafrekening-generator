import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

def main():
    # Load .env from project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    env_path = os.path.join(root_dir, '.env')
    load_dotenv(env_path)
    
    api_key = os.getenv("anthropic-ryanrent-bot")
    if not api_key:
        # Fallback: try reading manually if dotenv fails on quotes/spaces
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if "anthropic-ryanrent-bot" in line:
                        # Parse: key = "value"
                        parts = line.split('=')
                        if len(parts) == 2:
                            api_key = parts[1].strip().strip('"').strip("'")
                            break
        except Exception as e:
            print(f"Error reading .env: {e}")

    if not api_key:
        print("❌ Error: 'anthropic-ryanrent-bot' not found in .env")
        return

    print("🤖 RyanRent Intelligence Bot (Mock Data Mode)")
    print("   Connected to: ryanrent_mock.db")
    print("   Type 'quit' to exit.\n")
    
    # Initialize Bot with Mock DB
    db_path = os.path.join(root_dir, "database", "ryanrent_mock.db")
    bot = RyanRentBot(api_key, db_path=db_path)
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            print("Bot: ... thinking ...")
            response = bot.chat(user_input)
            print(f"Bot: {response}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
