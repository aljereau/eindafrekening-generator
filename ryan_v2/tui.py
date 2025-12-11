"""
RYAN-V2: RyanRent Intelligent Agent - TUI
Built with Textual for a modern terminal interface.
"""
import asyncio
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, Markdown, Button, Label, LoadingIndicator
from textual.binding import Binding
from textual.message import Message

# Import our V2 Agent
from .agent import RyanAgent
from .tools import list_tables

# Configure logging to write to file, NOT console (which breaks TUI)
import logging
logging.basicConfig(
    filename="ryan_v2.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)

class ChatMessage(Container):
    """A single chat message bubble."""
    
    def __init__(self, role: str, content: str, is_tool: bool = False):
        super().__init__()
        self.role = role
        self.content = content
        self.is_tool = is_tool
        
        if role == "user":
            self.classes = "user-message"
            self.avatar = "👤 You"
        elif role == "assistant":
            self.classes = "assistant-message"
            self.avatar = "🤖 Ryan"
        else: # Tool info
            self.classes = "tool-message"
            self.avatar = "🔧 System"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="header"):
            yield Label(self.avatar, classes="avatar")
        yield Markdown(self.content)

class DatabaseSidebar(Container):
    """Sidebar showing database stats."""
    
    def __init__(self):
        super().__init__(classes="sidebar")
        
    def compose(self) -> ComposeResult:
        yield Label("📊 Database Monitor", classes="sidebar-title")
        yield Markdown("Loading stats...", id="db-stats")
        yield Button("Refresh Schema", id="refresh-db", variant="primary")
        
    def update_stats(self):
        """Fetch real DB stats using our tools."""
        try:
            # We use the list_tables tool which returns a markdown string
            stats = list_tables()
            # Remove the title and making it compact
            compact_stats = stats.replace("📊 **Available Tables:**", "").strip()
            self.query_one("#db-stats", Markdown).update(compact_stats)
        except Exception as e:
            self.query_one("#db-stats", Markdown).update(f"Error: {e}")

class RyanApp(App):
    """The main TUI Application."""
    
    CSS = """
    Screen {
        layout: horizontal;
        background: #1e1e1e;
    }
    
    .sidebar {
        dock: left;
        width: 30;
        background: #252526;
        border-right: solid #333;
        padding: 1;
    }
    
    .sidebar-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: #007acc;
        color: white;
        margin-bottom: 1;
    }
    
    #chat-container {
        width: 1fr;
        layout: vertical;
        padding: 0 1;
    }
    
    #messages-area {
        height: 1fr;
        padding: 1;
    }
    
    Input {
        dock: bottom;
        margin: 1;
        border: wide #007acc;
    }
    
    .user-message {
        background: #2b2b2b;
        margin: 1 0;
        padding: 0 1;
        border: solid #333;
        content-align: right middle;
        height: auto;
    }
    
    .assistant-message {
        background: #1e1e1e;
        margin: 1 0;
        padding: 0 1;
        border-left: wide #007acc; # Ryan Blue
        height: auto;
    }
    
    .tool-message {
        background: #222;
        color: #666;
        margin: 0 4;
        padding: 0 1;
        text-style: italic;
        border-left: wide #eba134; 
        height: auto;
    }
    
    .avatar {
        text-style: bold;
        width: 100%;
        color: #888;
        padding-bottom: 0;
    }
    """
    
    TITLE = "RyanRent Intelligent Agent (V2)"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "refresh_stats", "Refresh DB"),
    ]

    def __init__(self):
        super().__init__()
        self.agent = RyanAgent() # Initialize our V2 agent
        
    def compose(self) -> ComposeResult:
        # Sidebar
        yield DatabaseSidebar()
        
        # Main Chat Area
        with Container(id="chat-container"):
            yield Header()
            with ScrollableContainer(id="messages-area"):
                yield ChatMessage("assistant", "👋 Hallo! Ik ben Ryan V2. Ik heb toegang tot de live database.\n\nWaar kan ik mee helpen?")
            
            yield Input(placeholder="Stel je vraag over de huizen, contracten of cijfers...", id="user-input")
            yield Footer()

    def on_mount(self):
        """Called when app starts."""
        self.query_one(DatabaseSidebar).update_stats()
        self.query_one("#user-input").focus()

    async def on_input_submitted(self, message: Input.Submitted):
        """Handle user input."""
        user_query = message.value
        if not user_query:
            return
            
        # Clear input
        message.input.value = ""
        
        # Add user message to UI
        await self.add_message("user", user_query)
        
        # Run agent in background worker to keep UI responsive
        self.run_worker(self.process_agent_response(user_query))

    async def process_agent_response(self, query: str):
        """Run the agent loop and stream updates to UI."""
        messages_area = self.query_one("#messages-area")
        
        # Add a thinking indicator (optional, but good UX)
        # For now, we'll just stream the responses
        
        try:
            # We use the generator version of the agent logic
            # Note: run() is a generator that yields strings
            # Since ryan_v2.agent.run is synchronous generator, we iterate it directly
            # BUT we should wrap it in thread if it blocks, but let's try direct first.
            # Actually, network calls block. We need to run the generator in a thread.
            
            # Since our agent is sync, we'll just do it step by step
            # Ideally we'd make the agent async, but for this demo:
            
            for response_chunk in self.agent.run(query):
                # Check if it's a tool notification or final answer
                is_tool_call = response_chunk.startswith("🔧") or response_chunk.startswith("⚠️")
                role = "tool" if is_tool_call else "assistant"
                
                await self.add_message(role, response_chunk)
                
        except Exception as e:
            await self.add_message("tool", f"❌ Error: {str(e)}")

    async def add_message(self, role: str, content: str):
        """Add a message to the scroll area and scroll to bottom."""
        # Clean up tool messages slightly for UI
        if role == "tool":
            content = content.replace("🔧 *Calling", "🔧 Executing tool:")
            
        messages_area = self.query_one("#messages-area")
        await messages_area.mount(ChatMessage(role, content))
        messages_area.scroll_end(animate=True)
        
    def action_refresh_stats(self):
        self.query_one(DatabaseSidebar).update_stats()

if __name__ == "__main__":
    app = RyanApp()
    app.run()
