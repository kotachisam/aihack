"""Session service for handling AI interactions in the TUI."""
from typing import Any, Dict, List

from .context import BasicCLIContextManager
from .utils.chat_processor import ChatProcessor
from .utils.command_utils import build_command_registry, parse_task_command
from .utils.model_manager import ModelManager
from .utils.session_state import SessionState
from .utils.system_handler import SystemCommandHandler
from .utils.task_processor import TaskProcessor


class SessionService:
    """Service layer for handling AI interactions in interactive sessions."""

    def __init__(self) -> None:
        self.state = SessionState()
        self.model_manager = ModelManager()

        # Initialize context management
        self.context_manager = BasicCLIContextManager()

        self.task_processor = TaskProcessor(self.model_manager, self.state)
        self.chat_processor = ChatProcessor(
            self.model_manager, self.state, self.context_manager
        )
        self.system_handler = SystemCommandHandler(self.model_manager, self.state)
        self.slash_commands = build_command_registry()

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the service and ensure model availability."""
        # Start context session
        session_id = self.context_manager.start_session()

        result = await self.model_manager.initialize()
        result["session_id"] = session_id
        return result

    async def process_chat(self, message: str) -> str:
        """Handle free-form chat with AI."""
        # Check for special syntax
        if message.startswith(">"):
            return await self.system_handler.process_shell_command(message[1:].strip())

        # Check for file mentions anywhere in the message
        if "@" in message:
            return await self.chat_processor.process_file_mention(message)

        # Regular chat
        return await self.chat_processor.process_regular_chat(message)

    async def process_task_command(self, command: str) -> str:
        """Handle structured task commands like /review, /analyze with flexible file syntax."""
        # Parse command using utility function
        task, rest_of_command = parse_task_command(command)
        if not task:
            return await self.system_handler.handle_built_in_command("help")

        # Handle built-in system commands first
        if self.system_handler.is_built_in_command(task):
            return await self.system_handler.handle_built_in_command(
                task, rest_of_command
            )

        # Handle AI tasks
        if not self.model_manager.is_model_available():
            return "❌ AI not available. Please start Ollama: ollama serve\n"

        # Validate task first
        if not self.task_processor.validate_task(task):
            return self.task_processor.get_task_error_message(task)

        # Handle flexible file syntax
        if rest_of_command:
            # Check if it contains @ file mentions
            if "@" in rest_of_command:
                # Use the file mention processing with task context
                return await self.task_processor.process_task_with_file_mentions(
                    task, rest_of_command
                )
            else:
                # Legacy direct file path (backward compatibility)
                file_path = rest_of_command.split()[0]  # Take first word as file path
                return await self.task_processor.process_file_task(task, file_path)
        else:
            return f"❌ Task '{task}' requires a file. Usage: /{task} @filename or /{task} filename\n"

    # Delegate methods for backwards compatibility
    def get_slash_command_suggestions(
        self, partial_command: str = ""
    ) -> List[Dict[str, str]]:
        """Get slash command suggestions filtered by partial input."""
        return self.system_handler.get_slash_command_suggestions(partial_command)

    def get_recent_files_suggestions(self) -> List[str]:
        """Get recently used files for @ suggestions."""
        return self.state.get_recent_files_suggestions()

    def add_recent_file(self, file_path: str) -> None:
        """Track a recently accessed file."""
        self.state.add_recent_file(file_path)

    def get_contextual_bash_suggestions(self, context: str = "") -> List[str]:
        """Get intelligent bash command suggestions based on recent history and context."""
        return self.system_handler.get_contextual_bash_suggestions(context)

    def set_detail_mode(self, detailed: bool) -> None:
        """Set file content detail mode."""
        self.state.set_detail_mode(detailed)

    def get_current_model_name(self) -> str:
        """Get the name of the currently active model for styling."""
        return self.model_manager.get_current_model_name()

    def add_shell_command_to_context(self, command: str) -> None:
        """Add shell command to history for AI context."""
        self.state.add_shell_command_to_context(command)

    def switch_model_with_context(self, new_model: str) -> Dict[str, Any]:
        """Switch model with context optimization."""

        # Switch in model manager first
        switch_result = self.model_manager.switch_model(new_model)

        # Optimize context for new model
        optimized = self.context_manager.switch_model(new_model)

        return {
            "message": switch_result,
            "context_optimization": {
                "original_length": optimized.original_length,
                "optimized_length": optimized.optimized_length,
                "compression_ratio": f"{optimized.compression_ratio:.2f}",
                "quality_score": f"{optimized.quality_score:.2f}",
            },
        }

    def get_context_info(self) -> Dict[str, Any]:
        """Get current context information."""
        return self.context_manager.get_session_info()

    def add_message_to_context(self, role: str, content: str) -> None:
        """Add message to context for persistence."""
        current_model = self.model_manager.get_current_model_name()
        self.context_manager.add_message(role, content, current_model)
