from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Select, Label, Static

class Settings(Container):
    """Settings Screen for RyanRent Bot"""

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Global Settings", classes="page-header"),
            
            Container(
                Label("🧠 AI Model Selection", classes="section-header"),
                Static("Choose the brain that powers Ryan. Different models have different strengths.", classes="section-desc"),
                
                Select(
                    [
                        ("GPT-4o (Balanced & Fast)", "gpt-4o"),
                        ("O1-Preview (Deep Reasoning)", "o1-preview"),
                        ("O1-Mini (Fast Reasoning)", "o1-mini"),
                        ("GPT-4 Turbo (Legacy High-Perf)", "gpt-4-turbo"),
                        ("Claude 4.5 Sonnet (Latest)", "claude-sonnet-4-5-20250929"),
                        ("Claude 3.5 Sonnet (Creative & Safe)", "claude-3-5-sonnet-20240620"),
                        ("Claude 3 Opus (Maximum Intelligence)", "claude-3-opus-20240229"),
                        ("Gemini 3 Pro (Preview)", "gemini-3-pro-preview"),
                        ("Gemini 1.5 Pro (Google Standard)", "gemini-1.5-pro"),
                    ],
                    prompt="Select Model...",
                    value="gpt-4o",
                    id="model-selector",
                    allow_blank=False
                ),
                classes="settings-card"
            ),
            
            id="settings-page"
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle model change."""
        if event.select.id == "model-selector":
            if not getattr(self.app, "bot", None):
                self.notify("Bot not initialized.", severity="error")
                return
            
            new_model = event.value
            if new_model:
                res = self.app.bot.switch_model(new_model)
                
                if res.get("status") == "error":
                    self.notify(f"Error: {res.get('message')}", severity="error")
                else:
                    self.notify(f"Switched to {res['provider'].upper()}: {res['model']}")
