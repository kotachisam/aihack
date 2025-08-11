"""Chat processing for file mentions and AI chat coordination."""
import os
from typing import Any

from .command_utils import extract_file_mentions
from .file_utils import format_file_content, get_file_suggestions, resolve_file_path
from .session_state import SessionState


class ChatProcessor:
    """Processes chat messages with file mentions and AI coordination."""

    def __init__(self, model_manager: Any, state: SessionState) -> None:
        self.model_manager = model_manager
        self.state = state

    async def process_file_mention(self, message: str) -> str:
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

        if not self.model_manager.is_model_available():
            return f"{context}\n\n❌ AI not available to process your message. Please start Ollama: ollama serve\n"

        try:
            response = await self.model_manager.current_model.generate(full_prompt)
            return f"{response}\n"
        except Exception as e:
            return f"{context}\n\n❌ Error: {str(e)}\n"

    async def _regular_chat(self, message: str) -> str:
        """Handle regular chat without special syntax."""
        if not self.model_manager.is_model_available():
            return "❌ AI not available. Please start Ollama: ollama serve\n"

        try:
            response = await self.model_manager.current_model.generate(message)
            return f"{response}\n"
        except Exception as e:
            return f"❌ Error: {str(e)}\n"

    async def process_regular_chat(self, message: str) -> str:
        """Process regular chat message without file mentions."""
        return await self._regular_chat(message)
