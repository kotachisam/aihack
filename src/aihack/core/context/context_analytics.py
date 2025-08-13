"""
Context Analytics - Data collection and analysis for context optimization.
"""

import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class ContextEvent:
    """Single context optimization event for analysis."""

    session_id: str
    timestamp: datetime
    source_model: str
    target_model: str
    original_length: int
    optimized_length: int
    compression_ratio: float
    quality_score: float
    segments: List[Dict[str, Any]]  # Serialized ContextSegment data
    user_feedback: Optional[float] = None  # 1-5 rating if provided
    execution_time_ms: float = 0.0


@dataclass
class ModelPerformance:
    """Performance metrics for a specific model."""

    model_name: str
    avg_compression_ratio: float
    avg_quality_score: float
    avg_processing_time: float
    total_optimizations: int
    user_satisfaction: float
    context_types_handled: Dict[str, int]


class ContextDatabase:
    """SQLite database for context event storage."""

    def __init__(self, db_path: str = "~/.aihack/context_data.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS context_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source_model TEXT NOT NULL,
                    target_model TEXT NOT NULL,
                    original_length INTEGER NOT NULL,
                    optimized_length INTEGER NOT NULL,
                    compression_ratio REAL NOT NULL,
                    quality_score REAL NOT NULL,
                    segments TEXT NOT NULL,
                    user_feedback REAL,
                    execution_time_ms REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_session_timestamp
                ON context_events(session_id, timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_model_pair
                ON context_events(source_model, target_model)
            """
            )

    def store_event(self, event: ContextEvent) -> None:
        """Store context optimization event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO context_events
                (session_id, timestamp, source_model, target_model,
                 original_length, optimized_length, compression_ratio,
                 quality_score, segments, user_feedback, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.session_id,
                    event.timestamp.isoformat(),
                    event.source_model,
                    event.target_model,
                    event.original_length,
                    event.optimized_length,
                    event.compression_ratio,
                    event.quality_score,
                    json.dumps(event.segments),
                    event.user_feedback,
                    event.execution_time_ms,
                ),
            )

    def get_events(
        self, session_id: Optional[str] = None, days_back: int = 30
    ) -> List[ContextEvent]:
        """Retrieve context events for analysis."""
        cutoff = datetime.now() - timedelta(days=days_back)

        query = """
            SELECT * FROM context_events
            WHERE timestamp >= ?
        """
        params = [cutoff.isoformat()]

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            events = []

            for row in cursor.fetchall():
                events.append(
                    ContextEvent(
                        session_id=row[1],
                        timestamp=datetime.fromisoformat(row[2]),
                        source_model=row[3],
                        target_model=row[4],
                        original_length=row[5],
                        optimized_length=row[6],
                        compression_ratio=row[7],
                        quality_score=row[8],
                        segments=json.loads(row[9]),
                        user_feedback=row[10],
                        execution_time_ms=row[11],
                    )
                )

            return events


class ContextAnalyzer:
    """Analyzes context optimization patterns and effectiveness."""

    def __init__(self, database: ContextDatabase):
        self.db = database

    def analyze_model_performance(
        self, days_back: int = 30
    ) -> Dict[str, ModelPerformance]:
        """Analyze performance of each model combination."""
        events = self.db.get_events(days_back=days_back)
        model_stats = defaultdict(list)

        # Group events by target model
        for event in events:
            model_stats[event.target_model].append(event)

        performance = {}
        for model, model_events in model_stats.items():
            if not model_events:
                continue

            # Calculate metrics
            compressions = [e.compression_ratio for e in model_events]
            qualities = [e.quality_score for e in model_events]
            times = [e.execution_time_ms for e in model_events]
            feedbacks = [e.user_feedback for e in model_events if e.user_feedback]

            # Count context types handled
            context_types: Dict[str, int] = defaultdict(int)
            for event in model_events:
                for segment in event.segments:
                    context_types[segment.get("segment_type", "unknown")] += 1

            performance[model] = ModelPerformance(
                model_name=model,
                avg_compression_ratio=float(np.mean(compressions)),
                avg_quality_score=float(np.mean(qualities)),
                avg_processing_time=float(np.mean(times)),
                total_optimizations=len(model_events),
                user_satisfaction=float(np.mean(feedbacks)) if feedbacks else 0.0,
                context_types_handled=dict(context_types),
            )

        return performance

    def find_optimal_weights(self, target_model: str) -> Dict[str, float]:
        """Use historical data to find optimal importance weights."""
        events = self.db.get_events(days_back=90)
        model_events = [e for e in events if e.target_model == target_model]

        if len(model_events) < 10:
            # Not enough data, return defaults
            return {"strategic": 1.0, "implementation": 0.8, "debug": 0.6, "chat": 0.3}

        # Analyze which context types correlate with high quality scores
        context_quality = defaultdict(list)

        for event in model_events:
            if event.quality_score > 0:
                for segment in event.segments:
                    segment_type = segment.get("segment_type", "chat")
                    context_quality[segment_type].append(event.quality_score)

        # Calculate correlation-based weights
        optimal_weights: Dict[str, float] = {}
        base_quality = float(np.mean([e.quality_score for e in model_events]))

        for context_type, qualities in context_quality.items():
            if qualities:
                avg_quality = float(np.mean(qualities))
                # Weight is proportional to how much this context type improves quality
                weight = min(1.0, max(0.1, avg_quality / base_quality))
                optimal_weights[context_type] = weight

        return optimal_weights

    def detect_patterns(self) -> Dict[str, Any]:
        """Detect usage patterns and optimization opportunities."""
        events = self.db.get_events(days_back=30)

        if not events:
            return {}

        patterns = {
            "most_common_transitions": self._analyze_model_transitions(events),
            "peak_usage_hours": self._analyze_usage_timing(events),
            "problematic_context_types": self._find_problematic_contexts(events),
            "compression_trends": self._analyze_compression_trends(events),
            "user_satisfaction_trends": self._analyze_satisfaction_trends(events),
        }

        return patterns

    def _analyze_model_transitions(self, events: List[ContextEvent]) -> Dict[str, int]:
        """Find most common model transition patterns."""
        transitions: Dict[str, int] = defaultdict(int)

        for event in events:
            if event.source_model != event.target_model:
                transition = f"{event.source_model} -> {event.target_model}"
                transitions[transition] += 1

        return dict(sorted(transitions.items(), key=lambda x: x[1], reverse=True))

    def _analyze_usage_timing(self, events: List[ContextEvent]) -> Dict[int, int]:
        """Find peak usage hours."""
        hours: Dict[int, int] = defaultdict(int)

        for event in events:
            hour = event.timestamp.hour
            hours[hour] += 1

        return dict(sorted(hours.items(), key=lambda x: x[1], reverse=True))

    def _find_problematic_contexts(
        self, events: List[ContextEvent]
    ) -> List[Dict[str, Any]]:
        """Find context types that consistently perform poorly."""
        context_performance = defaultdict(list)

        for event in events:
            for segment in event.segments:
                context_type = segment.get("segment_type", "unknown")
                context_performance[context_type].append(event.quality_score)

        problematic = []
        for context_type, scores in context_performance.items():
            if len(scores) >= 5:  # Need minimum data
                avg_score = np.mean(scores)
                if avg_score < 0.7:  # Below threshold
                    problematic.append(
                        {
                            "context_type": context_type,
                            "avg_quality": avg_score,
                            "sample_size": len(scores),
                            "improvement_potential": 0.9 - avg_score,
                        }
                    )

        return sorted(
            problematic, key=lambda x: x["improvement_potential"], reverse=True
        )

    def _analyze_compression_trends(self, events: List[ContextEvent]) -> Dict[str, Any]:
        """Analyze compression ratio trends over time."""
        if len(events) < 10:
            return {}

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Split into recent vs older
        split_point = len(sorted_events) // 2
        older_events = sorted_events[:split_point]
        recent_events = sorted_events[split_point:]

        older_compression = np.mean([e.compression_ratio for e in older_events])
        recent_compression = np.mean([e.compression_ratio for e in recent_events])

        return {
            "older_avg_compression": older_compression,
            "recent_avg_compression": recent_compression,
            "trend": "improving"
            if recent_compression < older_compression
            else "degrading",
            "change_magnitude": float(abs(recent_compression - older_compression)),
        }

    def _analyze_satisfaction_trends(
        self, events: List[ContextEvent]
    ) -> Dict[str, Any]:
        """Analyze user satisfaction trends."""
        feedback_events = [e for e in events if e.user_feedback is not None]

        if len(feedback_events) < 5:
            return {"insufficient_data": True}

        # Sort by timestamp
        sorted_events = sorted(feedback_events, key=lambda e: e.timestamp)

        # Calculate moving average
        window_size = min(5, len(sorted_events) // 2)
        recent_feedback = [e.user_feedback for e in sorted_events[-window_size:]]

        # Filter out None values for numpy
        all_feedback = [
            e.user_feedback for e in feedback_events if e.user_feedback is not None
        ]
        recent_feedback_filtered = [f for f in recent_feedback if f is not None]

        return {
            "total_feedback_count": len(feedback_events),
            "avg_satisfaction": float(np.mean(all_feedback)) if all_feedback else 0.0,
            "recent_satisfaction": float(np.mean(recent_feedback_filtered))
            if recent_feedback_filtered
            else 0.0,
            "satisfaction_trend": "improving"
            if (recent_feedback_filtered and np.mean(recent_feedback_filtered) > 3.5)
            else "needs_attention",
        }


class ContextLearner:
    """Learns from context optimization data to improve future performance."""

    def __init__(self, database: ContextDatabase, analyzer: ContextAnalyzer):
        self.db = database
        self.analyzer = analyzer

    def suggest_weight_adjustments(self, target_model: str) -> Dict[str, Any]:
        """Suggest weight adjustments based on performance data."""
        current_performance = self.analyzer.analyze_model_performance()

        if target_model not in current_performance:
            return {}  # No data available

        perf = current_performance[target_model]
        suggestions: Dict[str, Any] = {}

        # If quality is low, suggest increasing weights for well-performing context types
        if perf.avg_quality_score < 0.8:
            optimal_weights = self.analyzer.find_optimal_weights(target_model)
            suggestions["recommended_weights"] = optimal_weights
            suggestions[
                "reason"
            ] = f"Quality score {perf.avg_quality_score:.2f} below target 0.8"

        # If compression is too aggressive, suggest increasing weights
        if perf.avg_compression_ratio < 0.3:
            suggestions["increase_weights_by"] = 0.1
            suggestions[
                "reason"
            ] = f"Compression ratio {perf.avg_compression_ratio:.2f} too aggressive"

        return suggestions

    def generate_improvement_plan(self) -> Dict[str, Any]:
        """Generate actionable improvement plan based on data analysis."""
        patterns = self.analyzer.detect_patterns()
        performance = self.analyzer.analyze_model_performance()

        plan: Dict[str, Any] = {
            "priority_improvements": [],
            "weight_adjustments": {},
            "feature_requests": [],
            "monitoring_focus": [],
        }

        # Identify priority improvements
        if "problematic_context_types" in patterns:
            for problem in patterns["problematic_context_types"][:3]:  # Top 3
                plan["priority_improvements"].append(
                    {
                        "issue": f"Low quality for {problem['context_type']} contexts",
                        "impact": problem["improvement_potential"],
                        "action": f"Improve classification or weighting for {problem['context_type']}",
                    }
                )

        # Suggest weight adjustments for each model
        for model_name in performance.keys():
            adjustments = self.suggest_weight_adjustments(model_name)
            if adjustments:
                plan["weight_adjustments"][model_name] = adjustments

        # Suggest new features based on usage patterns
        if "most_common_transitions" in patterns:
            top_transition = list(patterns["most_common_transitions"].keys())[0]
            plan["feature_requests"].append(
                f"Optimize for common transition: {top_transition}"
            )

        # Monitoring recommendations
        if performance:
            worst_model = min(performance.values(), key=lambda p: p.avg_quality_score)
            plan["monitoring_focus"].append(
                f"Monitor {worst_model.model_name} quality closely"
            )

        return plan
