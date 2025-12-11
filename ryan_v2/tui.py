"""
RYAN-V2: RyanRent Intelligent Agent - TUI
Built with Textual for a modern terminal interface.
"""
import asyncio
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, Markdown, Button, Label, LoadingIndicator, Select, Collapsible

# ... (imports remain)

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
            style = "color: #ff5555;"
        else:
            style = "color: #888;"
            
        self.log_container.mount(Label(content, style=style))
        
    def set_complete(self):
        self.collapsible.title = "✅ Process Completed"

# ... (RyanApp class)

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
    
    .avatar {
        text-style: bold;
        width: 100%;
        color: #888;
        padding-bottom: 0;
    }
    """

    # ... (__init__ remains)

    # ... (compose remains)
    
    # ... (on_mount remains)

    # ... (on_select_changed remains)

    # ... (on_input_submitted remains)

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
