"""
Telemetry and monitoring hooks for harmonic analysis.

Provides logging and metrics collection for scale/melody evidence,
pattern detection, and analysis performance.
"""

import logging
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""

    PATTERN_DETECTION = "pattern_detection"
    EVIDENCE_GENERATION = "evidence_generation"
    CONFIDENCE_DISTRIBUTION = "confidence_distribution"
    ANALYSIS_PERFORMANCE = "analysis_performance"
    SCALE_MELODY_USAGE = "scale_melody_usage"
    ARBITRATION_OUTCOME = "arbitration_outcome"


@dataclass
class AnalysisMetrics:
    """Metrics collected during analysis."""

    # Timing metrics
    analysis_time_ms: float = 0.0
    pattern_matching_time_ms: float = 0.0
    evidence_generation_time_ms: float = 0.0

    # Pattern detection metrics
    patterns_detected: int = 0
    pattern_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    evidence_count: int = 0

    # Scale/melody specific metrics
    scale_summaries_generated: int = 0
    melody_summaries_generated: int = 0
    scale_modes_detected: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    melody_contours_detected: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )

    # Confidence metrics
    confidence_distribution: Dict[str, List[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    arbitration_outcomes: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )

    # Input characteristics
    input_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    chord_count: int = 0
    melody_note_count: int = 0
    scale_count: int = 0


class TelemetryCollector:
    """Collects and aggregates telemetry data."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.session_metrics: List[AnalysisMetrics] = []
        self.aggregated_metrics: AnalysisMetrics = AnalysisMetrics()

    def log_analysis_start(self, context: Any) -> Optional[str]:
        """Log the start of an analysis and return a session ID."""
        if not self.enabled:
            return None

        session_id = f"analysis_{int(time.time() * 1000)}"

        # Log input characteristics
        input_types = []
        if hasattr(context, "chords") and context.chords:
            input_types.append("chords")
        if hasattr(context, "melody") and context.melody:
            input_types.append("melody")
        if hasattr(context, "scales") and context.scales:
            input_types.append("scales")
        if hasattr(context, "roman_numerals") and context.roman_numerals:
            input_types.append("romans")

        logger.debug(f"📊 Analysis started: session={session_id}, inputs={input_types}")
        return session_id

    def log_pattern_detection(
        self, session_id: Optional[str], patterns: List[Any]
    ) -> None:
        """Log pattern detection results."""
        if not self.enabled or not session_id:
            return

        pattern_types: Counter[str] = Counter()
        for pattern in patterns:
            if hasattr(pattern, "pattern_id"):
                # Extract pattern type from ID
                pattern_type = (
                    pattern.pattern_id.split(".")[0]
                    if "." in pattern.pattern_id
                    else pattern.pattern_id
                )
                pattern_types[pattern_type] += 1

        logger.debug(
            f"🎼 Patterns detected: session={session_id}, patterns={dict(pattern_types)}"
        )

    def log_evidence_generation(
        self, session_id: Optional[str], evidences: List[Any]
    ) -> None:
        """Log evidence generation results."""
        if not self.enabled or not session_id:
            return

        evidence_types: Counter[str] = Counter()
        for evidence in evidences:
            if hasattr(evidence, "pattern_id"):
                evidence_type = (
                    evidence.pattern_id.split(".")[0]
                    if "." in evidence.pattern_id
                    else evidence.pattern_id
                )
                evidence_types[evidence_type] += 1

        logger.debug(f"🔍 Evidence: {session_id}, {dict(evidence_types)}")

    def log_scale_summary_generation(
        self, session_id: Optional[str], scale_summary: Any
    ) -> None:
        """Log scale summary generation."""
        if not self.enabled or not session_id or not scale_summary:
            return

        mode = getattr(scale_summary, "detected_mode", "unknown")
        characteristics = getattr(scale_summary, "characteristic_notes", [])

        logger.info(f"🎵 Scale: {session_id}, {mode}, {characteristics}")

        # Aggregate metrics
        self.aggregated_metrics.scale_summaries_generated += 1
        if mode != "unknown":
            self.aggregated_metrics.scale_modes_detected[mode] += 1

    def log_melody_summary_generation(
        self, session_id: Optional[str], melody_summary: Any
    ) -> None:
        """Log melody summary generation."""
        if not self.enabled or not session_id or not melody_summary:
            return

        contour = getattr(melody_summary, "contour", "unknown")
        range_semitones = getattr(melody_summary, "range_semitones", 0)
        characteristics = getattr(melody_summary, "melodic_characteristics", [])

        logger.info(
            f"🎼 Melody summary: session={session_id}, contour={contour}, "
            f"range={range_semitones}, characteristics={characteristics}"
        )

        # Aggregate metrics
        self.aggregated_metrics.melody_summaries_generated += 1
        if contour != "unknown":
            self.aggregated_metrics.melody_contours_detected[contour] += 1

    def log_confidence_scores(
        self, session_id: Optional[str], analysis_summary: Any
    ) -> None:
        """Log confidence scores for distribution analysis."""
        if not self.enabled or not session_id or not analysis_summary:
            return

        analysis_type = (
            getattr(analysis_summary.type, "value", "unknown")
            if hasattr(analysis_summary, "type")
            else "unknown"
        )
        confidence = getattr(analysis_summary, "confidence", 0.0)

        logger.debug(
            f"📈 Confidence: session={session_id}, type={analysis_type}, "
            f"confidence={confidence:.3f}"
        )

        # Aggregate metrics
        self.aggregated_metrics.confidence_distribution[analysis_type].append(
            confidence
        )

    def log_arbitration_outcome(
        self,
        session_id: Optional[str],
        chosen_type: str,
        functional_conf: float,
        modal_conf: float,
    ) -> None:
        """Log arbitration decision outcomes."""
        if not self.enabled or not session_id:
            return

        logger.info(
            f"⚖️  Arbitration: session={session_id}, chosen={chosen_type}, "
            f"func={functional_conf:.3f}, modal={modal_conf:.3f}"
        )

        # Aggregate metrics
        self.aggregated_metrics.arbitration_outcomes[chosen_type] += 1

    def log_analysis_complete(
        self, session_id: Optional[str], analysis_time_ms: float, result: Any
    ) -> None:
        """Log analysis completion and final metrics."""
        if not self.enabled or not session_id:
            return

        logger.info(
            f"✅ Analysis complete: session={session_id}, "
            f"time={analysis_time_ms:.2f}ms"
        )

        # Create session metrics
        session_metrics = AnalysisMetrics(analysis_time_ms=analysis_time_ms)

        # Extract final result characteristics
        if result and hasattr(result, "primary") and result.primary:
            primary = result.primary

            # Scale summary metrics
            if hasattr(primary, "scale_summary") and primary.scale_summary:
                session_metrics.scale_summaries_generated = 1
                mode = getattr(primary.scale_summary, "detected_mode", None)
                if mode:
                    session_metrics.scale_modes_detected[mode] = 1

            # Melody summary metrics
            if hasattr(primary, "melody_summary") and primary.melody_summary:
                session_metrics.melody_summaries_generated = 1
                contour = getattr(primary.melody_summary, "contour", None)
                if contour:
                    session_metrics.melody_contours_detected[contour] = 1

            # Confidence metrics
            if hasattr(primary, "confidence"):
                analysis_type = (
                    getattr(primary.type, "value", "unknown")
                    if hasattr(primary, "type")
                    else "unknown"
                )
                session_metrics.confidence_distribution[analysis_type].append(
                    primary.confidence
                )

        # Evidence metrics
        if result and hasattr(result, "evidence") and result.evidence:
            session_metrics.evidence_count = len(result.evidence)

        self.session_metrics.append(session_metrics)

    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics across all sessions."""
        if not self.enabled:
            return {"telemetry_disabled": True}

        # Compute summary statistics
        total_sessions = len(self.session_metrics)

        if total_sessions == 0:
            return {"no_sessions": True}

        # Timing statistics
        analysis_times = [m.analysis_time_ms for m in self.session_metrics]
        avg_analysis_time = sum(analysis_times) / len(analysis_times)

        # Scale/melody usage
        total_scale_summaries = sum(
            m.scale_summaries_generated for m in self.session_metrics
        )
        total_melody_summaries = sum(
            m.melody_summaries_generated for m in self.session_metrics
        )

        # Confidence distributions
        all_confidences = []
        for m in self.session_metrics:
            for conf_list in m.confidence_distribution.values():
                all_confidences.extend(conf_list)

        avg_confidence = (
            sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        )

        return {
            "session_count": total_sessions,
            "performance": {
                "avg_analysis_time_ms": avg_analysis_time,
                "total_analysis_time_ms": sum(analysis_times),
            },
            "scale_melody_usage": {
                "scale_summaries_generated": total_scale_summaries,
                "melody_summaries_generated": total_melody_summaries,
                "scale_usage_rate": total_scale_summaries / total_sessions,
                "melody_usage_rate": total_melody_summaries / total_sessions,
            },
            "confidence_metrics": {
                "average_confidence": avg_confidence,
                "confidence_samples": len(all_confidences),
            },
            "pattern_detection": {
                "total_evidence_generated": sum(
                    m.evidence_count for m in self.session_metrics
                ),
                "avg_evidence_per_session": sum(
                    m.evidence_count for m in self.session_metrics
                )
                / total_sessions,
            },
        }

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        if not self.enabled:
            return '{"telemetry_disabled": true}'

        metrics = self.get_aggregated_metrics()

        if format == "json":
            import json

            return json.dumps(metrics, indent=2)
        elif format == "summary":
            # Human-readable summary
            perf = metrics.get("performance", {})
            scale_mel = metrics.get("scale_melody_usage", {})
            conf = metrics.get("confidence_metrics", {})
            patterns = metrics.get("pattern_detection", {})

            summary_lines = [
                "📊 Harmonic Analysis Telemetry Summary",
                "=" * 40,
                f"Sessions: {metrics.get('session_count', 0)}",
                f"Avg Time: {perf.get('avg_analysis_time_ms', 0):.1f}ms",
                f"Scale Usage: {scale_mel.get('scale_usage_rate', 0):.1%}",
                f"Melody Usage: {scale_mel.get('melody_usage_rate', 0):.1%}",
                f"Avg Confidence: {conf.get('average_confidence', 0):.2f}",
                f"Evidence/Session: {patterns.get('avg_evidence_per_session', 0):.1f}",
            ]
            return "\n".join(summary_lines)
        else:
            raise ValueError(f"Unknown format: {format}")


# Global telemetry collector instance
_global_telemetry = TelemetryCollector()


def get_telemetry_collector() -> TelemetryCollector:
    """Get the global telemetry collector instance."""
    return _global_telemetry


def configure_telemetry(enabled: bool = True, logger_level: str = "INFO") -> None:
    """Configure global telemetry settings."""
    _global_telemetry.enabled = enabled

    # Configure logger level
    numeric_level = getattr(logging, logger_level.upper(), logging.INFO)
    logging.getLogger(__name__).setLevel(numeric_level)

    logger.info(f"🔧 Telemetry configured: enabled={enabled}, level={logger_level}")


def log_scale_melody_pattern_detection(pattern_ids: List[str]) -> None:
    """Log detection of scale/melody specific patterns."""
    if not _global_telemetry.enabled:
        return

    scale_patterns = [p for p in pattern_ids if "scale" in p.lower()]
    melody_patterns = [
        p for p in pattern_ids if "melody" in p.lower() or "interval" in p.lower()
    ]

    if scale_patterns:
        logger.info(f"🎵 Scale patterns detected: {scale_patterns}")
    if melody_patterns:
        logger.info(f"🎼 Melody patterns detected: {melody_patterns}")


# Convenience functions for common telemetry operations
def log_analysis_metrics(session_id: str, **kwargs: Any) -> None:
    """Log arbitrary analysis metrics."""
    if _global_telemetry.enabled:
        logger.debug(f"📊 Metrics: session={session_id}, {kwargs}")


def export_telemetry_summary() -> str:
    """Export a human-readable telemetry summary."""
    return _global_telemetry.export_metrics("summary")
