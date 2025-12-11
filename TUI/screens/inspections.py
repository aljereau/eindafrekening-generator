from textual.app import ComposeResult
from textual.widgets import Button, Static, Label
from textual.containers import Container

class Inspections(Container):
    """View for managing inspections."""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Inspections Manager", classes="header-title"),
            Button("View Upcoming Inspections", variant="primary", id="btn-view-inspections"),
            Button("Export to Excel", variant="warning", id="btn-export"),
            Static("Select an option to begin.", id="inspections-status"),
            id="inspections-container"
        )
