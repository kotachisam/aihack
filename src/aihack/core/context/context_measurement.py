"""
Context Effectiveness Measurement - Real-time quality assessment.
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .context_engine import ContextSegment


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for context optimization."""

    coherence_score: float  # How well context flows together
    completeness_score: float  # How much essential info is preserved
    relevance_score: float  # How relevant the context is to the task
    compression_efficiency: float  # Quality per compression ratio
    semantic_preservation: float  # How well meaning is preserved
    execution_time_ms: float  # Processing time
    overall_score: float  # Weighted combination


class ContextQualityMeasurer:
    """Measures context optimization quality in real-time."""

    def __init__(self) -> None:
        self.quality_cache: Dict[
            str, QualityMetrics
        ] = {}  # Cache for expensive computations

    def measure_optimization_quality(
        self,
        original: str,
        optimized: str,
        segments: List[ContextSegment],
        target_model: str,
        execution_time_ms: float,
    ) -> QualityMetrics:
        """Comprehensive quality measurement of context optimization."""

        # Generate cache key
        cache_key = self._generate_cache_key(original, optimized, target_model)
        if cache_key in self.quality_cache:
            cached = self.quality_cache[cache_key]
            cached.execution_time_ms = execution_time_ms
            return cached

        # Calculate individual quality scores
        coherence = self._measure_coherence(original, optimized)
        completeness = self._measure_completeness(original, optimized, segments)
        relevance = self._measure_relevance(optimized, target_model)
        compression_eff = self._measure_compression_efficiency(
            original, optimized, segments
        )
        semantic_preservation = self._measure_semantic_preservation(original, optimized)

        # Calculate weighted overall score
        weights = {
            "coherence": 0.2,
            "completeness": 0.3,
            "relevance": 0.2,
            "compression_efficiency": 0.15,
            "semantic_preservation": 0.15,
        }

        overall = (
            coherence * weights["coherence"]
            + completeness * weights["completeness"]
            + relevance * weights["relevance"]
            + compression_eff * weights["compression_efficiency"]
            + semantic_preservation * weights["semantic_preservation"]
        )

        metrics = QualityMetrics(
            coherence_score=coherence,
            completeness_score=completeness,
            relevance_score=relevance,
            compression_efficiency=compression_eff,
            semantic_preservation=semantic_preservation,
            execution_time_ms=execution_time_ms,
            overall_score=overall,
        )

        # Cache result
        self.quality_cache[cache_key] = metrics

        # Limit cache size
        if len(self.quality_cache) > 100:
            oldest_key = next(iter(self.quality_cache))
            del self.quality_cache[oldest_key]

        return metrics

    def _generate_cache_key(
        self, original: str, optimized: str, target_model: str
    ) -> str:
        """Generate cache key for quality computation."""
        content = f"{original[:100]}{optimized[:100]}{target_model}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _measure_coherence(self, original: str, optimized: str) -> float:
        """Measure how well the optimized context flows together."""
        # Check for abrupt transitions and missing connective elements
        optimized_lines = [
            line.strip() for line in optimized.split("\n") if line.strip()
        ]

        if len(optimized_lines) < 2:
            return 1.0  # Single line is coherent by definition

        coherence_score = 1.0

        # Check for abrupt topic changes
        topic_transitions = 0
        for i in range(1, len(optimized_lines)):
            prev_line = optimized_lines[i - 1].lower()
            curr_line = optimized_lines[i].lower()

            # Simple heuristic: look for completely different vocabulary
            prev_words = set(re.findall(r"\w+", prev_line))
            curr_words = set(re.findall(r"\w+", curr_line))

            if prev_words and curr_words:
                overlap = len(prev_words & curr_words) / len(prev_words | curr_words)
                if overlap < 0.1:  # Very little word overlap
                    topic_transitions += 1

        # Penalize excessive topic jumping
        if topic_transitions > len(optimized_lines) * 0.3:
            coherence_score *= 0.7

        # Check for missing context clues
        context_indicators = [
            "because",
            "therefore",
            "however",
            "also",
            "additionally",
            "furthermore",
        ]
        original_indicators = sum(
            1 for indicator in context_indicators if indicator in original.lower()
        )
        optimized_indicators = sum(
            1 for indicator in context_indicators if indicator in optimized.lower()
        )

        if original_indicators > 0:
            preservation_ratio = optimized_indicators / original_indicators
            coherence_score *= min(1.0, preservation_ratio + 0.5)

        return max(0.0, min(1.0, coherence_score))

    def _measure_completeness(
        self, original: str, optimized: str, segments: List[ContextSegment]
    ) -> float:
        """Measure how much essential information is preserved."""
        if not segments:
            # Fallback: simple length-based completeness
            return len(optimized) / len(original) if original else 1.0

        # Weight completeness by segment importance
        total_importance = sum(seg.importance_score for seg in segments)
        preserved_importance = 0.0

        for segment in segments:
            # Check if segment content is substantially preserved in optimized
            segment_words = set(re.findall(r"\w+", segment.content.lower()))
            optimized_words = set(re.findall(r"\w+", optimized.lower()))

            if segment_words:
                overlap_ratio = len(segment_words & optimized_words) / len(
                    segment_words
                )
                preserved_importance += segment.importance_score * overlap_ratio

        completeness = (
            preserved_importance / total_importance if total_importance > 0 else 1.0
        )
        return max(0.0, min(1.0, completeness))

    def _measure_relevance(self, optimized: str, target_model: str) -> float:
        """Measure relevance of optimized context to target model."""
        # Model-specific relevance indicators
        model_preferences = {
            "claude": {
                "prefers": ["strategy", "architecture", "analysis", "reasoning"],
                "dislikes": ["verbose", "repetitive", "trivial"],
            },
            "gemini": {
                "prefers": ["implementation", "code", "specific", "actionable"],
                "dislikes": ["abstract", "philosophical", "vague"],
            },
            "local": {
                "prefers": ["structured", "clear", "direct", "specific"],
                "dislikes": ["ambiguous", "complex", "abstract"],
            },
        }

        if target_model not in model_preferences:
            return 0.8  # Neutral score for unknown models

        prefs = model_preferences[target_model]
        optimized_lower = optimized.lower()

        relevance_score = 0.7  # Base score

        # Boost for preferred content
        for preferred in prefs["prefers"]:
            if preferred in optimized_lower:
                relevance_score += 0.05

        # Penalize disliked content
        for disliked in prefs["dislikes"]:
            if disliked in optimized_lower:
                relevance_score -= 0.05

        # Check for model-appropriate structure
        if target_model == "local":
            # Local models prefer structured, numbered lists
            if re.search(r"\d+\.", optimized) or re.search(r"[-*]\s", optimized):
                relevance_score += 0.1

        return max(0.0, min(1.0, relevance_score))

    def _measure_compression_efficiency(
        self, original: str, optimized: str, segments: List[ContextSegment]
    ) -> float:
        """Measure quality achieved per unit of compression."""
        original_len = len(original)
        optimized_len = len(optimized)

        if original_len == 0:
            return 1.0

        compression_ratio = optimized_len / original_len

        # Efficiency = information density improvement
        # If we compressed by 50% but kept 90% of the important info, that's very efficient
        important_segments = [seg for seg in segments if seg.importance_score > 0.7]
        important_content = "\n".join(seg.content for seg in important_segments)

        if not important_content:
            return compression_ratio  # No important content identified

        important_preservation = len(
            [seg for seg in important_segments if seg.content in optimized]
        ) / len(important_segments)

        # Efficiency is high when we compress a lot but preserve important content
        efficiency = important_preservation / (
            compression_ratio + 0.1
        )  # Avoid division by zero
        return max(0.0, min(1.0, efficiency))

    def _measure_semantic_preservation(self, original: str, optimized: str) -> float:
        """Measure how well semantic meaning is preserved."""
        # Simple semantic preservation heuristics

        # 1. Key concept preservation
        original_concepts = self._extract_key_concepts(original)
        optimized_concepts = self._extract_key_concepts(optimized)

        if not original_concepts:
            return 1.0

        concept_preservation = len(original_concepts & optimized_concepts) / len(
            original_concepts
        )

        # 2. Relationship preservation (simple version)
        original_relationships = self._extract_relationships(original)
        optimized_relationships = self._extract_relationships(optimized)

        if original_relationships:
            relationship_preservation = len(
                original_relationships & optimized_relationships
            ) / len(original_relationships)
        else:
            relationship_preservation = 1.0

        # Combined semantic score
        semantic_score = 0.7 * concept_preservation + 0.3 * relationship_preservation
        return max(0.0, min(1.0, semantic_score))

    def _extract_key_concepts(self, text: str) -> set:
        """Extract key concepts from text (simplified approach)."""
        # Remove common words and extract meaningful terms
        common_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        concepts = set(word for word in words if word not in common_words)

        # Also extract quoted strings and code-like patterns
        quotes = re.findall(r'"([^"]+)"', text)
        code_patterns = re.findall(r"`([^`]+)`", text)

        concepts.update(quotes)
        concepts.update(code_patterns)

        return concepts

    def _extract_relationships(self, text: str) -> set:
        """Extract simple relationships from text."""
        relationships = set()

        # Look for common relationship patterns
        patterns = [
            r"(\w+)\s+is\s+(\w+)",
            r"(\w+)\s+has\s+(\w+)",
            r"(\w+)\s+uses\s+(\w+)",
            r"(\w+)\s+calls\s+(\w+)",
            r"(\w+)\s+extends\s+(\w+)",
            r"(\w+)\s+implements\s+(\w+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                relationships.add(f"{match[0]}-{match[1]}")

        return relationships


class RealTimeQualityMonitor:
    """Monitors context quality in real-time during conversations."""

    def __init__(self) -> None:
        self.measurer = ContextQualityMeasurer()
        self.quality_history: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            "low_quality": 0.6,
            "poor_coherence": 0.5,
            "excessive_compression": 0.2,
        }

    def monitor_optimization(
        self,
        original: str,
        optimized: str,
        segments: List[ContextSegment],
        target_model: str,
        execution_time_ms: float,
    ) -> Dict[str, Any]:
        """Monitor optimization quality and generate alerts if needed."""

        metrics = self.measurer.measure_optimization_quality(
            original, optimized, segments, target_model, execution_time_ms
        )

        # Store in history
        self.quality_history.append(
            {
                "timestamp": datetime.now(),
                "metrics": metrics,
                "target_model": target_model,
            }
        )

        # Keep only recent history
        if len(self.quality_history) > 50:
            self.quality_history = self.quality_history[-50:]

        # Generate alerts
        alerts = []

        if metrics.overall_score < self.alert_thresholds["low_quality"]:
            alerts.append(
                {
                    "type": "quality_warning",
                    "message": f"Low optimization quality: {metrics.overall_score:.2f}",
                    "suggestion": "Consider adjusting importance weights",
                }
            )

        if metrics.coherence_score < self.alert_thresholds["poor_coherence"]:
            alerts.append(
                {
                    "type": "coherence_warning",
                    "message": f"Poor context coherence: {metrics.coherence_score:.2f}",
                    "suggestion": "May need better segment ordering",
                }
            )

        compression_ratio = len(optimized) / len(original) if original else 1.0
        if compression_ratio < self.alert_thresholds["excessive_compression"]:
            alerts.append(
                {
                    "type": "compression_warning",
                    "message": f"Excessive compression: {compression_ratio:.2f}",
                    "suggestion": "Consider increasing context length limit",
                }
            )

        return {
            "metrics": metrics,
            "alerts": alerts,
            "trend": self._analyze_trend(),
            "recommendations": self._generate_recommendations(metrics),
        }

    def _analyze_trend(self) -> str:
        """Analyze quality trend over recent optimizations."""
        if len(self.quality_history) < 3:
            return "insufficient_data"

        recent_scores = [h["metrics"].overall_score for h in self.quality_history[-5:]]
        older_scores = [
            h["metrics"].overall_score for h in self.quality_history[-10:-5]
        ]

        if not older_scores:
            return "insufficient_data"

        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)

        if recent_avg > older_avg + 0.05:
            return "improving"
        elif recent_avg < older_avg - 0.05:
            return "declining"
        else:
            return "stable"

    def _generate_recommendations(self, metrics: QualityMetrics) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []

        if metrics.completeness_score < 0.7:
            recommendations.append(
                "Increase importance weights for essential content types"
            )

        if metrics.coherence_score < 0.7:
            recommendations.append("Improve segment ordering or add transition text")

        if metrics.compression_efficiency < 0.5:
            recommendations.append(
                "Review compression strategy - may be too aggressive"
            )

        if metrics.execution_time_ms > 1000:
            recommendations.append("Optimize processing speed - taking too long")

        if not recommendations:
            recommendations.append(
                "Quality metrics look good - no immediate action needed"
            )

        return recommendations
