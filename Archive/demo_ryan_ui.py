#!/usr/bin/env python3
"""Demo script to showcase the new RYAN chatbot UI"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich import box
from datetime import datetime
import time

console = Console()

def print_header():
    """Display a beautiful header for RYAN chatbot"""
    header_text = Text()
    header_text.append("╔═══════════════════════════════════════════════════════════╗\n", style="bold cyan")
    header_text.append("║                                                           ║\n", style="bold cyan")
    header_text.append("║              ", style="bold cyan")                         
    header_text.append("║          🏠 RYAN", style="bold white on blue")                 ║\n", style="bold cyan")
    header_text.append("║            - RyanRent Intelligence Bot                    ║\n", style="bold cyan")
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

def print_goodbye():
    """Display goodbye message"""
    goodbye_text = Text()
    goodbye_text.append("\n👋 ", style="bold yellow")
    goodbye_text.append("Thanks for chatting with RYAN!", style="bold white")
    goodbye_text.append("\n   See you next time! 🏠\n", style="cyan")
    console.print(goodbye_text)

# Demo the UI
console.clear()
print_header()

# Simulate a conversation
print_user_message("How many properties does RyanRent manage?")
console.print()
print_thinking()
time.sleep(1)
console.print("\033[A\033[K", end="")  # Clear thinking line

ryan_response = """Based on the database, RyanRent currently manages **12 active properties** across Amsterdam.

Here's a quick breakdown:
- **Studio apartments**: 5
- **1-bedroom**: 4
- **2-bedroom**: 3

All properties are fully occupied with an average occupancy rate of **98.5%**."""

print_ryan_message(ryan_response)

print_user_message("What's the total monthly revenue?")
console.print()
print_thinking()
time.sleep(1)
console.print("\033[A\033[K", end="")

ryan_response2 = """The total monthly revenue from all properties is **€18,450**.

This breaks down to:
- Average rent per property: €1,537.50
- Highest rent: €2,100 (2-bedroom in Jordaan)
- Lowest rent: €950 (Studio in Oost)"""

print_ryan_message(ryan_response2)

print_goodbye()
