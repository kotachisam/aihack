"""Interactive session mode for AI-Hack."""
import asyncio
from typing import Any, Dict, List, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import Click, Key
from textual.widgets import Header, Input, Label, ListItem, ListView, Static

from ..core.session_service import SessionService
from ..core.utils.fs.file_completion import FileCompletionEngine, FileCompletionState
from ..core.utils.fs.file_utils import get_file_suggestions
from ..core.utils.fs.smart_completion import AdvancedFileCompletion


class StreamingText(Static):
    """A widget that displays text with streaming animation."""

    def __init__(self, content: str, *args: Any, **kwargs: Any) -> None:
        super().__init__("", *args, **kwargs)
        self.full_content = content
        self.current_content = ""
        self.streaming = False
        self.scroll_container: Optional[Any] = None

    def set_scroll_container(self, container: Any) -> None:
        """Set the container to auto-scroll during streaming."""
        self.scroll_container = container

    async def start_streaming(self, speed: float = 0.02) -> None:
        """Start the streaming animation."""
        if self.streaming:
            return

        self.streaming = True
        self.current_content = ""

        for i, char in enumerate(self.full_content):
            if not self.streaming:  # Allow interruption
                break

            self.current_content += char
            self.update(self.current_content)

            # Only auto-scroll if user is already at the bottom (not manually scrolled up)
            if (
                self.scroll_container is not None and i % 10 == 0
            ):  # Every 10 chars to avoid too frequent scrolling
                # Check if user is at or near the bottom before auto-scrolling
                if self._is_user_at_bottom():
                    self.scroll_container.scroll_end(animate=False)

            # Vary speed based on character type for more natural feel
            if char in ".,!?":
                await asyncio.sleep(speed * 3)  # Pause at punctuation
            elif char == " ":
                await asyncio.sleep(speed * 0.5)  # Faster through spaces
            else:
                await asyncio.sleep(speed)

        # Final scroll only if user was following along (at bottom)
        if self.scroll_container is not None and self._is_user_at_bottom():
            self.scroll_container.scroll_end(animate=False)

        self.streaming = False

    def _is_user_at_bottom(self) -> bool:
        """Check if the user is currently scrolled to the bottom (or close to it)."""
        if not self.scroll_container:
            return True

        try:
            # Consider "at bottom" if within 2 lines of the actual bottom
            current_scroll = self.scroll_container.scroll_y
            max_scroll = self.scroll_container.max_scroll_y
            return bool(current_scroll >= max_scroll - 2)
        except (AttributeError, TypeError):
            # If we can't determine scroll position, assume at bottom
            return True

    def stop_streaming(self) -> None:
        """Stop streaming and show full content immediately."""
        self.streaming = False
        self.current_content = self.full_content
        self.update(self.current_content)


class SessionApp(App):
    """An interactive TUI session for AI-Hack."""

    CSS_PATH = "session.css"
    ENABLE_COMMAND_PALETTE = False  # Disable built-in command palette

    BINDINGS = [
        ("ctrl+c", "cancel_or_quit", "Cancel/Quit"),
        ("escape", "cancel_or_quit", "Cancel/Quit"),
        ("ctrl+r", "toggle_detail_mode", "Toggle Detail Mode"),
        ("ctrl+m", "cycle_model", "Cycle AI Model"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.service = SessionService()
        self.suggestions_visible = False
        self.current_suggestions: List[str] = []
        self.current_suggestion_type = (
            ""  # Track what type of suggestions we're showing
        )
        self.selected_suggestion_index = 0  # Track which suggestion is selected
        self.detail_mode = False  # False = summary, True = full content
        self.last_cancel_time = (
            0.0  # Track time of last cancel for double-tap detection
        )
        self.scroll_momentum = 0.0  # Track scroll momentum for graduated scrolling
        self.last_scroll_time = 0.0
        self.command_history: List[str] = []  # Track command history
        self.history_index = -1  # Current position in history (-1 = not browsing)
        self.current_streaming_widget: Optional[
            StreamingText
        ] = None  # Track active streaming for interruption
        self.is_processing = False  # Track if we're processing a command
        self.current_task: Optional[
            asyncio.Task[str]
        ] = None  # Track current AI task for cancellation

        # Enhanced file completion
        self.completion_engine = FileCompletionEngine()
        self.advanced_completion = AdvancedFileCompletion()
        self.completion_state: Optional[FileCompletionState] = None
        self.completion_initialized = False

        # Performance optimizations
        self._last_completion_text = ""
        self._completion_cache: Dict[str, List] = {}
        self._last_completion_time = 0.0

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with VerticalScroll(id="content-log"):
            yield Static("Welcome to your AI-Hack session!", id="welcome")
        yield ListView(id="suggestions-list", classes="hidden")
        yield Static("", id="quit-hint", classes="hidden")
        yield Static("", id="status-banner", classes="hidden")
        with Horizontal(id="input-container"):
            yield Static(">", id="prompt-icon")
            yield Input(placeholder="Type your command...", id="command-input")

    async def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.query_one(Input).focus()

        # Initialize AI service
        status = await self.service.initialize()
        log = self.query_one("#content-log")

        log.mount(Static(status["message"], classes="system-message"))
        if not status["available"] and "suggestion" in status:
            log.mount(Static(status["suggestion"], classes="system-message"))

        # Initialize enhanced file completion
        try:
            await self.completion_engine.initialize()
            await self.advanced_completion.initialize()
            self.completion_initialized = True
        except Exception as e:
            log.mount(
                Static(
                    f"⚠️ File completion init warning: {str(e)}",
                    classes="system-message",
                )
            )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user command input."""
        command = event.value.strip()
        log = self.query_one("#content-log")
        input_widget = self.query_one(Input)

        if not command:
            return

        if command.lower() in ("/exit", "/quit", "/q"):
            self.exit()
            return

        # Add to command history
        if command not in self.command_history:
            self.command_history.append(command)
            # Keep last 50 commands
            self.command_history = self.command_history[-50:]
        self.history_index = -1  # Reset history browsing

        # Echo the command to the log
        log.mount(Static(f"> {command}", classes="user-message"))
        input_widget.clear()

        # Show loading indicator
        loading_message = Static("🤖 Thinking...", classes="loading-message")
        log.mount(loading_message)
        log.scroll_end()

        # Ensure input stays focused and mark as processing
        input_widget.focus()
        self.is_processing = True

        # Process command through service layer
        try:
            if command.startswith("/"):
                task_coroutine = self.service.process_task_command(command)
            else:
                task_coroutine = self.service.process_chat(command)

            # Store the task so we can cancel it
            self.current_task = asyncio.create_task(task_coroutine)
            response = await self.current_task

            # Remove loading message
            loading_message.remove()

            # Handle special responses
            if response == "/exit":
                self.exit()
                return
            elif response == "/clear":
                # Clear all messages except welcome
                for widget in log.children[1:]:  # Keep welcome message
                    widget.remove()
                return

            # Show streaming response for AI-generated content
            if (
                response.strip()
                and not response.startswith("❌")
                and not response.startswith("✅")
            ):
                # Get model-specific CSS class
                model_name = self.service.get_current_model_name()
                css_class = f"ai-response-{model_name}"

                # Create streaming text widget for AI responses
                streaming_widget = StreamingText(response, classes=css_class)
                streaming_widget.set_scroll_container(
                    log
                )  # Enable auto-scroll during streaming
                self.current_streaming_widget = (
                    streaming_widget  # Track for interruption
                )
                log.mount(streaming_widget)
                # Start streaming animation
                asyncio.create_task(streaming_widget.start_streaming(speed=0.015))
            else:
                # Show non-AI responses immediately (errors, confirmations, etc.)
                model_name = self.service.get_current_model_name()
                css_class = f"ai-response-{model_name}"
                log.mount(Static(response, classes=css_class))

        except asyncio.CancelledError:
            loading_message.remove()
            # Don't add error message for cancelled tasks - user intentionally cancelled
        except Exception as e:
            loading_message.remove()
            log.mount(Static(f"❌ Error: {str(e)}", classes="error-message"))
        finally:
            # Clear processing state
            self.is_processing = False
            self.current_streaming_widget = None
            self.current_task = None

        log.scroll_end()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes to update visual indicators and show suggestions."""
        prompt_icon = self.query_one("#prompt-icon", Static)
        current_value = event.value
        input_widget = self.query_one("#command-input", Input)
        status_banner = self.query_one("#status-banner", Static)

        # Reset history browsing when user starts typing
        if self.history_index != -1 and hasattr(event, "input"):
            # Check if this change was from user typing (not from history navigation)
            if event.input and event.input.cursor_position == len(current_value):
                self.history_index = -1

        # Handle different types of suggestions - check for @ anywhere in input first
        cursor_pos = getattr(input_widget, "cursor_position", len(current_value))

        # Enhanced @ detection - check anywhere in input
        if "@" in current_value and self.completion_initialized:
            await self._handle_enhanced_file_completion(current_value, cursor_pos)
        elif current_value.startswith("/"):
            # Slash command suggestions
            command_part = current_value[1:]  # Remove the /
            await self._show_slash_suggestions(command_part)
        elif current_value.startswith("@"):
            # Fallback to basic file mention suggestions for backward compatibility
            if len(current_value) > 1:
                await self._show_file_suggestions(current_value)
            else:
                # Show recent files when just @ is typed
                await self._show_recent_files_suggestions()
        elif current_value.startswith(">"):
            # Bash command suggestions
            command_part = current_value[1:].strip()
            await self._show_bash_suggestions(command_part)
        elif current_value.startswith("#"):
            # Memory/context suggestions (future feature)
            await self._show_memory_suggestions()
        else:
            # Hide suggestions for regular chat
            if self.suggestions_visible:
                await self._hide_suggestions()

        if current_value.startswith(">"):
            # Shell command mode
            prompt_icon.update("🔧")
            input_widget.placeholder = "Shell command..."
            status_banner.update(
                "🔧 > Shell Commands - Execute system commands safely • ↑↓ navigate • Tab/Enter select • Esc cancel"
            )
            status_banner.set_class(False, "hidden")
            status_banner.set_class(True, "shell-mode")
        elif current_value.startswith("@"):
            # File mention mode
            prompt_icon.update("📄")
            input_widget.placeholder = "File mention..."
            status_banner.update(
                "📄 @ File Reference - Include files/dirs in chat • ↑↓ navigate • Tab/Enter select • Esc cancel"
            )
            status_banner.set_class(False, "hidden")
            status_banner.set_class(True, "file-mode")
        elif current_value.startswith("/"):
            # Slash command mode
            prompt_icon.update("⚡")
            input_widget.placeholder = "Slash command..."
            status_banner.update(
                "⚡ / Slash Commands - AI tasks & system commands • ↑↓ navigate • Tab/Enter select • Esc cancel"
            )
            status_banner.set_class(False, "hidden")
            status_banner.set_class(True, "command-mode")
        elif current_value.startswith("#"):
            # Memory/context mode (future feature)
            prompt_icon.update("🧠")
            input_widget.placeholder = "Memory command..."
            status_banner.update(
                "🧠 # Memory Mode - Save/load context, bridge AI models • ↑↓ navigate • Tab/Enter select"
            )
            status_banner.set_class(False, "hidden")
            status_banner.set_class(True, "memory-mode")
        else:
            # Regular chat mode - show current model
            model_name = self.service.get_current_model_name()
            model_icons = {"local": "🤖", "claude": "🧠", "gemini": "✨"}
            prompt_icon.update(model_icons.get(model_name, ">"))
            input_widget.placeholder = f"Chat with {model_name.title()}..."
            status_banner.set_class(True, "hidden")
            status_banner.set_class(False, "shell-mode")
            status_banner.set_class(False, "file-mode")
            status_banner.set_class(False, "command-mode")
            status_banner.set_class(False, "memory-mode")

    async def _handle_enhanced_file_completion(
        self, current_value: str, cursor_pos: int
    ) -> None:
        """Handle enhanced file completion with mid-prompt @ detection."""
        try:
            # Performance optimization: avoid repeated processing
            current_time = asyncio.get_event_loop().time()
            if (
                current_value == self._last_completion_text
                and current_time - self._last_completion_time < 0.1
            ):
                return

            self._last_completion_text = current_value
            self._last_completion_time = current_time

            # Parse input for file mentions
            self.completion_state = self.completion_engine.parse_input(
                current_value, cursor_pos
            )

            # If there's an active mention at cursor, show suggestions
            if self.completion_state.active_mention:
                mention = self.completion_state.active_mention

                # Check cache first
                cache_key = f"{mention.file_ref}:{mention.completion_type.value}"
                if cache_key in self._completion_cache:
                    suggestions = self._completion_cache[cache_key]
                else:
                    # Get suggestions using advanced completion
                    suggestions = await self.advanced_completion.get_smart_suggestions(
                        mention.file_ref, limit=8
                    )
                    # Cache for 5 seconds
                    self._completion_cache[cache_key] = suggestions
                    # Simple cache cleanup - keep only last 20 entries
                    if len(self._completion_cache) > 20:
                        oldest_key = next(iter(self._completion_cache))
                        del self._completion_cache[oldest_key]

                if suggestions:
                    # Update completion context
                    await self.completion_engine.update_completion_context(
                        self.completion_state, mention
                    )

                    # Show enhanced suggestions
                    await self._show_enhanced_file_suggestions(suggestions, mention)
                else:
                    # Fallback to basic suggestions
                    await self._show_file_suggestions(current_value)
            else:
                # No active mention, hide suggestions
                if self.suggestions_visible:
                    await self._hide_suggestions()

        except Exception:
            # Fallback to basic file suggestions on any error
            if current_value.startswith("@"):
                await self._show_file_suggestions(current_value)

    async def _show_enhanced_file_suggestions(
        self, suggestions: List[Dict[str, Any]], mention: Any
    ) -> None:
        """Show enhanced file suggestions with smart formatting."""
        if not suggestions:
            return

        suggestions_list = self.query_one("#suggestions-list", ListView)
        suggestions_list.clear()

        # Add category header
        suggestions_list.append(
            ListItem(Label("─── Smart File Suggestions ───"), classes="category-header")
        )

        # Add suggestions with enhanced formatting
        display_suggestions = []
        for suggestion in suggestions:
            path = suggestion["path"]
            icon = suggestion["icon"]
            suggestion_type = suggestion.get("suggestion_type", "match")

            # Create display text with context
            if suggestion_type == "directory_mapped":
                display_text = f"{icon} {path}"
            elif suggestion_type == "exact_match":
                display_text = f"{icon} {path}"
            else:
                display_text = f"{icon} {path}"

            suggestions_list.append(ListItem(Label(display_text)))
            display_suggestions.append(path)

        # Update state
        self.current_suggestions = display_suggestions
        self.current_suggestion_type = "enhanced_files"
        self.selected_suggestion_index = 0

        # Show suggestions
        suggestions_list.set_class(False, "hidden")
        self.suggestions_visible = True
        await self._update_suggestion_highlight()

    async def _show_file_suggestions(self, current_value: str) -> None:
        """Show basic file suggestions (fallback method)."""
        # Extract the partial file reference after @
        parts = current_value.split("@")
        if len(parts) > 1:  # Make sure there's at least one @ character
            try:
                file_ref = (
                    parts[-1].split()[0] if parts[-1] else ""
                )  # Get the file reference part
                # Show suggestions immediately, even for empty string
                if file_ref:
                    # Get filtered suggestions based on what's typed
                    suggestions = get_file_suggestions(file_ref)
                else:
                    # Show all available files/dirs when nothing is typed yet
                    suggestions = self.service.get_recent_files_suggestions()

                if suggestions:
                    suggestions_list = self.query_one("#suggestions-list", ListView)
                    suggestions_list.clear()

                    # Add header to distinguish from enhanced suggestions
                    suggestions_list.append(
                        ListItem(
                            Label("─── File Suggestions ───"), classes="category-header"
                        )
                    )

                    for suggestion in suggestions[:8]:  # Limit to 8 suggestions
                        icon = "📁" if suggestion.endswith("/") else "📄"
                        suggestions_list.append(ListItem(Label(f"{icon} {suggestion}")))

                    self.current_suggestions = suggestions
                    self.current_suggestion_type = "files"
                    self.selected_suggestion_index = 0
                    suggestions_list.set_class(False, "hidden")
                    self.suggestions_visible = True
                    await self._update_suggestion_highlight()
            except (IndexError, AttributeError):
                # Ignore errors when parsing incomplete input
                pass

    async def _show_slash_suggestions(self, partial_command: str) -> None:
        """Show slash command suggestions."""
        suggestions = self.service.get_slash_command_suggestions(partial_command)

        if suggestions:
            suggestions_list = self.query_one("#suggestions-list", ListView)
            suggestions_list.clear()

            current_category = None
            for suggestion in suggestions[:10]:  # Limit to 10
                # Add category header if it changed
                if suggestion["category"] != current_category:
                    current_category = suggestion["category"]
                    if suggestions_list.children:  # Only add separator if not first
                        suggestions_list.append(
                            ListItem(
                                Label(f"─── {current_category} ───"),
                                classes="category-header",
                            )
                        )
                    else:
                        suggestions_list.append(
                            ListItem(
                                Label(f"─── {current_category} ───"),
                                classes="category-header",
                            )
                        )

                # Add command suggestion
                suggestions_list.append(
                    ListItem(
                        Label(
                            f"⚡ /{suggestion['command']} - {suggestion['description']}"
                        )
                    )
                )

            self.current_suggestions = [s["command"] for s in suggestions]
            self.current_suggestion_type = "slash"
            self.selected_suggestion_index = 0
            suggestions_list.set_class(False, "hidden")
            self.suggestions_visible = True
            await self._update_suggestion_highlight()

    async def _show_recent_files_suggestions(self) -> None:
        """Show recent files when @ is typed."""
        # Use the new _get_all_file_suggestions for consistency
        suggestions = self.service.get_recent_files_suggestions()

        if suggestions:
            suggestions_list = self.query_one("#suggestions-list", ListView)
            suggestions_list.clear()

            suggestions_list.append(
                ListItem(
                    Label("─── Files & Directories ───"), classes="category-header"
                )
            )
            for suggestion in suggestions:
                icon = "📁" if suggestion.endswith("/") else "📄"
                suggestions_list.append(ListItem(Label(f"{icon} {suggestion}")))

            self.current_suggestions = suggestions
            self.current_suggestion_type = "files"
            self.selected_suggestion_index = 0
            suggestions_list.set_class(False, "hidden")
            self.suggestions_visible = True
            await self._update_suggestion_highlight()

    async def _show_bash_suggestions(self, partial_command: str) -> None:
        """Show bash command suggestions."""
        # Get conversation context from recent messages
        context = partial_command

        bash_suggestions = self.service.get_contextual_bash_suggestions(context)

        if bash_suggestions:
            suggestions_list = self.query_one("#suggestions-list", ListView)
            suggestions_list.clear()

            suggestions_list.append(
                ListItem(
                    Label("─── Contextual Bash Commands ───"), classes="category-header"
                )
            )
            for cmd in bash_suggestions:
                suggestions_list.append(ListItem(Label(f"🔧 {cmd}")))

            self.current_suggestions = bash_suggestions
            self.current_suggestion_type = "bash"
            self.selected_suggestion_index = 0
            suggestions_list.set_class(False, "hidden")
            self.suggestions_visible = True
            await self._update_suggestion_highlight()

    async def _show_memory_suggestions(self) -> None:
        """Show memory/context suggestions (future feature)."""
        suggestions_list = self.query_one("#suggestions-list", ListView)
        suggestions_list.clear()

        suggestions_list.append(
            ListItem(
                Label("─── Memory Commands (Coming Soon) ───"),
                classes="category-header",
            )
        )
        future_commands = [
            "save context",
            "load context",
            "bridge claude",
            "bridge gemini",
            "list contexts",
        ]
        for cmd in future_commands:
            suggestions_list.append(ListItem(Label(f"🧠 {cmd}")))

        self.current_suggestions = future_commands
        self.current_suggestion_type = "memory"
        self.selected_suggestion_index = 0
        suggestions_list.set_class(False, "hidden")
        self.suggestions_visible = True
        await self._update_suggestion_highlight()

    async def _update_suggestion_highlight(self) -> None:
        """Update the visual highlight on the selected suggestion."""
        suggestions_list = self.query_one("#suggestions-list", ListView)

        # Clear previous highlights
        for i, item in enumerate(suggestions_list.children):
            if hasattr(item, "set_class"):
                item.set_class(False, "selected")

        # Highlight selected item (skip category headers)
        visible_items = [
            item
            for item in suggestions_list.children
            if not hasattr(item, "classes")
            or "category-header" not in str(item.classes)
        ]
        if visible_items and 0 <= self.selected_suggestion_index < len(visible_items):
            selected_item = visible_items[self.selected_suggestion_index]
            selected_item.set_class(True, "selected")

            # Scroll to show the selected item
            try:
                suggestions_list.scroll_to_widget(selected_item, animate=False)
            except (ValueError, AttributeError):
                # Fallback: scroll to center if scroll_to_widget fails
                total_items = len(suggestions_list.children)
                if total_items > 0:
                    scroll_position = (
                        self.selected_suggestion_index / total_items
                    ) * suggestions_list.max_scroll_y
                    suggestions_list.scroll_y = scroll_position

    async def _handle_tab_completion(self) -> None:
        """Handle tab completion by completing with the selected suggestion."""
        await self._complete_with_selected_suggestion()
        # Check if we should continue showing suggestions (for directories)
        await self._maybe_continue_suggestions()

    async def _handle_enhanced_tab_completion(self) -> None:
        """Handle enhanced tab completion with path segment expansion."""
        try:
            if not self.completion_state or not self.completion_state.active_mention:
                await self._complete_with_selected_suggestion()
                return

            mention = self.completion_state.active_mention
            context = self.completion_state.completion_contexts.get(mention.start_pos)

            if not context:
                await self._complete_with_selected_suggestion()
                return

            selected_suggestion = self.current_suggestions[
                self.selected_suggestion_index
            ]

            # Check if this is a directory that should be expanded
            if selected_suggestion.endswith("/") or "/" in selected_suggestion:
                # Use path segment expansion
                expanded = self.advanced_completion.path_expander.expand_next_segment(
                    self.advanced_completion.path_expander.create_expansion_state(
                        mention.file_ref
                    )
                )

                if expanded and self.completion_state:
                    # Apply expansion
                    input_widget = self.query_one("#command-input", Input)
                    new_text = self.completion_engine.apply_completion(
                        self.completion_state, context, expanded
                    )
                    input_widget.value = new_text

                    # Update cursor position
                    new_cursor_pos = mention.start_pos + 1 + len(expanded)
                    input_widget.cursor_position = new_cursor_pos

                    # Continue showing suggestions for further expansion
                    await self._maybe_continue_suggestions()
                    return

            # Fallback to regular completion
            await self._complete_with_selected_suggestion()

        except Exception:
            # Fallback on any error
            await self._complete_with_selected_suggestion()

    async def _maybe_continue_suggestions(self) -> None:
        """Continue showing suggestions if appropriate for further expansion."""
        try:
            input_widget = self.query_one("#command-input", Input)
            current_value = input_widget.value
            cursor_pos = getattr(input_widget, "cursor_position", len(current_value))

            # Re-parse input to see if we should continue
            if "@" in current_value and self.completion_initialized:
                # Small delay to let input settle
                await asyncio.sleep(0.01)
                await self._handle_enhanced_file_completion(current_value, cursor_pos)
        except Exception:
            # If anything goes wrong, just hide suggestions
            await self._hide_suggestions()

    async def _complete_with_selected_suggestion(self) -> None:
        """Complete input with the selected suggestion."""
        if not self.current_suggestions or self.selected_suggestion_index >= len(
            self.current_suggestions
        ):
            return

        input_widget = self.query_one("#command-input", Input)
        current_value = input_widget.value
        selected_suggestion = self.current_suggestions[self.selected_suggestion_index]

        if self.current_suggestion_type == "slash":
            # Replace /partial with /command
            input_widget.value = f"/{selected_suggestion} "
        elif self.current_suggestion_type in ["files", "enhanced_files"]:
            # Replace @partial with @filename - handle both basic and enhanced
            if (
                self.current_suggestion_type == "enhanced_files"
                and self.completion_state
                and self.completion_state.active_mention
            ):
                # Enhanced completion
                mention = self.completion_state.active_mention
                context = self.completion_state.completion_contexts.get(
                    mention.start_pos
                )
                if context:
                    new_text = self.completion_engine.apply_completion(
                        self.completion_state, context, selected_suggestion
                    )
                    input_widget.value = new_text + (
                        " " if not selected_suggestion.endswith("/") else ""
                    )
                    return

            # Fallback to basic completion
            parts = current_value.split("@")
            if len(parts) > 1:
                base_part = "@".join(parts[:-1]) + "@"
                input_widget.value = (
                    base_part
                    + selected_suggestion
                    + (" " if not selected_suggestion.endswith("/") else "")
                )
            else:
                input_widget.value = f"@{selected_suggestion} "
        elif self.current_suggestion_type == "bash":
            # Replace >partial with >command
            input_widget.value = f">{selected_suggestion}"
        elif self.current_suggestion_type == "memory":
            # Replace #partial with #command
            input_widget.value = f"#{selected_suggestion} "

    async def _hide_suggestions(self) -> None:
        """Hide the suggestions list."""
        suggestions_list = self.query_one("#suggestions-list", ListView)
        suggestions_list.set_class(True, "hidden")
        suggestions_list.clear()
        self.suggestions_visible = False
        self.current_suggestions = []
        self.current_suggestion_type = ""
        self.selected_suggestion_index = 0

    async def on_click(self, event: Click) -> None:
        """Handle click events to focus input."""
        # Always focus the command input when clicking anywhere in the TUI
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    async def on_key(self, event: Key) -> None:
        """Handle key events for suggestion navigation and command history."""
        if self.suggestions_visible:
            if event.key == "up":
                # Move selection up in suggestions
                if self.selected_suggestion_index > 0:
                    self.selected_suggestion_index -= 1
                    await self._update_suggestion_highlight()
                event.prevent_default()
            elif event.key == "down":
                # Move selection down in suggestions
                if self.selected_suggestion_index < len(self.current_suggestions) - 1:
                    self.selected_suggestion_index += 1
                    await self._update_suggestion_highlight()
                event.prevent_default()
            elif event.key == "tab":
                # Enhanced tab completion with path expansion
                if self.current_suggestions:
                    await self._handle_tab_completion()
                    event.prevent_default()
            elif event.key == "enter":
                # Complete and accept (hide suggestions)
                if self.current_suggestions:
                    await self._complete_with_selected_suggestion()
                    await self._hide_suggestions()
                    event.prevent_default()
                # If no suggestions, let enter work normally (don't prevent default)
            elif event.key == "escape":
                await self._hide_suggestions()
                # Don't prevent default - let it fall through to action_cancel_or_quit
        else:
            # Handle command history navigation when not in suggestions mode
            input_widget = self.query_one("#command-input", Input)

            if event.key == "up":
                # Handle up arrow: cursor navigation first, then history
                if await self._handle_cursor_navigation("up", input_widget):
                    event.prevent_default()
                else:
                    # Only use history if cursor can't move up
                    if self.command_history:
                        if self.history_index == -1:
                            # First time browsing history
                            self.history_index = len(self.command_history) - 1
                        elif self.history_index > 0:
                            self.history_index -= 1

                        if 0 <= self.history_index < len(self.command_history):
                            input_widget.value = self.command_history[
                                self.history_index
                            ]
                            input_widget.cursor_position = len(input_widget.value)
                    event.prevent_default()

            elif event.key == "down":
                # Handle down arrow: cursor navigation first, then history
                if await self._handle_cursor_navigation("down", input_widget):
                    event.prevent_default()
                else:
                    # Only use history if cursor can't move down
                    if self.command_history and self.history_index != -1:
                        if self.history_index < len(self.command_history) - 1:
                            self.history_index += 1
                            input_widget.value = self.command_history[
                                self.history_index
                            ]
                            input_widget.cursor_position = len(input_widget.value)
                        else:
                            # Go back to empty input
                            self.history_index = -1
                            input_widget.value = ""
                    event.prevent_default()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark  # type: ignore[has-type]

    async def action_toggle_detail_mode(self) -> None:
        """Toggle between summary and detailed file content mode."""
        self.detail_mode = not self.detail_mode
        self.service.set_detail_mode(self.detail_mode)

        # Show feedback
        log = self.query_one("#content-log")
        mode_text = "Detailed" if self.detail_mode else "Summary"
        log.mount(Static(f"🔄 File content mode: {mode_text}", classes="system-message"))
        log.scroll_end()

    async def action_cycle_model(self) -> None:
        """Cycle through available AI models with context optimization."""
        current_model = self.service.get_current_model_name()

        # Define model cycle order
        models = ["local", "claude", "gemini"]
        try:
            current_index = models.index(current_model)
            next_index = (current_index + 1) % len(models)
            next_model = models[next_index]
        except ValueError:
            next_model = "local"  # Default fallback

        # Switch model with context optimization
        result = self.service.switch_model_with_context(next_model)

        # Show feedback with optimization stats
        log = self.query_one("#content-log")

        # Basic switch message
        log.mount(Static(result["message"], classes="system-message"))

        # Context optimization stats
        opt_stats = result["context_optimization"]
        if opt_stats["original_length"] > 0:
            stats_msg = (
                f"📊 Context optimized: {opt_stats['compression_ratio']}x compression, "
                f"{opt_stats['quality_score']} quality score"
            )
            log.mount(Static(stats_msg, classes="system-message"))

        log.scroll_end()

    async def action_quit(self) -> None:
        """Quit the application with session summary and cleanup."""
        self._clear_terminal_on_exit()
        self._show_terminal_session_summary()
        self.exit()

    def _show_terminal_session_summary(self) -> None:
        """Show session summary in the terminal after TUI closes."""
        # Count interactions from the log
        log = self.query_one("#content-log")
        user_messages = len(
            [
                w
                for w in log.children
                if hasattr(w, "classes") and "user-message" in str(w.classes)
            ]
        )
        ai_responses = len(
            [
                w
                for w in log.children
                if hasattr(w, "classes") and "ai-response" in str(w.classes)
            ]
        )
        files_accessed = len(self.service.get_recent_files_suggestions())

        # Print directly to terminal (will appear after TUI closes)
        print("\n" + "=" * 60)
        print("🎯 AI-Hack Session Summary")
        print("=" * 60)
        print(f"• {user_messages} user interactions")
        print(f"• {ai_responses} AI responses")
        print(f"• {files_accessed} files accessed")
        print("• Context preserved across conversations")
        print("• Ready for cross-model bridging")
        print("=" * 60)
        print("Thanks for using AI-Hack! 🚀")
        print("=" * 60 + "\n")

    async def _handle_cursor_navigation(
        self, direction: str, input_widget: Any
    ) -> bool:
        """Handle intelligent cursor navigation in multi-line text.

        Returns True if cursor was moved, False if at boundary (use history).
        """
        text = input_widget.value
        cursor_pos = input_widget.cursor_position

        if not text:
            return False  # No text, can't navigate

        lines = text.split("\n")

        # Find current line and position within line
        current_line_idx = 0
        char_count = 0
        pos_in_line = cursor_pos

        for i, line in enumerate(lines):
            if char_count + len(line) + (1 if i < len(lines) - 1 else 0) >= cursor_pos:
                current_line_idx = i
                pos_in_line = cursor_pos - char_count
                break
            char_count += len(line) + 1  # +1 for newline

        if direction == "up":
            if current_line_idx > 0:
                # Move to same position in line above
                target_line = lines[current_line_idx - 1]
                new_pos_in_line = min(pos_in_line, len(target_line))

                # Calculate new cursor position
                new_cursor_pos = sum(
                    len(lines[i]) + 1 for i in range(current_line_idx - 1)
                )
                new_cursor_pos += new_pos_in_line
                input_widget.cursor_position = new_cursor_pos
                return True
            elif cursor_pos > 0:
                # At first line but not at start - go to start of line
                line_start = sum(len(lines[i]) + 1 for i in range(current_line_idx))
                input_widget.cursor_position = line_start
                return True
            else:
                # At start of first line - can't move up
                return False

        elif direction == "down":
            if current_line_idx < len(lines) - 1:
                # Move to same position in line below
                target_line = lines[current_line_idx + 1]
                new_pos_in_line = min(pos_in_line, len(target_line))

                # Calculate new cursor position
                new_cursor_pos = sum(
                    len(lines[i]) + 1 for i in range(current_line_idx + 1)
                )
                new_cursor_pos += new_pos_in_line
                input_widget.cursor_position = new_cursor_pos
                return True
            elif cursor_pos < len(text):
                # At last line but not at end - go to end of line
                current_line = lines[current_line_idx]
                line_start = sum(len(lines[i]) + 1 for i in range(current_line_idx))
                input_widget.cursor_position = line_start + len(current_line)
                return True
            else:
                # At end of last line - can't move down
                return False

        return False

    async def _show_quit_hint(self, message: str, duration: float = 3.0) -> None:
        """Show a temporary quit hint between the content log and input area."""
        quit_hint = self.query_one("#quit-hint", Static)
        quit_hint.update(message)
        quit_hint.set_class(False, "hidden")

        # Auto-hide after duration using a background task to not block
        asyncio.create_task(self._hide_quit_hint_after(duration))

    async def _hide_quit_hint_after(self, duration: float) -> None:
        """Hide quit hint after a delay."""
        await asyncio.sleep(duration)
        try:
            quit_hint = self.query_one("#quit-hint", Static)
            quit_hint.set_class(True, "hidden")
        except Exception:
            # Widget might be gone if app is shutting down
            pass

    def _clear_terminal_on_exit(self) -> None:
        """Clear the terminal when exiting to avoid splash screen clutter."""
        import os
        import subprocess

        try:
            # Clear screen using standard terminal command
            if os.name == "nt":  # Windows
                subprocess.run("cls", shell=True)
            else:  # Unix/Linux/macOS
                subprocess.run("clear", shell=True)
        except Exception:
            # Fallback: print enough newlines to push content off screen
            print("\n" * 50)

    async def action_cancel_or_quit(self) -> None:
        """Cancel current input, interrupt streaming, or quit on second press."""
        import time

        current_time = time.time()

        # Check if we're currently processing or streaming - interrupt it
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            log = self.query_one("#content-log")
            log.mount(
                Static("⚠️ Generation interrupted by user", classes="system-message")
            )
            log.scroll_end()
            await self._show_quit_hint(
                "⚠️ Generation stopped. Press Esc/Ctrl+C again to exit TUI", 3.0
            )
            self.last_cancel_time = current_time
            return
        elif self.current_streaming_widget and self.current_streaming_widget.streaming:
            self.current_streaming_widget.stop_streaming()
            log = self.query_one("#content-log")
            log.mount(
                Static("⚠️ Generation interrupted by user", classes="system-message")
            )
            log.scroll_end()
            await self._show_quit_hint(
                "⚠️ Generation stopped. Press Esc/Ctrl+C again to exit TUI", 3.0
            )
            self.last_cancel_time = current_time
            return

        # Check if input has content - clear it first
        input_widget = self.query_one("#command-input", Input)
        if input_widget.value.strip():
            input_widget.value = ""
            # Show cancel hint in quit hint area
            await self._show_quit_hint(
                "💡 Input cleared. Press Esc/Ctrl+C again to exit TUI", 3.0
            )
            self.last_cancel_time = current_time
            return

        # Double-tap detection for quit (within 2 seconds)
        if current_time - self.last_cancel_time < 2.0:
            await self.action_quit()
        else:
            # First press with empty input - show exit hint
            await self._show_quit_hint("🚪 Press Esc/Ctrl+C again to exit TUI", 3.0)
            self.last_cancel_time = current_time


if __name__ == "__main__":
    app = SessionApp()
    app.run()
