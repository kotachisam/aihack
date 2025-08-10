"""Interactive session mode for AI-Hack."""
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Input, Static


class SessionApp(App):
    """An interactive TUI session for AI-Hack."""

    CSS_PATH = "session.css"

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with VerticalScroll(id="content-log"):
            yield Static("Welcome to your AI-Hack session!", id="welcome")
        with Horizontal(id="input-container"):
            yield Static(">", id="prompt-icon")
            yield Input(placeholder="Type your command...", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.query_one(Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user command input."""
        command = event.value.strip()
        log = self.query_one("#content-log")
        input_widget = self.query_one(Input)

        if command.lower() in ("/exit", "/quit"):
            self.exit()
            return

        # Echo the command to the log
        log.mount(Static(f"> {command}"))
        input_widget.clear()

        # TODO: Process the command
        # For now, just echo a response
        log.mount(Static(f"Processing: {command}..."))
        log.scroll_end()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark  # type: ignore[has-type]


if __name__ == "__main__":
    app = SessionApp()
    app.run()
