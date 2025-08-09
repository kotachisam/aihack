from rich.console import Console
from rich.syntax import Syntax

console = Console()


def display_success_message() -> None:
    """Display analysis completion message."""
    console.print("✅ Analysis complete", style="green bold")


def display_code_syntax(code: str, language: str = "python") -> None:
    """Display code with syntax highlighting."""
    console.print(Syntax(code, language, theme="monokai"))
