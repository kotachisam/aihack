"""System command handler for status, directory listing, and built-in commands."""
import os
from typing import Any, Dict, List

from .command_utils import (
    get_contextual_bash_suggestions,
    get_help_message,
    get_slash_command_suggestions,
)
from .session_state import SessionState
from .shell_utils import execute_shell_command, format_shell_output


class SystemCommandHandler:
    """Handles system commands like status, directory listing, and shell execution."""

    def __init__(self, model_manager: Any, state: SessionState) -> None:
        self.model_manager = model_manager
        self.state = state

    async def handle_built_in_command(
        self, task: str, rest_of_command: str = ""
    ) -> str:
        """Handle built-in system commands."""
        if task in ["help", "h"]:
            return get_help_message(self.state.detail_mode)

        if task in ["exit", "quit", "q"]:
            return "/exit"  # Special marker for app to handle

        if task == "status":
            return (
                str(await self.model_manager.get_status())
                + f"📁 Working directory: {os.getcwd()}\n"
            )

        if task in ["api", "providers"]:
            return str(await self.model_manager.get_api_status())

        if task in ["ls", "dir"]:
            return await self._list_directory(
                rest_of_command if rest_of_command else "."
            )

        if task == "pwd":
            return f"📁 {os.getcwd()}\n"

        if task == "clear":
            return "/clear"  # Special marker for app to handle

        if task in ["claude", "gemini", "local", "ollama"]:
            return str(await self.model_manager.switch_model(task))

        return ""  # Command not handled by this handler

    async def _list_directory(self, path: str) -> str:
        """List directory contents."""
        try:
            if not os.path.exists(path):
                return f"❌ Path not found: {path}\n"

            if os.path.isfile(path):
                stat = os.stat(path)
                return f"📄 {path} ({stat.st_size} bytes)\n"

            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    stat = os.stat(item_path)
                    items.append(f"📄 {item} ({stat.st_size} bytes)")

            return f"📁 **Contents of {path}:**\n" + "\n".join(items) + "\n"

        except Exception as e:
            return f"❌ Error listing {path}: {str(e)}\n"

    async def process_shell_command(self, command: str) -> str:
        """Execute shell command and store in conversational context."""
        # Store command in context for AI models to see
        self.state.add_shell_command_to_context(command)

        # Use utility function for safe shell execution
        result = await execute_shell_command(command, timeout=10.0)
        return format_shell_output(result, command)

    def get_slash_command_suggestions(
        self, partial_command: str = ""
    ) -> List[Dict[str, str]]:
        """Get slash command suggestions filtered by partial input."""
        return get_slash_command_suggestions(partial_command)

    def get_contextual_bash_suggestions(self, context: str = "") -> List[str]:
        """Get intelligent bash command suggestions based on recent history and context."""
        return get_contextual_bash_suggestions(
            self.state.shell_command_history, context
        )

    def is_built_in_command(self, task: str) -> bool:
        """Check if a task is a built-in system command."""
        built_in_commands = {
            "help",
            "h",
            "exit",
            "quit",
            "q",
            "status",
            "api",
            "providers",
            "ls",
            "dir",
            "pwd",
            "clear",
            "claude",
            "gemini",
            "local",
            "ollama",
        }
        return task in built_in_commands
