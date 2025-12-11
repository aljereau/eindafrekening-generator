from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Input, Static, Label, Markdown
from textual.message import Message

class ChatScreen(Container):
    """The Chat interface."""

    class NewMessage(Message):
        """Posted when the user sends a message."""
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="chat-container"):
            # We use a VerticalScroll to hold the messages
            yield VerticalScroll(id="chat-history")
            yield Input(placeholder="Type a message...", id="chat-input")

    async def on_mount(self) -> None:
        """Load history when screen, but wait for UI to be ready."""
        # Use call_later to avoid mounting before layout is fully ready?
        # Or just call it.
        self.load_history()

    def append_message(self, text: str, sender: str = "user") -> None:
        """Add a message to the chat history."""
        history = self.query_one("#chat-history")
        
        # Determine styling classes
        sender_class = "sender-user" if sender == "user" else "sender-bot"
        msg_class = "message-user" if sender == "user" else "message-bot"
        prefix = "👤 You" if sender == "user" else "🤖 RYAN"
        
        # Create a container for the formatted message
        msg_container = Container(classes=f"message-container {msg_class}")
        history.mount(msg_container)
        
        # Header (Sender Name)
        header = Label(f"{prefix}", classes=f"message-header {sender_class}")
        msg_container.mount(header)
        
        # Content - Using Markdown
        if text:
            md_widget = Markdown(text, classes="message-body")
            msg_container.mount(md_widget)
        
        # Scroll to bottom
        history.scroll_end(animate=False)
        
        # Save to Persistent Storage
        self.save_history(text, sender)

    def append_status(self, text: str, type: str = "info") -> None:
        """Add a status/log message to the chat (e.g. tool usage)."""
        history = self.query_one("#chat-history")
        
        # Create a small status line
        status_line = Label(f"🛠️ {text}", classes="status-message")
        if type == "error":
            status_line.styles.color = "red"
        elif type == "warning":
            status_line.styles.color = "yellow"
            
        history.mount(status_line)
        history.scroll_end(animate=False)

    def save_history(self, text: str, sender: str) -> None:
        """Save a message to JSON file."""
        import json
        import os
        
        try:
            history_file = os.path.join(os.path.dirname(__file__), "chat_history.json")
            data = []
            
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = []
            
            data.append({"sender": sender, "text": text, "timestamp": str(datetime.datetime.now())})
            
            # Limit history
            if len(data) > 50:
                data = data[-50:]
                
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            pass # Silent fail
            
    def load_history(self) -> None:
        """Load history from JSON file."""
        import json
        import os
        
        try:
            history_file = os.path.join(os.path.dirname(__file__), "chat_history.json")
            if not os.path.exists(history_file):
                return
                
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for msg in data:
                # We reuse styling logic but bypass saving to avoid recursion
                sender = msg.get("sender", "user")
                text = msg.get("text", "")
                
                history = self.query_one("#chat-history")
                
                # Determine styling classes
                sender_class = "sender-user" if sender == "user" else "sender-bot"
                msg_class = "message-user" if sender == "user" else "message-bot"
                prefix = "👤 You" if sender == "user" else "🤖 RYAN"
                
                msg_container = Container(classes=f"message-container {msg_class}")
                history.mount(msg_container)
                
                header = Label(f"{prefix}", classes=f"message-header {sender_class}")
                msg_container.mount(header)
                
                if text:
                    md_widget = Markdown(text, classes="message-body")
                    msg_container.mount(md_widget)
            
            history.scroll_end(animate=False)
            
        except Exception as e:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value.strip()
        if message:
            self.append_message(message, "user")
            event.input.value = ""
            self.post_message(self.NewMessage(message))
