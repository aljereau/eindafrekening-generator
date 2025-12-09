import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv
import questionary
from rich.console import Console

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot
from TUI.app import RyanRentApp

console = Console()

def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="RyanRent Chatbot (TUI)")
    parser.add_argument("--provider", choices=["openai", "anthropic", "ollama"], default="anthropic", help="AI Provider")
    parser.add_argument("--model", type=str, help="Model name")
    args = parser.parse_args()

    # Load .env from project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    env_path = os.path.join(root_dir, '.env')
    load_dotenv(env_path)
    
    # Load keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Select key
    api_key = None
    if args.provider == "openai":
        api_key = openai_key
    elif args.provider == "anthropic":
        api_key = anthropic_key
    elif args.provider == "ollama":
        api_key = "ollama"

    # Interactive model selection if needed (Simplified for clean startup)
    if not args.model and not api_key:
        # Fallback to simple selection if keys missing or just to be safe
        pass 

    # Default if not set
    if not args.model:
        args.model = "claude-sonnet-4-5-20250929" # Default high-end

    # Initialize Bot
    db_path = os.path.join(root_dir, "database", "ryanrent_mock.db")
    
    try:
        console.print("[green]Initializing RyanRent Bot...[/green]")
        bot = RyanRentBot(api_key, db_path=db_path, provider=args.provider, model_name=args.model)
        
        # Launch TUI
        app = RyanRentApp(bot=bot)
        app.run()
        
    except Exception as e:
        console.print(f"[bold red]Failed to start:[/bold red] {e}")
        return

if __name__ == "__main__":
    main()
