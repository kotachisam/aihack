# ai_hack/cli/main.py
import asyncio
import os
import warnings

import click
import pyfiglet
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

from aihack.core.tasks import TaskRegistry
from aihack.models.local import OllamaModel

# Configure environment and warnings
os.environ.setdefault("PYTHONWARNINGS", "ignore::UserWarning:urllib3")
warnings.filterwarnings("ignore", message=".*urllib3.*OpenSSL.*")

console = Console()


def _show_splash_screen() -> None:
    """Displays the ASCII art splash screen."""
    ascii_art = pyfiglet.figlet_format("AI-Hack", font="slant")
    subtitle = "Your Privacy-First AI Coding Partner 🚀"
    tagline = "Type [bold green]ah session[/bold green] or [bold green]letshack[/bold green] to begin."
    message = f"[bold cyan]{ascii_art}[/bold cyan]\n[dim]{subtitle}[/dim]\n\n{tagline}"

    console.print(
        Panel(
            Align.center(message),
            border_style="magenta",
            padding=(1, 2),
            expand=True,
        )
    )


@click.group(invoke_without_command=True)
@click.help_option("-h", "--help")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """AI-Hack: Your Privacy-First AI Coding Partner 🚀"""
    if ctx.invoked_subcommand is None:
        _show_splash_screen()


@cli.command()
@click.argument("code_file", type=click.Path(exists=True))
@click.option(
    "-t",
    "--task",
    default=TaskRegistry.get_default_task(),
    help=f"Task to perform: {', '.join(TaskRegistry.get_all_task_names())}",
)
@click.option(
    "-m", "--model", default="local", help="Model to use: local, claude, gemini"
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "-p",
    "--privacy",
    type=click.Choice(["high", "balanced", "performance"]),
    default="balanced",
    help="Privacy level: high=local only, balanced=smart routing, performance=prefer cloud",
)
def hack(code_file: str, task: str, model: str, verbose: bool, privacy: str) -> None:
    """Quick AI-assisted code analysis and suggestions"""
    asyncio.run(_hack_async(code_file, task, model, verbose, privacy))


async def _hack_async(
    code_file: str, task: str, model: str, verbose: bool, privacy: str
) -> None:
    """Async implementation of hack command"""
    # Validate task
    if not TaskRegistry.is_valid_task(task):
        console.print(f"❌ Invalid task: {task}")
        console.print(f"Valid tasks: {', '.join(TaskRegistry.get_all_task_names())}")
        return

    with open(code_file, "r") as f:
        code = f.read()

    task_config = TaskRegistry.get_task_config(task)

    if verbose:
        console.print(f"🔍 {task_config.get('description', 'Processing')} {code_file}")
        lines = code.split("\n")
        console.print(f"📊 File stats: {len(lines)} lines, {len(code)} characters")
        console.print(f"🔒 Privacy level: {privacy}")
    else:
        console.print(f"🔍 Analyzing {code_file} ({task})...")

    # Privacy enforcement
    if privacy == "high":
        model = "local"
        if verbose:
            console.print("🔒 Privacy mode: forcing local processing")

    if model == "local":
        with console.status("[bold green]Connecting to local AI model...") as status:
            local_ai = OllamaModel()

            # Check if Ollama is available
            if not await local_ai.is_available():
                console.print(
                    "❌ Local model (Ollama) not available. Make sure it's running."
                )
                console.print("💡 Try: ollama serve")
                return

            status.update("[bold green]Analyzing code with CodeLlama...")

            if TaskRegistry.is_valid_task(task):
                response = await local_ai.code_review(code, task)
            else:
                response = await local_ai.analyze_code(code)

        console.print("\n🤖 [bold blue]AI Analysis:[/bold blue]")
        console.print(response)

    else:
        console.print(f"⚠️  Model '{model}' not yet implemented. Using local for now.")
        console.print("✅ Analysis complete!")


@cli.command("review")
@click.argument("code_file", type=click.Path(exists=True))
@click.option(
    "-m", "--model", default="local", help="Model to use: local, claude, gemini"
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-s", "--security", is_flag=True, help="Focus on security issues")
def review(code_file: str, model: str, verbose: bool, security: bool) -> None:
    """Code review with AI assistance (alias for hack --task review)"""
    task = "security" if security else "review"
    privacy = "high" if security else "balanced"
    asyncio.run(_hack_async(code_file, task, model, verbose, privacy))


@cli.command("status")
@click.option("-v", "--verbose", is_flag=True, help="Show detailed status")
@click.option("-a", "--all", "check_all", is_flag=True, help="Check all models")
def status(verbose: bool, check_all: bool) -> None:
    """Check AI-Hack and model status"""
    asyncio.run(_status_async(verbose, check_all))


async def _status_async(verbose: bool, check_all: bool) -> None:
    """Check system status"""
    console.print("🔍 Checking AI-Hack status...")

    # Check local model
    local_ai = OllamaModel()
    local_available = await local_ai.is_available()

    if local_available:
        console.print("✅ Local model (Ollama) is available")
        if verbose:
            health = await local_ai.health_check()
            console.print(f"   Model: {health.get('model', 'Unknown')}")
            console.print(f"   Response time: {health.get('response_time_ms', 0)}ms")
    else:
        console.print("❌ Local model (Ollama) not available")
        console.print("   Try: ollama serve")

    if check_all:
        console.print("⚠️  Cloud model checks not implemented yet")
        console.print("   Claude: Not configured")
        console.print("   Gemini: Not configured")


@cli.command("models")
@click.option("-v", "--verbose", is_flag=True, help="Show detailed model info")
def models(verbose: bool) -> None:
    """List available models and their capabilities"""
    console.print("🤖 Available Models:")
    console.print("   local   - Ollama models (CodeLlama, Mixtral, etc.)")
    console.print("   claude  - Anthropic Claude (not yet implemented)")
    console.print("   gemini  - Google Gemini (not yet implemented)")

    if verbose:
        console.print("\n📋 Task Support:")
        for task in TaskRegistry.get_all_task_names():
            config = TaskRegistry.get_task_config(task)
            console.print(
                f"   {task:<10} - {config.get('description', 'No description')}"
            )


@cli.command("session")
def session() -> None:
    """Start an interactive AI-Hack session."""
    from aihack.cli.session import SessionApp

    app = SessionApp()
    app.run()


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
