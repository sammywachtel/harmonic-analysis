"""
Plugin registry for custom pattern evaluators.

This module provides a registry system for custom confidence functions that cannot
be expressed declaratively in the pattern JSON. Plugins are pure functions that
evaluate patterns and produce evidence scores.
"""

from typing import Any, Callable, Dict, Protocol

from .evidence import Evidence


class PatternEvaluator(Protocol):
    """Protocol for pattern evaluator plugins."""

    def __call__(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Evidence:
        """
        Evaluate a pattern match and produce evidence.

        Args:
            pattern: Pattern configuration from JSON
            context: Analysis context with normalized inputs

        Returns:
            Evidence object with scores and features
        """
        ...


class PluginRegistry:
    """Registry for pattern evaluator plugins."""

    def __init__(self) -> None:
        """Initialize empty plugin registry."""
        self._evaluators: Dict[str, PatternEvaluator] = {}
        self._register_builtin_evaluators()

    def _register_builtin_evaluators(self) -> None:
        """Register built-in evaluator functions."""
        # Register default evaluators - we'll add these as we port patterns
        self.register("logistic_default", self._logistic_default)
        self.register("logistic_dorian", self._logistic_dorian)
        self.register("identity", self._identity_evaluator)

    def register(self, name: str, evaluator: PatternEvaluator) -> None:
        """
        Register a pattern evaluator function.

        Args:
            name: Unique name for the evaluator
            evaluator: Function that produces Evidence from pattern matches

        Raises:
            ValueError: If name is already registered
        """
        if name in self._evaluators:
            raise ValueError(f"Plugin already registered: {name}")
        self._evaluators[name] = evaluator

    def get(self, name: str) -> PatternEvaluator:
        """
        Get a registered evaluator by name.

        Args:
            name: Name of the evaluator

        Returns:
            The evaluator function

        Raises:
            KeyError: If evaluator not found
        """
        try:
            return self._evaluators[name]
        except KeyError as e:
            raise KeyError(f"Unknown plugin evaluator: {name}") from e

    def list_evaluators(self) -> list[str]:
        """Get list of all registered evaluator names."""
        return sorted(self._evaluators.keys())

    # Built-in evaluators

    def _logistic_default(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Evidence:
        """
        Default logistic confidence function for functional patterns.

        Uses a sigmoid curve based on pattern weight and context features.
        """
        # Extract basic info from pattern and context
        pattern_weight = pattern.get("evidence", {}).get("weight", 0.5)
        span = context.get("span", (0, 1))
        pattern_id = pattern.get("id", "unknown")

        # Simple scoring based on pattern weight
        # In future iterations, this will use actual features
        raw_score = pattern_weight

        # Build evidence
        return Evidence(
            pattern_id=pattern_id,
            track_weights={"functional": pattern_weight},
            features={"pattern_weight": pattern_weight},
            raw_score=raw_score,
            uncertainty=None,
            span=tuple(span),
        )

    def _logistic_dorian(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Evidence:
        """
        Dorian-specific confidence function for modal patterns.

        Emphasizes modal characteristics and de-emphasizes functional markers.
        """
        pattern_weight = pattern.get("evidence", {}).get("weight", 0.7)
        span = context.get("span", (0, 1))
        pattern_id = pattern.get("id", "unknown")

        # Modal patterns get higher modal weight, lower functional weight
        return Evidence(
            pattern_id=pattern_id,
            track_weights={"modal": pattern_weight, "functional": pattern_weight * 0.3},
            features={"modal_char_score": pattern_weight, "pattern_weight": pattern_weight},
            raw_score=pattern_weight,
            uncertainty=None,
            span=tuple(span),
        )

    def _identity_evaluator(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Evidence:
        """
        Identity evaluator that passes through raw scores unchanged.

        Used as fallback when no calibration is available.
        """
        pattern_weight = pattern.get("evidence", {}).get("weight", 0.5)
        span = context.get("span", (0, 1))
        pattern_id = pattern.get("id", "unknown")

        # Get track contributions from pattern config
        tracks = pattern.get("track", ["functional"])
        track_weights = {track: pattern_weight for track in tracks}

        return Evidence(
            pattern_id=pattern_id,
            track_weights=track_weights,
            features={"identity": 1.0},
            raw_score=pattern_weight,
            uncertainty=None,
            span=tuple(span),
        )