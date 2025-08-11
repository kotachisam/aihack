"""Pure utility functions for command processing and help text generation."""
import re
from typing import Dict, List, Tuple

from ..tasks import TaskRegistry


def parse_task_command(command: str) -> Tuple[str, str]:
    """Parse a task command into task name and arguments.

    Args:
        command: Full command string starting with '/'

    Returns:
        Tuple of (task_name, rest_of_command)
    """
    # Parse command - keep the original command for @ file processing
    parts = command[1:].split(None, 1)  # Split into task and rest
    if not parts:
        return "", ""

    task = parts[0].lower()
    rest_of_command = parts[1] if len(parts) > 1 else ""

    return task, rest_of_command


def extract_file_mentions(message: str) -> List[str]:
    """Extract file paths from @ mentions in a message.

    Args:
        message: Message potentially containing @file mentions

    Returns:
        List of file references from @ mentions
    """
    file_pattern = r"@([^\s]+)"
    return re.findall(file_pattern, message)


def build_command_registry() -> Dict[str, Dict[str, str]]:
    """Build registry of available slash commands with descriptions.

    Returns:
        Dictionary mapping command names to their descriptions and categories
    """
    commands = {
        "help": {
            "description": "Show all available commands and syntax",
            "category": "System",
        },
        "status": {
            "description": "Check AI model status and working directory",
            "category": "System",
        },
        "api": {
            "description": "Show available cloud providers and API configuration",
            "category": "System",
        },
        "pwd": {"description": "Show current working directory", "category": "System"},
        "ls": {"description": "List directory contents [path]", "category": "System"},
        "clear": {"description": "Clear the session log", "category": "System"},
        "exit": {"description": "Exit session", "category": "System"},
        "quit": {"description": "Exit session", "category": "System"},
        "q": {"description": "Exit session", "category": "System"},
        "claude": {
            "description": "Switch to Claude (Anthropic) model",
            "category": "Models",
        },
        "gemini": {
            "description": "Switch to Gemini (Google) model",
            "category": "Models",
        },
        "local": {
            "description": "Switch to Local (Ollama) model",
            "category": "Models",
        },
        "ollama": {
            "description": "Switch to Local (Ollama) model",
            "category": "Models",
        },
    }

    # Add task commands
    for task in TaskRegistry.get_all_task_names():
        config = TaskRegistry.get_task_config(task)
        commands[task] = {
            "description": f"{config['description']} @file",
            "category": "AI Tasks",
        }

    return commands


def get_slash_command_suggestions(partial_command: str = "") -> List[Dict[str, str]]:
    """Get slash command suggestions filtered by partial input.

    Args:
        partial_command: Partial command to filter by

    Returns:
        List of command dictionaries with command, description, and category
    """
    slash_commands = build_command_registry()

    if not partial_command:
        # Show all commands grouped by category
        suggestions = []
        for cmd, info in slash_commands.items():
            suggestions.append(
                {
                    "command": cmd,
                    "description": info["description"],
                    "category": info["category"],
                }
            )
        return sorted(suggestions, key=lambda x: (x["category"], x["command"]))

    # Filter commands that start with partial input
    filtered = []
    partial_lower = partial_command.lower()
    for cmd, info in slash_commands.items():
        if cmd.startswith(partial_lower):
            filtered.append(
                {
                    "command": cmd,
                    "description": info["description"],
                    "category": info["category"],
                }
            )

    return sorted(filtered, key=lambda x: x["command"])


def get_help_message(detail_mode: bool = False) -> str:
    """Get help message for available commands.

    Args:
        detail_mode: Current file content detail mode setting

    Returns:
        Formatted help message string
    """
    valid_tasks = TaskRegistry.get_all_task_names()
    task_list = "\n".join(
        [
            f"  /{task} @file - {TaskRegistry.get_task_config(task)['description']}"
            for task in valid_tasks
        ]
    )

    return f"""🤖 **AI-Hack Session Commands:**

**File Analysis:**
{task_list}

**System Commands:**
  /status - Check AI model status and working directory
  /api - Show available cloud providers and API configuration
  /pwd - Show current working directory
  /ls [path] - List directory contents
  /clear - Clear the session log
  /help - Show this help message
  /exit, /quit, /q - Exit session

**Special Syntax:**
  @filename - Reference files in chat (e.g., "Explain @main.py")
  > command - Execute shell commands (e.g., "> ls -la")
  ⚠️  WARNING: Avoid long-running commands (they will freeze the terminal)

**File Content Modes:**
  Ctrl+R - Toggle between Summary (first 10 lines) and Full content
  Current mode: {"Detailed" if detail_mode else "Summary"}

**Chat Mode:**
Just type any message (no prefix) for free-form chat with CodeLlama!

**Safe Shell Commands:**
  > git status
  > ls -la
  > cat filename.txt
  > python --version

**Unsafe Commands (avoid):**
  > ollama serve (long-running)
  > python script.py (if script waits for input)
  > vim file.txt (interactive editors)

**Examples:**
  /review @myfile.py
  /analyze @src/main.py what are the security concerns?
  /security @auth.py check for vulnerabilities
  @config.py what does this file do?
  > git log --oneline -5
  How do I optimize this function?
"""


def get_contextual_bash_suggestions(
    command_history: List[str], context: str = ""
) -> List[str]:
    """Get intelligent bash command suggestions based on recent history and context.

    Args:
        command_history: Recent shell command history
        context: Additional context for suggestions

    Returns:
        List of suggested bash commands
    """
    suggestions = []

    # Base on recent shell command patterns
    recent_patterns = _analyze_recent_commands(command_history)
    suggestions.extend(recent_patterns)

    # Common commands that are always useful
    common_commands = [
        "git status",
        "git add .",
        "git commit -m ''",
        "git diff",
        "ls -la",
        "pwd",
        "history",
        "cat ",
    ]
    suggestions.extend(common_commands)

    # Context-aware suggestions (but don't restrict)
    if "git" in context.lower():
        suggestions.extend(
            [
                "git branch",
                "git log --oneline -10",
                "git push",
                "git pull",
                "git checkout ",
                "git merge ",
            ]
        )

    # Remove duplicates and return
    return list(dict.fromkeys(suggestions))[:10]  # Top 10 suggestions


def _analyze_recent_commands(command_history: List[str]) -> List[str]:
    """Analyze recent commands to suggest logical next steps.

    Args:
        command_history: List of recent shell commands

    Returns:
        List of suggested follow-up commands
    """
    if not command_history:
        return []

    suggestions = []
    last_few = command_history[-5:]  # Look at last 5 commands

    for cmd in last_few:
        if cmd.startswith("git add"):
            suggestions.append("git commit -m ''")
        elif cmd.startswith("git commit"):
            suggestions.append("git push")
        elif "cd " in cmd:
            suggestions.append("ls -la")
            suggestions.append("pwd")

    return suggestions[:3]  # Top 3 contextual suggestions
