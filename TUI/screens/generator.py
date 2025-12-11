from textual.app import ComposeResult
from textual.widgets import Button, Static, Label
from textual.containers import Container, VerticalScroll

class Generator(Container):
    """View for the Eindafrekening Generator."""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Settlement Generator", classes="header-title"),
            Button("Generate All (Batch)", variant="primary", id="btn-batch"),
            Button("Generate Single Client", variant="success", id="btn-single"),
            VerticalScroll(
                Static("Waiting for command...", id="generator-logs"),
            ),
            id="generator-container"
        )
