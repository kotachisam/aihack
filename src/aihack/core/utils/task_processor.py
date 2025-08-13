"""Task processing for structured AI task commands."""
import os
from typing import Any

from ..tasks import TaskRegistry
from .command_utils import extract_file_mentions
from .fs.file_utils import get_file_suggestions, resolve_file_path
from .session_state import SessionState


class TaskProcessor:
    """Processes structured task commands like /review, /analyze with file handling."""

    def __init__(self, model_manager: Any, state: SessionState) -> None:
        self.model_manager = model_manager
        self.state = state

    async def process_file_task(self, task: str, file_path: str) -> str:
        """Process a task command with a single file."""
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
            result = await self.model_manager.current_model.code_review(code, task)

            return f"🤖 **{config['description']}** for `{file_path}`:\n\n{result}\n"

        except Exception as e:
            return f"❌ Error processing {file_path}: {str(e)}\n"

    async def process_task_with_file_mentions(self, task: str, message: str) -> str:
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
                result = await self.model_manager.current_model.code_review(
                    content, task
                )
                return f"🤖 **{config['description']}** for `{file_path}`:\n\n{result}\n"
            except Exception as e:
                return f"❌ Error processing {file_path}: {str(e)}\n"

        # Handle multiple files - concatenate results
        results = []
        for file_path, content in file_contents:
            try:
                result = await self.model_manager.current_model.code_review(
                    content, task
                )
                results.append(f"**{os.path.basename(file_path)}:**\n{result}")
            except Exception as e:
                results.append(f"**{os.path.basename(file_path)}:** ❌ Error: {str(e)}")

        file_list = ", ".join([os.path.basename(fp) for fp, _ in file_contents])
        return (
            f"🤖 **{config['description']}** for {file_list}:\n\n"
            + "\n\n---\n\n".join(results)
            + "\n"
        )

    def validate_task(self, task: str) -> bool:
        """Validate that a task is supported."""
        return TaskRegistry.is_valid_task(task)

    def get_task_error_message(self, task: str) -> str:
        """Get error message for invalid task."""
        valid_tasks = ", ".join(TaskRegistry.get_all_task_names())
        return f"❌ Unknown task '{task}'. Valid tasks: {valid_tasks}\n"
