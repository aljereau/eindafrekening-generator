import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.text import Text
from rich import box
from datetime import datetime
import questionary

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.bot import RyanRentBot

console = Console()

def print_header():
    """Display a beautiful header for RYAN chatbot"""
    header_text = Text()
    header_text.append("╔═══════════════════════════════════════════════════════════╗\n", style="bold cyan")
    header_text.append("║                                                           ║\n", style="bold cyan")
    header_text.append("║              ", style="bold cyan")
    header_text.append("🏠 RYAN", style="bold white on blue")
    header_text.append(" - RyanRent Intelligence Bot              ║\n", style="bold cyan")
    header_text.append("║                                                           ║\n", style="bold cyan")
    header_text.append("╚═══════════════════════════════════════════════════════════╝", style="bold cyan")
    
    console.print(header_text)
    console.print()
    
    # Info panel
    info_panel = Panel(
        "[cyan]💾 Database:[/cyan] [yellow]ryanrent_mock.db[/yellow]\n"
        "[cyan]🤖 Status:[/cyan] [green]Online & Ready[/green]\n"
        "[cyan]💡 Tip:[/cyan] Type [bold yellow]'quit'[/bold yellow] or [bold yellow]'exit'[/bold yellow] to end the conversation",
        title="[bold white]System Information[/bold white]",
        border_style="blue",
        box=box.ROUNDED
    )
    console.print(info_panel)
    console.print()

def print_user_message(message):
    """Display user message with nice formatting"""
    timestamp = datetime.now().strftime("%H:%M")
    user_panel = Panel(
        f"[white]{message}[/white]",
        title=f"[bold green]👤 You[/bold green] [dim]({timestamp})[/dim]",
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 1)
    )
    console.print(user_panel)

def print_ryan_message(message):
    """Display RYAN's response with nice formatting"""
    timestamp = datetime.now().strftime("%H:%M")
    
    # Render as markdown for better formatting
    md = Markdown(message)
    
    ryan_panel = Panel(
        md,
        title=f"[bold blue]🏠 RYAN[/bold blue] [dim]({timestamp})[/dim]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(0, 1)
    )
    console.print(ryan_panel)
    console.print()

def print_thinking():
    """Display thinking indicator"""
    console.print("[dim cyan]💭 RYAN is thinking...[/dim cyan]")

def print_error(error_msg):
    """Display error message"""
    error_panel = Panel(
        f"[red]{error_msg}[/red]",
        title="[bold red]❌ Error[/bold red]",
        border_style="red",
        box=box.ROUNDED
    )
    console.print(error_panel)

def print_goodbye():
    """Display goodbye message"""
    goodbye_text = Text()
    goodbye_text.append("\n👋 ", style="bold yellow")
    goodbye_text.append("Thanks for chatting with RYAN!", style="bold white")
    goodbye_text.append("\n   See you next time! 🏠\n", style="cyan")
    console.print(goodbye_text)

def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="RyanRent Chatbot")
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
    
    # Select key based on provider
    api_key = None
    if args.provider == "openai":
        api_key = openai_key
        if not api_key:
            print_error("'OPENAI_API_KEY' not found in .env")
            return
    elif args.provider == "anthropic":
        api_key = anthropic_key
        if not api_key:
            print_error("'ANTHROPIC_API_KEY' not found in .env")
            return
    elif args.provider == "ollama":
        api_key = "ollama"

    # Clear screen
    console.clear()
    print_header()
    
    # Interactive model selection if not provided via CLI
    if not args.model:
        # Fetch available Ollama models
        ollama_models = []
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        ollama_models.append(model_name)
        except Exception:
            pass
        
        # Build choices list with LATEST model IDs (Claude 4.5 series)
        choices = [
            questionary.Choice("Claude Sonnet 4.5 (Recommended - Latest)", value=("claude-sonnet-4-5-20250929", "anthropic")),
            questionary.Choice("Claude Opus 4.5 (Most Capable)", value=("claude-opus-4-5-20251101", "anthropic")),
            questionary.Choice("Claude Haiku 4.5 (Fastest & Cheapest)", value=("claude-haiku-4-5-20251001", "anthropic")),
            questionary.Separator("--- OpenAI ---"),
            questionary.Choice("GPT-4o", value=("gpt-4o", "openai")),
            questionary.Choice("GPT-4o Mini", value=("gpt-4o-mini", "openai")),
            questionary.Choice("o1-preview (Reasoning)", value=("o1-preview", "openai")),
        ]
        
        # Add Ollama models if available
        if ollama_models:
            choices.append(questionary.Separator("--- Local (Ollama) ---"))
            for model in ollama_models:
                choices.append(questionary.Choice(f"{model}", value=(model, "ollama")))
        
        # Add custom option
        choices.append(questionary.Separator("---"))
        choices.append(questionary.Choice("Custom (type model name)", value=("custom", "custom")))
        
        # Show interactive menu
        selection = questionary.select(
            "Select a model:",
            choices=choices,
            style=questionary.Style([
                ('qmark', 'fg:cyan bold'),
                ('question', 'bold'),
                ('answer', 'fg:green bold'),
                ('pointer', 'fg:yellow bold'),
                ('highlighted', 'fg:yellow bold'),
                ('selected', 'fg:green'),
                ('separator', 'fg:cyan'),
            ])
        ).ask()
        
        if selection:
            model_name, provider = selection
            
            if provider == "custom":
                custom_model = questionary.text("Enter model name:").ask()
                if custom_model:
                    args.model = custom_model
                    if custom_model.startswith("claude"):
                        args.provider = "anthropic"
                    elif custom_model.startswith("gpt") or custom_model.startswith("o1"):
                        args.provider = "openai"
                    elif ":" in custom_model:
                        args.provider = "ollama"
                else:
                    args.model = "claude-sonnet-4-5-20250929"
                    args.provider = "anthropic"
            else:
                args.model = model_name
                args.provider = provider
        else:
            args.model = "claude-sonnet-4-5-20250929"
            args.provider = "anthropic"
        
        # Update API key based on provider
        if args.provider == "anthropic":
            api_key = anthropic_key
        elif args.provider == "openai":
            api_key = openai_key
        elif args.provider == "ollama":
            api_key = "ollama"
        
        console.clear()
        print_header()
    
    console.print(f"[dim]Using Provider: {args.provider.upper()}[/dim]")
    console.print(f"[dim]Using Model: {args.model}[/dim]")
    console.print("")
    
    # Initialize Bot
    db_path = os.path.join(root_dir, "database", "ryanrent_mock.db")
    try:
        bot = RyanRentBot(api_key, db_path=db_path, provider=args.provider, model_name=args.model)
    except Exception as e:
        print_error(f"Failed to initialize bot: {e}")
        return
    
    # Main chat loop
    while True:
        try:
            user_input = Prompt.ask("[bold green]💬 Your message[/bold green]")
            
            if user_input.lower().strip() in ['quit', 'exit', 'bye', 'goodbye']:
                print_goodbye()
                break
            
            if not user_input.strip():
                continue
            
            print_user_message(user_input)
            console.print()
            print_thinking()
            
            response = bot.chat(user_input)
            
            console.print("\033[A\033[K", end="")
            print_ryan_message(response)
            
        except KeyboardInterrupt:
            console.print()
            print_goodbye()
            break
        except EOFError:
            console.print()
            print_goodbye()
            break
        except Exception as e:
            print_error(str(e))
            console.print()

if __name__ == "__main__":
    main()
