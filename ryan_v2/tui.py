"""
RYAN-V2: RyanRent Intelligent Agent - TUI
Built with Textual for a modern terminal interface.
"""
import asyncio
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, Markdown, Button, Label, LoadingIndicator, Select, Collapsible
from textual.binding import Binding
from textual.message import Message

# Import our V2 Agent
from .agent import RyanAgent
from .tools import list_tables
from .config import MODEL_IDS, DEFAULT_PROVIDER, AVAILABLE_MODELS

# Configure logging to write to file, NOT console (which breaks TUI)
import logging
logging.basicConfig(
    filename="ryan_v2.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)

class ThinkingProcess(Container):
    """Collapsible container for agent thoughts and tool logs."""
    
    def __init__(self):
        super().__init__()
        self.log_container = Vertical(classes="thinking-logs")
        self.collapsible = Collapsible(self.log_container, title="⚙️ Thinking Process...", collapsed=True)
        self.collapsible.classes = "thinking-collapsible"

    def compose(self) -> ComposeResult:
        yield self.collapsible

    def add_log(self, content: str):
        """Add a log entry to the thinking process."""
        # Clean up formatting
        content = content.replace("🔧 *Calling", "🔧 Executing")
        content = content.replace("🔧 *Tool Output:", "✅ Output:")
        
        # Style errors
        if "❌" in content or "⚠️" in content:
            classes = "log-error"
        else:
            classes = "log-info"
            
        self.log_container.mount(Label(content, classes=classes))
        
    def set_complete(self):
        self.collapsible.title = "✅ Process Completed"

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
        yield Label("🧠 Model", classes="sidebar-title")
        
        # Create select options from AVAILABLE_MODELS
        # Default to the first model in the list
        default_model = AVAILABLE_MODELS[0][1]
        yield Select(AVAILABLE_MODELS, value=default_model, allow_blank=False, id="model-select")
        
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
        background: #007acc; # Ryan Blue
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
        border-left: wide #007acc;
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
    
    /* Thinking Process Styling */
    .thinking-collapsible {
        background: #252526;
        border: solid #444;
        margin: 1 0;
        height: auto;
        padding: 0;
    }
    
    .thinking-logs {
        padding: 1;
        height: auto;
        background: #1e1e1e;
    }
    
    .log-info {
        color: #888;
    }
    
    .log-error {
        color: #ff5555;
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
        # Initialize default agent using first model
        self.agent = RyanAgent(provider=AVAILABLE_MODELS[0][1])
        
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

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle model selection change."""
        if event.select.id == "model-select":
            composite_value = str(event.value)
            self.agent = RyanAgent(provider=composite_value)
            
            # Extract display name logic if possible, or just formatted value
            if ":" in composite_value:
                provider_name = composite_value.split(":")[0]
                model_name = composite_value.split(":")[1]
                display_name = f"{provider_name.capitalize()} ({model_name})"
            else:
                display_name = composite_value
                
            self.notify(f"Switched to {display_name}")

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
        
        # 1. Show Loading Indicator
        loading = LoadingIndicator()
        await messages_area.mount(loading)
        
        # 2. Prepare Thinking Process
        thinking_process = ThinkingProcess()
        thinking_mounted = False # Don't mount until we have tool output
        
        try:
            # Iterate through agent chunks
            for response_chunk in self.agent.run(query):
                
                # Remove loading indicator on first chunk
                if loading:
                    await loading.remove()
                    loading = None
                
                # Analyze chunk type
                is_tool_call = response_chunk.startswith("🔧")
                is_error = "❌" in response_chunk or "⚠️" in response_chunk
                
                if is_tool_call or is_error:
                    # Mount thinking process if not yet active
                    if not thinking_mounted:
                        await messages_area.mount(thinking_process)
                        thinking_mounted = True
                        
                    thinking_process.add_log(response_chunk)
                else:
                    # Final Answer / Text
                    # Mark thinking as done if it was active
                    if thinking_mounted:
                        thinking_process.set_complete()
                        
                    # Stream final answer
                    await self.add_message("assistant", response_chunk)
                    
            # Cleanup if finished
            if loading:
                await loading.remove()
                
            if thinking_mounted:
                thinking_process.set_complete()
                
        except Exception as e:
            if loading: await loading.remove()
            await self.add_message("tool", f"❌ System Error: {str(e)}")

    async def add_message(self, role: str, content: str):
        """Add a message to the scroll area and scroll to bottom."""
        messages_area = self.query_one("#messages-area")
        await messages_area.mount(ChatMessage(role, content))
        messages_area.scroll_end(animate=True)
        
    def action_refresh_stats(self):
        self.query_one(DatabaseSidebar).update_stats()

if __name__ == "__main__":
    app = RyanApp()
    app.run()
