"""Runner function for the standalone 'letshack' session command."""

from aihack.cli.main import _show_splash_screen
from aihack.cli.session import SessionApp


def run() -> None:
    """Entry point function to run the interactive session app."""
    _show_splash_screen()
    import time

    time.sleep(1)  # Give user time to see splash screen
    app = SessionApp()
    app.run()
