from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, ContentSwitcher
from textual.containers import Container, Horizontal
from textual.worker import Worker, WorkerState
from TUI.screens.home import Home
from TUI.screens.generator import Generator
from TUI.screens.inspections import Inspections
from TUI.screens.chat import ChatScreen
from TUI.screens.settings import Settings
import asyncio

class RyanRentApp(App):
    """The RyanRent Bot Terminal Application."""
    
    CSS_PATH = "styles.tcss"
    
    BINDINGS = [
        ("d", "switch_tab('home')", "Dashboard"),
        ("g", "switch_tab('generator')", "Generator"),
        ("i", "switch_tab('inspections')", "Inspections"),
        ("c", "switch_tab('chat')", "Chat"),
        ("s", "switch_tab('settings')", "Settings"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, bot=None):
        super().__init__()
        self.bot = bot

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Container(
            # Sidebar
            Container(
                Button("Dashboard", id="btn-home", variant="primary"),
                Button("Chat", id="btn-chat"),
                Button("Generator", id="btn-generator"),
                Button("Inspections", id="btn-inspections"),
                Button("Settings", id="btn-settings"),
                id="sidebar",
                classes="sidebar"
            ),
            # Main Content Area
            Container(
                ContentSwitcher(
                    Home(id="home"),
                    ChatScreen(id="chat"),
                    Generator(id="generator"),
                    Inspections(id="inspections"),
                    Settings(id="settings"),
                    initial="chat" if self.bot else "home",
                    id="content-switcher"
                ),
                id="main-content-area"
            ),
            classes="main-layout"
        )
        yield Footer()

    def action_switch_tab(self, tab: str) -> None:
        """Switch the current tab."""
        self.query_one(ContentSwitcher).current = tab

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar button presses."""
        if event.button.id == "btn-home":
            self.action_switch_tab("home")
        elif event.button.id == "btn-chat":
            self.action_switch_tab("chat")
        elif event.button.id == "btn-generator":
            self.action_switch_tab("generator")
        elif event.button.id == "btn-inspections":
            self.action_switch_tab("inspections")
        elif event.button.id == "btn-settings":
            self.action_switch_tab("settings")

    async def on_chat_screen_new_message(self, message: ChatScreen.NewMessage) -> None:
        """Handle new message from ChatScreen."""
        chat_screen = self.query_one(ChatScreen)
        user_text = message.text
        
        if not self.bot:
            chat_screen.append_message("Bot is offline or not configured.", "bot")
            return

        # Show thinking
        # (Optional: Add a spinner or temp message)
        
        # Run bot response in a worker to avoid blocking UI
        self.run_worker(self.get_bot_response(user_text, chat_screen), exclusive=True)

    async def get_bot_response(self, text: str, chat_screen: ChatScreen) -> None:
        """Async wrapper for bot.chat() which might be synchronous."""
        
        def status_callback(msg: str, type: str = "info"):
            # Update UI from the worker thread safely
            self.call_from_thread(chat_screen.append_status, msg, type)

        # Run bot chat in thread with callback
        response = await asyncio.to_thread(self.bot.chat, text, status_callback)
        chat_screen.append_message(response, "bot")

if __name__ == "__main__":
    app = RyanRentApp()
    app.run()
