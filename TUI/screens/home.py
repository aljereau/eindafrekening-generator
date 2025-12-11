from textual.app import ComposeResult
from textual.widgets import Button, Static, Label
from textual.containers import Container, Horizontal

class Home(Container):
    """The main dashboard view."""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("RYANRENT BOT V1.0 - ONLINE", id="welcome-message"),
            Horizontal(
                Static("System Status:\n[green]ALL SYSTEMS GO[/]", classes="stat-box"),
                Static("Pending Inspections:\n[yellow]3[/]", classes="stat-box"),
                Static("Recent Settlements:\n[blue]5 Generated[/]", classes="stat-box"),
                id="stats-container"
            ),
            id="home-content"
        )
