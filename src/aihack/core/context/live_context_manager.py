"""
Live Context Manager - Real-time context optimization during conversations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .context_engine import ContextEngine


@dataclass
class LiveMessage:
    content: str
    model: str
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    context_score: float = 0.0


@dataclass
class ConversationState:
    messages: List[LiveMessage] = field(default_factory=list)
    current_model: Optional[str] = None
    context_buffer: str = ""
    total_tokens_estimate: int = 0
    last_optimization: Optional[datetime] = None


class LiveContextManager:
    """Manages context optimization during active conversations."""

    def __init__(
        self,
        context_engine: Optional[ContextEngine] = None,
        max_context_length: int = 4000,
        optimization_threshold: int = 6000,
    ):
        self.context_engine = context_engine or ContextEngine()
        self.max_context_length = max_context_length
        self.optimization_threshold = optimization_threshold
        self.conversations: Dict[str, ConversationState] = {}

    def start_conversation(self, session_id: str, initial_model: str) -> None:
        """Initialize a new conversation session."""
        self.conversations[session_id] = ConversationState(current_model=initial_model)

    def add_message(
        self, session_id: str, content: str, role: str, model: Optional[str] = None
    ) -> None:
        """Add message to conversation and update context."""
        if session_id not in self.conversations:
            self.start_conversation(session_id, model or "claude")

        state = self.conversations[session_id]

        message = LiveMessage(
            content=content,
            model=model or state.current_model or "claude",
            timestamp=datetime.now(),
            role=role,
        )

        state.messages.append(message)
        state.context_buffer += f"\n{role}: {content}"
        state.total_tokens_estimate += len(content) // 4  # Rough token estimate

        # Auto-optimize if context getting too long
        if state.total_tokens_estimate > self.optimization_threshold:
            self._auto_optimize_context(session_id)

    def switch_model(self, session_id: str, new_model: str) -> str:
        """Switch to new model and optimize context for handoff."""
        if session_id not in self.conversations:
            raise ValueError(f"No conversation found for session {session_id}")

        state = self.conversations[session_id]
        old_model = state.current_model

        # Optimize context for new model
        optimized = self.context_engine.optimize_handoff(
            conversation=state.context_buffer,
            source_model=old_model or "claude",
            target_model=new_model,
            max_length=self.max_context_length,
        )

        # Update conversation state
        state.current_model = new_model
        state.context_buffer = optimized.content
        state.total_tokens_estimate = optimized.optimized_length // 4
        state.last_optimization = datetime.now()

        # Add system message about model switch
        self.add_message(
            session_id,
            f"Context optimized for {new_model}. Compression: {optimized.compression_ratio:.2f}, "
            f"Estimated time savings: {optimized.estimated_time_savings:.1f}s",
            role="system",
            model=new_model,
        )

        return optimized.content

    def get_current_context(self, session_id: str) -> str:
        """Get current optimized context for the session."""
        if session_id not in self.conversations:
            return ""

        state = self.conversations[session_id]

        # If context is getting long, optimize on-the-fly
        if state.total_tokens_estimate > self.max_context_length:
            self._auto_optimize_context(session_id)

        return state.context_buffer

    def _auto_optimize_context(self, session_id: str) -> None:
        """Automatically optimize context when it gets too long."""
        state = self.conversations[session_id]

        if not state.current_model:
            return

        # Optimize for current model
        optimized = self.context_engine.optimize_handoff(
            conversation=state.context_buffer,
            source_model=state.current_model,
            target_model=state.current_model,  # Same model, just compress
            max_length=self.max_context_length,
        )

        # Update state
        state.context_buffer = optimized.content
        state.total_tokens_estimate = optimized.optimized_length // 4
        state.last_optimization = datetime.now()

    def get_conversation_stats(self, session_id: str) -> Dict[str, Any]:
        """Get stats about the current conversation."""
        if session_id not in self.conversations:
            return {}

        state = self.conversations[session_id]

        return {
            "message_count": len(state.messages),
            "current_model": state.current_model,
            "estimated_tokens": state.total_tokens_estimate,
            "last_optimization": state.last_optimization,
            "context_length": len(state.context_buffer),
            "models_used": list(set(msg.model for msg in state.messages if msg.model)),
        }

    def cleanup_session(self, session_id: str) -> None:
        """Clean up conversation session."""
        if session_id in self.conversations:
            del self.conversations[session_id]


# Integration with CLI session
class CLIContextManager:
    """CLI-specific context management."""

    def __init__(self) -> None:
        self.live_manager = LiveContextManager()
        self.current_session: Optional[str] = None

    def start_session(self, model: str) -> str:
        """Start new CLI session."""
        session_id = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = session_id
        self.live_manager.start_conversation(session_id, model)
        return session_id

    def handle_user_input(self, user_input: str) -> None:
        """Process user input."""
        if self.current_session:
            self.live_manager.add_message(self.current_session, user_input, role="user")

    def handle_model_response(self, response: str, model: str) -> None:
        """Process model response."""
        if self.current_session:
            self.live_manager.add_message(
                self.current_session, response, role="assistant", model=model
            )

    def switch_model(self, new_model: str) -> str:
        """Switch models with context optimization."""
        if not self.current_session:
            return ""

        return self.live_manager.switch_model(self.current_session, new_model)

    def get_optimized_context(self) -> str:
        """Get current optimized context."""
        if not self.current_session:
            return ""

        return self.live_manager.get_current_context(self.current_session)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        if not self.current_session:
            return {}

        return self.live_manager.get_conversation_stats(self.current_session)
