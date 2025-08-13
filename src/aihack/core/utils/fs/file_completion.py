"""Enhanced file completion engine with real-time @ detection and smart suggestions."""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .file_index import FileSystemIndex, get_file_index


class CompletionType(Enum):
    """Types of file completions."""

    NONE = "none"
    FILE_REFERENCE = "file_reference"
    DIRECTORY_SHORTCUT = "directory_shortcut"
    PATH_SEGMENT = "path_segment"


@dataclass
class FileMention:
    """Represents a file mention in the input."""

    start_pos: int
    end_pos: int
    full_text: str
    file_ref: str
    completion_type: CompletionType
    is_complete: bool = False


@dataclass
class CompletionContext:
    """Context for a file completion."""

    mention: FileMention
    current_segment: str
    parent_directory: str
    suggestions: List[Tuple[str, float]]
    selected_index: int = 0


@dataclass
class FileCompletionState:
    """Manages state for file completion across input changes."""

    input_text: str
    cursor_position: int
    mentions: List[FileMention]
    active_mention: Optional[FileMention]
    completion_contexts: Dict[int, CompletionContext]  # mention start_pos -> context


class FileCompletionEngine:
    """Enhanced file completion with real-time @ detection and smart suggestions."""

    def __init__(self) -> None:
        self.file_index: Optional[FileSystemIndex] = None
        self.directory_shortcuts = self._build_directory_shortcuts()

    async def initialize(self) -> None:
        """Initialize the completion engine."""
        self.file_index = await get_file_index()

    def _build_directory_shortcuts(self) -> Dict[str, str]:
        """Build common directory shortcuts based on project structure."""
        return {
            "cli": "src/aihack/cli/",
            "core": "src/aihack/core/",
            "models": "src/aihack/models/",
            "safety": "src/aihack/safety/",
            "tests": "tests/",
            "scripts": "scripts/",
            "docs": "docs/",
            "src": "src/",
            "utils": "src/aihack/core/utils/",
            "runners": "src/aihack/cli/runners/",
        }

    def parse_input(self, text: str, cursor_pos: int) -> FileCompletionState:
        """Parse input text and extract file mentions with cursor awareness."""
        mentions = []

        # Enhanced regex to find @ mentions with better context handling
        pattern = r"@([^\s@]*)"

        for match in re.finditer(pattern, text):
            start_pos = match.start()
            end_pos = match.end()
            full_text = match.group(0)  # includes @
            file_ref = match.group(1)  # excludes @

            # Determine completion type
            completion_type = self._determine_completion_type(file_ref)

            # Check if mention is complete (followed by space or at end)
            is_complete = (
                end_pos >= len(text)
                or text[end_pos].isspace()
                or text[end_pos] in ".,!?;:"
            )

            mention = FileMention(
                start_pos=start_pos,
                end_pos=end_pos,
                full_text=full_text,
                file_ref=file_ref,
                completion_type=completion_type,
                is_complete=is_complete,
            )

            mentions.append(mention)

        # Find active mention (one containing cursor)
        active_mention = None
        for mention in mentions:
            if mention.start_pos <= cursor_pos <= mention.end_pos:
                active_mention = mention
                break

        return FileCompletionState(
            input_text=text,
            cursor_position=cursor_pos,
            mentions=mentions,
            active_mention=active_mention,
            completion_contexts={},
        )

    def _determine_completion_type(self, file_ref: str) -> CompletionType:
        """Determine the type of completion needed."""
        if not file_ref:
            return CompletionType.FILE_REFERENCE

        # Check for directory shortcuts
        if file_ref.lower() in self.directory_shortcuts:
            return CompletionType.DIRECTORY_SHORTCUT

        # Check if it contains path separators
        if "/" in file_ref:
            return CompletionType.PATH_SEGMENT

        return CompletionType.FILE_REFERENCE

    async def get_suggestions(
        self, state: FileCompletionState, mention: FileMention, limit: int = 8
    ) -> List[Tuple[str, float]]:
        """Get suggestions for a file mention."""
        if not self.file_index:
            await self.initialize()

        file_ref = mention.file_ref
        suggestions = []

        if mention.completion_type == CompletionType.DIRECTORY_SHORTCUT:
            suggestions = await self._get_shortcut_suggestions(file_ref, limit)
        elif mention.completion_type == CompletionType.PATH_SEGMENT:
            suggestions = await self._get_path_segment_suggestions(file_ref, limit)
        else:
            suggestions = await self._get_file_reference_suggestions(file_ref, limit)

        return suggestions

    async def _get_shortcut_suggestions(
        self, file_ref: str, limit: int
    ) -> List[Tuple[str, float]]:
        """Get suggestions for directory shortcuts."""
        suggestions: List[Tuple[str, float]] = []
        file_ref_lower = file_ref.lower()

        if not self.file_index:
            return suggestions

        # Direct shortcut match
        if file_ref_lower in self.directory_shortcuts:
            target_dir = self.directory_shortcuts[file_ref_lower]
            files_in_dir = self.file_index.get_files_in_directory(
                target_dir.rstrip("/")
            )

            for file_path in files_in_dir[:limit]:
                suggestions.append((file_path, 1.0))

        else:
            # Fuzzy match against shortcut names
            for shortcut, target_dir in self.directory_shortcuts.items():
                if shortcut.startswith(file_ref_lower):
                    score = len(file_ref_lower) / len(shortcut)
                    suggestions.append((target_dir, score))

        return suggestions

    async def _get_path_segment_suggestions(
        self, file_ref: str, limit: int
    ) -> List[Tuple[str, float]]:
        """Get suggestions for path segments."""
        # Use fuzzy matching from file index
        if not self.file_index:
            return []
        return self.file_index.get_fuzzy_matches(file_ref, limit)

    async def _get_file_reference_suggestions(
        self, file_ref: str, limit: int
    ) -> List[Tuple[str, float]]:
        """Get suggestions for general file references."""
        if not self.file_index:
            return []

        if not file_ref:
            # Show top-level files and directories
            root_contents = self.file_index.get_directory_contents("")
            suggestions = [(path, 1.0) for path in root_contents[:limit]]
            return suggestions

        # Use fuzzy matching from file index
        return self.file_index.get_fuzzy_matches(file_ref, limit)

    async def update_completion_context(
        self, state: FileCompletionState, mention: FileMention
    ) -> CompletionContext:
        """Update or create completion context for a mention."""
        suggestions = await self.get_suggestions(state, mention)

        # Determine current segment and parent directory
        file_ref = mention.file_ref
        if "/" in file_ref:
            parts = file_ref.split("/")
            current_segment = parts[-1]
            parent_directory = "/".join(parts[:-1])
        else:
            current_segment = file_ref
            parent_directory = ""

        context = CompletionContext(
            mention=mention,
            current_segment=current_segment,
            parent_directory=parent_directory,
            suggestions=suggestions,
            selected_index=0,
        )

        state.completion_contexts[mention.start_pos] = context
        return context

    def advance_selection(self, context: CompletionContext, direction: int = 1) -> None:
        """Advance selection in completion context."""
        if not context.suggestions:
            return

        context.selected_index = (context.selected_index + direction) % len(
            context.suggestions
        )

    def get_selected_suggestion(self, context: CompletionContext) -> Optional[str]:
        """Get currently selected suggestion from context."""
        if not context.suggestions or context.selected_index >= len(
            context.suggestions
        ):
            return None

        return context.suggestions[context.selected_index][0]

    def apply_completion(
        self, state: FileCompletionState, context: CompletionContext, completion: str
    ) -> str:
        """Apply completion to input text."""
        mention = context.mention

        # Replace the file reference part with completion
        new_text = (
            state.input_text[: mention.start_pos + 1]
            + completion  # Keep @ symbol
            + state.input_text[mention.end_pos :]
        )

        return new_text

    def expand_path_segment(
        self, state: FileCompletionState, context: CompletionContext
    ) -> Optional[str]:
        """Expand current path segment incrementally."""
        if not context.suggestions:
            return None

        selected = self.get_selected_suggestion(context)
        if not selected:
            return None

        current_ref = context.mention.file_ref

        # If selected is a directory and we're not already in it, expand to it
        if selected.endswith("/") and not current_ref.endswith("/"):
            return selected

        # If current path is a prefix of selected, expand to next segment
        if selected.startswith(current_ref) and len(selected) > len(current_ref):
            # Find next '/' after current position
            remaining = selected[len(current_ref) :]
            if "/" in remaining:
                next_segment_end = remaining.index("/") + 1
                return current_ref + remaining[:next_segment_end]
            else:
                # No more segments, complete the file
                return selected

        return selected

    def get_display_suggestions(
        self, context: CompletionContext
    ) -> List[Dict[str, Any]]:
        """Get formatted suggestions for display."""
        display_suggestions = []

        for i, (path, score) in enumerate(context.suggestions):
            is_directory = path.endswith("/")
            display_name = path

            # Add appropriate icon
            icon = "📁" if is_directory else "📄"

            # Highlight selection
            is_selected = i == context.selected_index

            display_suggestions.append(
                {
                    "path": path,
                    "display_name": display_name,
                    "icon": icon,
                    "is_directory": is_directory,
                    "is_selected": is_selected,
                    "score": score,
                }
            )

        return display_suggestions
