"""Session service for handling AI interactions in the TUI."""
import asyncio
import os
import subprocess
from typing import Any, Dict, List, Union

from ..config import Settings
from ..models.claude import ClaudeModel
from ..models.gemini import GeminiModel
from ..models.local import OllamaModel
from .tasks import TaskRegistry
from .utils.command_utils import (
    build_command_registry,
    extract_file_mentions,
    get_contextual_bash_suggestions,
    get_help_message,
    get_slash_command_suggestions,
    parse_task_command,
)
from .utils.fs.file_utils import (
    format_file_content,
    get_file_suggestions,
    resolve_file_path,
)
from .utils.session_state import SessionState
from .utils.shell_utils import execute_shell_command, format_shell_output


class SessionService:
    """Service layer for handling AI interactions in interactive sessions."""

    def __init__(self) -> None:
        self.settings = Settings()
        self.local_model = OllamaModel()
        self.model_available = False

        # Initialize cloud models if API keys are available
        self.claude_model = None
        self.gemini_model = None

        if self.settings.claude_api_key:
            self.claude_model = ClaudeModel(self.settings.claude_api_key)

        if self.settings.google_api_key:
            self.gemini_model = GeminiModel(self.settings.google_api_key)

        self._cloud_providers: Dict[str, Dict[str, Any]] = {
            "claude": {
                "name": "Claude (Anthropic)",
                "env_var": "CLAUDE_API_KEY",
                "model": self.claude_model,
            },
            "gemini": {
                "name": "Gemini (Google)",
                "env_var": "GOOGLE_API_KEY",
                "model": self.gemini_model,
            },
        }
        self.state = SessionState()
        self.slash_commands = build_command_registry()

        # Default to local model, but allow cloud model selection
        self.current_model: Union[
            OllamaModel, ClaudeModel, GeminiModel
        ] = self.local_model
        self.current_model_name = "local"

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the service and ensure model availability."""
        # First check if Ollama is already running
        self.model_available = await self.local_model.is_available()

        if not self.model_available:
            # Try to start Ollama automatically
            startup_result = await self._auto_start_ollama()
            if startup_result:
                # Wait longer for Ollama to fully initialize and load model
                for i in range(10):  # Try for up to 10 seconds
                    await asyncio.sleep(1)
                    self.model_available = await self.local_model.is_available()
                    if self.model_available:
                        break

        if self.model_available:
            health = await self.local_model.health_check()
            return {
                "available": True,
                "message": "🤖 CodeLlama connected! Ready to help with your code.\n",
                "model": health.get("model", "Unknown"),
                "response_time_ms": health.get("response_time_ms", 0),
            }
        else:
            return {
                "available": True,  # Still show as available for fallback
                "message": "⚙️ Ollama service starting... This may take a moment.\n",
                "suggestion": "💡 Try your first command - Ollama will auto-connect. Cloud providers available via /api.\n",
            }

    async def process_chat(self, message: str) -> str:
        """Handle free-form chat with AI."""
        # Check for special syntax
        if message.startswith(">"):
            return await self._process_shell_command(message[1:].strip())

        # Check for file mentions anywhere in the message
        if "@" in message:
            return await self._process_file_mention(message)

        if not self.model_available and self.current_model == self.local_model:
            return "❌ Local AI not available. Please start Ollama: ollama serve\n"

        try:
            response = await self.current_model.generate(message)
            return f"{response}\n"
        except Exception as e:
            return f"❌ Error: {str(e)}\n"

    async def process_task_command(self, command: str) -> str:
        """Handle structured task commands like /review, /analyze with flexible file syntax."""
        # Parse command using utility function
        task, rest_of_command = parse_task_command(command)
        if not task:
            return get_help_message(self.state.detail_mode)

        # Handle built-in commands
        if task in ["help", "h"]:
            return get_help_message(self.state.detail_mode)

        if task in ["exit", "quit", "q"]:
            return "/exit"  # Special marker for app to handle

        if task == "status":
            return await self._get_status()

        if task in ["api", "providers"]:
            return await self._get_api_status()

        if task in ["ls", "dir"]:
            return await self._list_directory(
                rest_of_command if rest_of_command else "."
            )

        if task == "pwd":
            return f"📁 {os.getcwd()}\n"

        if task == "clear":
            return "/clear"  # Special marker for app to handle

        if task in ["claude", "gemini", "local", "ollama"]:
            return await self._switch_model(task)

        # Handle AI tasks
        if not self.model_available:
            return "❌ AI not available. Please start Ollama: ollama serve\n"

        # Validate task first
        if not TaskRegistry.is_valid_task(task):
            valid_tasks = ", ".join(TaskRegistry.get_all_task_names())
            return f"❌ Unknown task '{task}'. Valid tasks: {valid_tasks}\n"

        # Handle flexible file syntax
        if rest_of_command:
            # Check if it contains @ file mentions
            if "@" in rest_of_command:
                # Use the file mention processing with task context
                return await self._process_task_with_file_mentions(
                    task, rest_of_command
                )
            else:
                # Legacy direct file path (backward compatibility)
                file_path = rest_of_command.split()[0]  # Take first word as file path
                return await self._process_file_task(task, file_path)
        else:
            return f"❌ Task '{task}' requires a file. Usage: /{task} @filename or /{task} filename\n"

    async def _process_file_task(self, task: str, file_path: str) -> str:
        """Process a task command with a file."""
        # Check if file exists
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"

        # Validate task
        if not TaskRegistry.is_valid_task(task):
            valid_tasks = ", ".join(TaskRegistry.get_all_task_names())
            return f"❌ Unknown task '{task}'. Valid tasks: {valid_tasks}"

        try:
            # Read file
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Process with AI
            config = TaskRegistry.get_task_config(task)
            result = await self.current_model.code_review(code, task)

            return f"🤖 **{config['description']}** for `{file_path}`:\n\n{result}\n"

        except Exception as e:
            return f"❌ Error processing {file_path}: {str(e)}\n"

    async def _process_task_with_file_mentions(self, task: str, message: str) -> str:
        """Process a task command that includes @ file mentions and optional additional instructions."""
        # Extract file paths from @ mentions using utility function
        matches = extract_file_mentions(message)

        if not matches:
            return f"❌ No files found in '{task}' command. Use @filename to specify files.\n"

        # Process each file mention with smart resolution
        file_contents = []
        processed_files = []

        for file_ref in matches:
            resolved_path = resolve_file_path(file_ref)

            if resolved_path and os.path.exists(resolved_path):
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Track recently accessed file
                    self.state.add_recent_file(resolved_path)
                    processed_files.append(resolved_path)
                    file_contents.append((resolved_path, content))

                except Exception as e:
                    return f"❌ Error reading {resolved_path}: {str(e)}\n"
            else:
                # Show what we tried to find
                suggestions = get_file_suggestions(file_ref)
                if suggestions:
                    suggestion_text = ", ".join(suggestions[:3])
                    return f"❌ File not found: {file_ref}\n💡 Did you mean: {suggestion_text}?\n"
                else:
                    return f"❌ File not found: {file_ref}\n"

        # Get task configuration
        config = TaskRegistry.get_task_config(task)

        # Process with AI - for now, handle one file at a time (most common case)
        if len(file_contents) == 1:
            file_path, content = file_contents[0]
            try:
                result = await self.current_model.code_review(content, task)
                return f"🤖 **{config['description']}** for `{file_path}`:\n\n{result}\n"
            except Exception as e:
                return f"❌ Error processing {file_path}: {str(e)}\n"

        # Handle multiple files - concatenate results
        results = []
        for file_path, content in file_contents:
            try:
                result = await self.current_model.code_review(content, task)
                results.append(f"**{os.path.basename(file_path)}:**\n{result}")
            except Exception as e:
                results.append(f"**{os.path.basename(file_path)}:** ❌ Error: {str(e)}")

        file_list = ", ".join([os.path.basename(fp) for fp, _ in file_contents])
        return (
            f"🤖 **{config['description']}** for {file_list}:\n\n"
            + "\n\n---\n\n".join(results)
            + "\n"
        )

    async def _auto_start_ollama(self) -> bool:
        """Attempt to auto-start Ollama service."""
        try:
            # Check if ollama is installed
            result = subprocess.run(
                ["which", "ollama"], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return False  # Ollama not installed

            # Try to start Ollama in the background
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )

            return True

        except Exception:
            return False

    async def _get_api_status(self) -> str:
        """Get status of all available API providers."""
        status_lines = ["🌐 **API Provider Status:**\n"]

        # Local model status
        if self.model_available:
            health = await self.local_model.health_check()
            status_lines.append(
                f"✅ **Local**: Ollama ({health.get('model', 'Unknown')}) - {health.get('response_time_ms', 0)}ms"
            )
        else:
            status_lines.append("⚙️ **Local**: Ollama (starting up...)")

        # Check cloud providers
        for provider_id, provider_info in self._cloud_providers.items():
            env_var = str(provider_info["env_var"])
            name = str(provider_info["name"])
            model = provider_info["model"]

            if model is not None:
                status_lines.append(f"🔑 **Cloud**: {name} (API key configured)")
            else:
                status_lines.append(f"❌ **Cloud**: {name} (no API key - set {env_var})")

        status_lines.append("\n💡 **Tips:**")
        status_lines.append("- Local models are private and free")
        status_lines.append("- Cloud models are faster but require API keys")
        status_lines.append("- Set environment variables for cloud access")

        return "\n".join(status_lines) + "\n"

    async def _process_shell_command(self, command: str) -> str:
        """Execute shell command and store in conversational context."""
        # Store command in context for AI models to see
        self.state.add_shell_command_to_context(command)

        # Use utility function for safe shell execution
        result = await execute_shell_command(command, timeout=10.0)
        return format_shell_output(result, command)

    async def _process_file_mention(self, message: str) -> str:
        """Handle @ file mentions in messages with smart file resolution."""
        # Extract file paths from @ mentions
        matches = extract_file_mentions(message)

        if not matches:
            # Fall back to regular chat
            return await self._regular_chat(message)

        # Process each file mention with smart resolution
        file_contents = []
        for file_ref in matches:
            resolved_path = resolve_file_path(file_ref)

            if resolved_path and os.path.exists(resolved_path):
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    formatted_content = format_file_content(
                        resolved_path, content, self.state.detail_mode
                    )
                    file_contents.append(formatted_content)
                    # Track recently accessed file
                    self.state.add_recent_file(resolved_path)
                except Exception as e:
                    file_contents.append(f"❌ Error reading {resolved_path}: {str(e)}")
            else:
                # Show what we tried to find
                suggestions = get_file_suggestions(file_ref)
                if suggestions:
                    suggestion_text = ", ".join(suggestions[:3])
                    file_contents.append(
                        f"❌ File not found: {file_ref}\n💡 Did you mean: {suggestion_text}?"
                    )
                else:
                    file_contents.append(f"❌ File not found: {file_ref}")

        # Create enhanced message with actual file names
        enhanced_message = message
        processed_files = []

        for i, file_ref in enumerate(matches):
            resolved_path = resolve_file_path(file_ref)
            if resolved_path:
                filename = os.path.basename(resolved_path)
                enhanced_message = enhanced_message.replace(
                    f"@{file_ref}", f"[{filename}]"
                )
                processed_files.append(filename)
            else:
                enhanced_message = enhanced_message.replace(
                    f"@{file_ref}", f"[{file_ref}]"
                )

        context = "\n\n".join(file_contents)
        full_prompt = f"Context from mentioned files:\n{context}\n\nUser message: {enhanced_message}"

        if not self.model_available:
            return f"{context}\n\n❌ AI not available to process your message. Please start Ollama: ollama serve\n"

        try:
            response = await self.current_model.generate(full_prompt)
            return f"{response}\n"
        except Exception as e:
            return f"{context}\n\n❌ Error: {str(e)}\n"

    async def _regular_chat(self, message: str) -> str:
        """Handle regular chat without special syntax."""
        if not self.model_available:
            return "❌ AI not available. Please start Ollama: ollama serve\n"

        try:
            response = await self.current_model.generate(message)
            return f"{response}\n"
        except Exception as e:
            return f"❌ Error: {str(e)}\n"

    async def _get_status(self) -> str:
        """Get detailed system status."""
        if not self.model_available:
            return "❌ AI Model unavailable. Please start Ollama: ollama serve\n"

        health = await self.local_model.health_check()
        if health["available"]:
            return f"✅ AI Model: {health['model']} (Response time: {health.get('response_time_ms', 0)}ms)\n📁 Working directory: {os.getcwd()}\n"
        else:
            return f"❌ AI Model unavailable: {health.get('error', 'Unknown error')}\n"

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

    def get_slash_command_suggestions(
        self, partial_command: str = ""
    ) -> List[Dict[str, str]]:
        """Get slash command suggestions filtered by partial input."""
        return get_slash_command_suggestions(partial_command)

    def get_recent_files_suggestions(self) -> List[str]:
        """Get recently used files for @ suggestions."""
        return self.state.get_recent_files_suggestions()

    def add_recent_file(self, file_path: str) -> None:
        """Track a recently accessed file."""
        self.state.add_recent_file(file_path)

    def get_contextual_bash_suggestions(self, context: str = "") -> List[str]:
        """Get intelligent bash command suggestions based on recent history and context."""
        return get_contextual_bash_suggestions(
            self.state.shell_command_history, context
        )

    def set_detail_mode(self, detailed: bool) -> None:
        """Set file content detail mode."""
        self.state.set_detail_mode(detailed)

    def get_current_model_name(self) -> str:
        """Get the name of the currently active model for styling."""
        return self.current_model_name

    def add_shell_command_to_context(self, command: str) -> None:
        """Add shell command to history for AI context."""
        self.state.add_shell_command_to_context(command)

    async def _switch_model(self, model_name: str) -> str:
        """Switch to a different AI model."""
        if model_name in ["local", "ollama"]:
            self.current_model = self.local_model
            self.current_model_name = "local"
            return "🤖 Switched to Local model (Ollama)\n"

        elif model_name == "claude":
            if self.claude_model is not None:
                self.current_model = self.claude_model
                self.current_model_name = "claude"
                return "🧠 Switched to Claude (Anthropic)\n"
            else:
                return "❌ Claude not available. Please set CLAUDE_API_KEY in your .env file\n"

        elif model_name == "gemini":
            if self.gemini_model is not None:
                self.current_model = self.gemini_model
                self.current_model_name = "gemini"
                return "✨ Switched to Gemini (Google)\n"
            else:
                return "❌ Gemini not available. Please set GOOGLE_API_KEY in your .env file\n"

        return f"❌ Unknown model '{model_name}'. Available: local, claude, gemini\n"
