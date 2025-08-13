"""
Basic Context Engine - Open Source version with essential context persistence.
Simplified version of the full context engine for community use.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ContextType(Enum):
    STRATEGIC = "strategic"
    IMPLEMENTATION = "implementation"
    DEBUG = "debug"
    CHAT = "chat"


class ModelType(Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    LOCAL = "local"


@dataclass
class ContextSegment:
    content: str
    segment_type: ContextType
    importance_score: float
    timestamp: datetime


@dataclass
class OptimizedContext:
    content: str
    original_length: int
    optimized_length: int
    compression_ratio: float
    quality_score: float


class BasicContextClassifier:
    """Simple keyword-based context classification for open source."""

    def classify_segment(self, text: str) -> ContextType:
        text_lower = text.lower()

        # Strategic indicators - high-level planning and architecture
        strategic_keywords = [
            "architecture",
            "design",
            "approach",
            "strategy",
            "plan",
            "goal",
            "overview",
        ]
        if any(keyword in text_lower for keyword in strategic_keywords):
            return ContextType.STRATEGIC

        # Debug indicators - error handling and troubleshooting
        debug_keywords = [
            "error",
            "bug",
            "fix",
            "debug",
            "issue",
            "problem",
            "traceback",
            "exception",
        ]
        if any(keyword in text_lower for keyword in debug_keywords):
            return ContextType.DEBUG

        # Implementation indicators - code and technical details
        impl_keywords = [
            "function",
            "class",
            "method",
            "implement",
            "code",
            "variable",
            "import",
            "def",
        ]
        if any(keyword in text_lower for keyword in impl_keywords):
            return ContextType.IMPLEMENTATION

        # Default to chat for casual conversation
        return ContextType.CHAT


class BasicWeightingStrategy:
    """Hardcoded importance weights for open source version."""

    def get_weights(self, target_model: ModelType) -> Dict[ContextType, float]:
        # Base importance hierarchy: Strategic > Implementation > Debug > Chat
        base_weights = {
            ContextType.STRATEGIC: 1.0,
            ContextType.IMPLEMENTATION: 0.8,
            ContextType.DEBUG: 0.6,
            ContextType.CHAT: 0.3,
        }

        # Simple model-specific adjustments
        if target_model == ModelType.LOCAL:
            # Local models benefit from more structured context
            base_weights[ContextType.IMPLEMENTATION] = 0.9
            base_weights[ContextType.DEBUG] = 0.7
        elif target_model == ModelType.CLAUDE:
            # Claude handles strategic thinking well
            base_weights[ContextType.STRATEGIC] = 1.0
            base_weights[ContextType.CHAT] = 0.4
        elif target_model == ModelType.GEMINI:
            # Gemini good at analysis and debugging
            base_weights[ContextType.IMPLEMENTATION] = 0.9
            base_weights[ContextType.DEBUG] = 0.8

        return base_weights


class BasicContextEngine:
    """Basic context persistence engine for open source."""

    def __init__(self) -> None:
        self.classifier = BasicContextClassifier()
        self.weighting = BasicWeightingStrategy()

    def segment_conversation(self, conversation: str) -> List[ContextSegment]:
        """Break conversation into typed segments with timestamps."""
        lines = conversation.split("\n")
        segments = []

        current_segment: List[str] = []
        current_type = None

        for line in lines:
            if line.strip():
                line_type = self.classifier.classify_segment(line)

                if current_type is None:
                    current_type = line_type

                if line_type != current_type:
                    # Finish current segment
                    if current_segment:
                        segments.append(
                            ContextSegment(
                                content="\n".join(current_segment),
                                segment_type=current_type,
                                importance_score=0.0,  # Will be set later
                                timestamp=datetime.now(),
                            )
                        )

                    # Start new segment
                    current_segment = [line]
                    current_type = line_type
                else:
                    current_segment.append(line)

        # Add final segment
        if current_segment and current_type:
            segments.append(
                ContextSegment(
                    content="\n".join(current_segment),
                    segment_type=current_type,
                    importance_score=0.0,
                    timestamp=datetime.now(),
                )
            )

        return segments

    def apply_weights(
        self, segments: List[ContextSegment], target_model: ModelType
    ) -> List[ContextSegment]:
        """Apply importance weights based on target model."""
        weights = self.weighting.get_weights(target_model)

        for segment in segments:
            segment.importance_score = weights.get(segment.segment_type, 0.5)

        return segments

    def optimize_context(
        self, segments: List[ContextSegment], max_length: int = 4000
    ) -> str:
        """Optimize context by importance, respecting length limits."""
        # Sort by importance score (descending)
        sorted_segments = sorted(
            segments, key=lambda s: s.importance_score, reverse=True
        )

        optimized_content = []
        current_length = 0

        for segment in sorted_segments:
            segment_length = len(segment.content)

            if current_length + segment_length <= max_length:
                optimized_content.append(segment.content)
                current_length += segment_length
            else:
                # Try to fit partial segment if there's meaningful space
                remaining = max_length - current_length
                if remaining > 100:
                    partial = segment.content[: remaining - 3] + "..."
                    optimized_content.append(partial)
                break

        return "\n".join(optimized_content)

    def optimize_handoff(
        self,
        conversation: str,
        source_model: str,
        target_model: str,
        max_length: int = 4000,
    ) -> OptimizedContext:
        """Main API - optimize context for model handoff."""
        try:
            target_model_enum = ModelType(target_model.lower())
        except ValueError:
            target_model_enum = ModelType.LOCAL  # Default fallback

        # Segment and weight the conversation
        segments = self.segment_conversation(conversation)
        weighted_segments = self.apply_weights(segments, target_model_enum)

        # Optimize for length constraints
        optimized_content = self.optimize_context(weighted_segments, max_length)

        # Calculate basic metrics
        original_length = len(conversation)
        optimized_length = len(optimized_content)
        compression_ratio = (
            optimized_length / original_length if original_length > 0 else 1.0
        )

        # Simple quality score based on preserved important segments
        important_segments = [
            s
            for s in weighted_segments
            if s.segment_type in [ContextType.STRATEGIC, ContextType.IMPLEMENTATION]
        ]
        preserved_important = sum(
            1 for s in important_segments if s.content in optimized_content
        )
        quality_score = (
            preserved_important / len(important_segments) if important_segments else 1.0
        )

        return OptimizedContext(
            content=optimized_content,
            original_length=original_length,
            optimized_length=optimized_length,
            compression_ratio=compression_ratio,
            quality_score=quality_score,
        )


class BasicSessionManager:
    """Basic session persistence for open source."""

    def __init__(self, data_dir: str = "~/.aihack"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.data_dir / "sessions.json"
        self.sessions = self._load_sessions()

    def _load_sessions(self) -> Dict[str, Any]:
        """Load existing sessions from disk."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, "r") as f:
                    loaded_data = json.load(f)
                    return loaded_data if isinstance(loaded_data, dict) else {}
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        try:
            with open(self.sessions_file, "w") as f:
                json.dump(self.sessions, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save session data: {e}")

    def save_session_context(self, session_id: str, context: str, model: str) -> None:
        """Save current context for session."""
        self.sessions[session_id] = {
            "context": context,
            "model": model,
            "last_updated": datetime.now().isoformat(),
            "message_count": len(context.split("\n")),
        }
        self._save_sessions()

    def restore_session_context(self, session_id: str) -> Optional[Tuple[str, str]]:
        """Restore context for session if it exists."""
        session_data = self.sessions.get(session_id)
        if session_data:
            return session_data["context"], session_data["model"]
        return None

    def list_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """List recent sessions with basic info."""
        sessions_list = []
        for session_id, data in self.sessions.items():
            sessions_list.append(
                {
                    "id": session_id,
                    "model": data.get("model", "unknown"),
                    "last_updated": data.get("last_updated", ""),
                    "message_count": data.get("message_count", 0),
                }
            )

        # Sort by last updated, most recent first
        sessions_list.sort(key=lambda x: x["last_updated"], reverse=True)
        return sessions_list[:limit]

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Remove sessions older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0

        sessions_to_remove = []
        for session_id, data in self.sessions.items():
            try:
                last_updated = datetime.fromisoformat(data["last_updated"])
                if last_updated < cutoff_date:
                    sessions_to_remove.append(session_id)
            except (ValueError, KeyError):
                # Invalid date format, remove old session
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            removed_count += 1

        if removed_count > 0:
            self._save_sessions()

        return removed_count


# Simple CLI integration class
class BasicCLIContextManager:
    """Basic CLI context management for open source."""

    def __init__(self) -> None:
        self.context_engine = BasicContextEngine()
        self.session_manager = BasicSessionManager()
        self.current_session: Optional[str] = None
        self.current_context = ""
        self.current_model = "local"

    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start new session or restore existing one."""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = session_id

        # Try to restore existing context
        restored = self.session_manager.restore_session_context(session_id)
        if restored:
            self.current_context, self.current_model = restored
            return f"Restored session {session_id} with {self.current_model}"
        else:
            self.current_context = ""
            return f"Started new session {session_id}"

    def add_message(self, role: str, content: str, model: Optional[str] = None) -> None:
        """Add message to current context."""
        if model:
            self.current_model = model

        message = f"{role}: {content}"
        if self.current_context:
            self.current_context += f"\n{message}"
        else:
            self.current_context = message

        # Save context periodically
        if self.current_session is not None:
            self.session_manager.save_session_context(
                self.current_session, self.current_context, self.current_model
            )

    def switch_model(
        self, new_model: str, max_context_length: int = 4000
    ) -> OptimizedContext:
        """Switch model with context optimization."""
        if not self.current_context:
            self.current_model = new_model
            return OptimizedContext("", 0, 0, 1.0, 1.0)

        # Optimize context for new model
        optimized = self.context_engine.optimize_handoff(
            self.current_context, self.current_model, new_model, max_context_length
        )

        # Update current state
        self.current_context = optimized.content
        self.current_model = new_model

        # Save updated context
        if self.current_session is not None:
            self.session_manager.save_session_context(
                self.current_session, self.current_context, self.current_model
            )

        return optimized

    def get_current_context(self) -> str:
        """Get current optimized context."""
        return self.current_context

    def get_session_info(self) -> Dict[str, Any]:
        """Get info about current session."""
        return {
            "session_id": self.current_session,
            "model": self.current_model,
            "context_length": len(self.current_context),
            "estimated_tokens": len(self.current_context) // 4,
        }
