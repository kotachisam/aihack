"""
Context Engine - Weighted importance models for cross-AI context bridging.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


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
    line_start: int
    line_end: int


@dataclass
class OptimizedContext:
    content: str
    original_length: int
    optimized_length: int
    compression_ratio: float
    estimated_time_savings: float
    quality_score: float


class WeightingStrategy(ABC):
    """Abstract base for context weighting strategies."""

    @abstractmethod
    def get_weights(self, target_model: ModelType) -> Dict[ContextType, float]:
        pass


class BasicWeightingStrategy(WeightingStrategy):
    """Simple hardcoded weights for MVP."""

    def get_weights(self, target_model: ModelType) -> Dict[ContextType, float]:
        base_weights = {
            ContextType.STRATEGIC: 1.0,
            ContextType.IMPLEMENTATION: 0.8,
            ContextType.DEBUG: 0.6,
            ContextType.CHAT: 0.3,
        }

        # Model-specific adjustments
        if target_model == ModelType.LOCAL:
            # Local models need more structured context
            base_weights[ContextType.IMPLEMENTATION] = 0.9
            base_weights[ContextType.DEBUG] = 0.7

        elif target_model == ModelType.CLAUDE:
            # Claude handles strategic context well
            base_weights[ContextType.STRATEGIC] = 1.0
            base_weights[ContextType.CHAT] = 0.4

        elif target_model == ModelType.GEMINI:
            # Gemini good at implementation details
            base_weights[ContextType.IMPLEMENTATION] = 0.9
            base_weights[ContextType.DEBUG] = 0.8

        return base_weights


class ContextClassifier:
    """Classifies conversation segments by type."""

    def classify_segment(self, text: str) -> ContextType:
        text_lower = text.lower()

        # Strategic indicators
        strategic_keywords = [
            "architecture",
            "design",
            "approach",
            "strategy",
            "plan",
            "goal",
        ]
        if any(keyword in text_lower for keyword in strategic_keywords):
            return ContextType.STRATEGIC

        # Debug indicators
        debug_keywords = [
            "error",
            "bug",
            "fix",
            "debug",
            "issue",
            "problem",
            "traceback",
        ]
        if any(keyword in text_lower for keyword in debug_keywords):
            return ContextType.DEBUG

        # Implementation indicators
        impl_keywords = ["function", "class", "method", "implement", "code", "variable"]
        if any(keyword in text_lower for keyword in impl_keywords):
            return ContextType.IMPLEMENTATION

        # Default to chat
        return ContextType.CHAT


class ContextEngine:
    """Main context optimization engine."""

    def __init__(self, weighting_strategy: Optional[WeightingStrategy] = None):
        self.weighting_strategy = weighting_strategy or BasicWeightingStrategy()
        self.classifier = ContextClassifier()

    def segment_conversation(self, conversation: str) -> List[ContextSegment]:
        """Break conversation into typed segments."""
        lines = conversation.split("\n")
        segments = []

        current_segment: List[str] = []
        current_type = None
        start_line = 0

        for i, line in enumerate(lines):
            if line.strip():
                line_type = self.classifier.classify_segment(line)

                if current_type is None:
                    current_type = line_type
                    start_line = i

                if line_type != current_type:
                    # Finish current segment
                    if current_segment:
                        segments.append(
                            ContextSegment(
                                content="\n".join(current_segment),
                                segment_type=current_type,
                                importance_score=0.0,  # Will be set later
                                line_start=start_line,
                                line_end=i - 1,
                            )
                        )

                    # Start new segment
                    current_segment = [line]
                    current_type = line_type
                    start_line = i
                else:
                    current_segment.append(line)

        # Add final segment
        if current_segment and current_type:
            segments.append(
                ContextSegment(
                    content="\n".join(current_segment),
                    segment_type=current_type,
                    importance_score=0.0,
                    line_start=start_line,
                    line_end=len(lines) - 1,
                )
            )

        return segments

    def apply_weights(
        self, segments: List[ContextSegment], target_model: ModelType
    ) -> List[ContextSegment]:
        """Apply importance weights to segments."""
        weights = self.weighting_strategy.get_weights(target_model)

        for segment in segments:
            segment.importance_score = weights.get(segment.segment_type, 0.5)

        return segments

    def optimize_context(
        self, segments: List[ContextSegment], max_length: int = 4000
    ) -> str:
        """Optimize context by importance, respecting length limits."""
        # Sort by importance score descending
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
                # Try to fit partial segment
                remaining = max_length - current_length
                if remaining > 100:  # Only if meaningful space left
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
        target_model_enum = ModelType(target_model.lower())

        # Segment and weight
        segments = self.segment_conversation(conversation)
        weighted_segments = self.apply_weights(segments, target_model_enum)

        # Optimize
        optimized_content = self.optimize_context(weighted_segments, max_length)

        # Calculate metrics
        original_length = len(conversation)
        optimized_length = len(optimized_content)
        compression_ratio = (
            optimized_length / original_length if original_length > 0 else 1.0
        )

        # Estimate time savings (rough heuristic)
        estimated_time_savings = max(
            0, (original_length - optimized_length) / 1000 * 0.5
        )

        # Quality score based on how much strategic/implementation content preserved
        strategic_preserved = sum(
            1
            for s in weighted_segments
            if s.segment_type in [ContextType.STRATEGIC, ContextType.IMPLEMENTATION]
            and s.content in optimized_content
        )
        total_important = sum(
            1
            for s in weighted_segments
            if s.segment_type in [ContextType.STRATEGIC, ContextType.IMPLEMENTATION]
        )
        quality_score = (
            strategic_preserved / total_important if total_important > 0 else 1.0
        )

        return OptimizedContext(
            content=optimized_content,
            original_length=original_length,
            optimized_length=optimized_length,
            compression_ratio=compression_ratio,
            estimated_time_savings=estimated_time_savings,
            quality_score=quality_score,
        )
