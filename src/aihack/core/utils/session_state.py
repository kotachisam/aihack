"""Session state management for tracking files, history, and settings."""
from typing import List


class SessionState:
    """Manages session state including recent files, command history, and settings."""

    def __init__(self) -> None:
        self.detail_mode: bool = False  # False = summary, True = full content
        self.recent_files: List[str] = []  # Track recently accessed files
        self.shell_command_history: List[
            str
        ] = []  # Track shell commands for AI context

    def set_detail_mode(self, detailed: bool) -> None:
        """Set file content detail mode.

        Args:
            detailed: True for detailed mode, False for summary mode
        """
        self.detail_mode = detailed

    def add_recent_file(self, file_path: str) -> None:
        """Track a recently accessed file.

        Args:
            file_path: Path to the file that was accessed
        """
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:10]  # Keep last 10

    def add_shell_command_to_context(self, command: str) -> None:
        """Add shell command to history for AI context.

        Args:
            command: Shell command that was executed
        """
        self.shell_command_history.append(command)
        # Keep last 20 commands for context
        self.shell_command_history = self.shell_command_history[-20:]

    def get_recent_files_suggestions(self) -> List[str]:
        """Get recently used files for @ suggestions.

        Returns:
            List of recent file paths, or scanned directory files if none
        """
        # Return recent files, or scan current directory if none
        if self.recent_files:
            return self.recent_files[:8]

        # Import here to avoid circular imports
        from .fs.file_utils import get_all_file_suggestions

        return get_all_file_suggestions()[:12]
