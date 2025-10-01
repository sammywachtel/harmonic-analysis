"""
Calibration module with quality gates for pattern engine.

This module implements confidence calibration with strict quality gates
to prevent degradation when signal is insufficient.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional

import numpy as np

if TYPE_CHECKING:
    # For type checking, import sklearn types
    from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]
    from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
else:
    # At runtime, import sklearn normally but handle missing stubs
    from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]
    from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]


@dataclass(frozen=True)
class CalibrationMetrics:
    """Metrics for evaluating calibration quality."""

    ece: float  # Expected Calibration Error
    brier: float  # Brier score
    correlation: float  # Correlation between raw and targets
    variance: float  # Variance in targets
    sample_count: int  # Number of samples


@dataclass(frozen=True)
class CalibrationReport:
    """Comprehensive calibration evaluation report."""

    baseline_metrics: CalibrationMetrics  # Pre-calibration metrics
    calibrated_metrics: CalibrationMetrics  # Post-calibration metrics
    mapping_type: str  # Type of calibration applied
    passed_quality_gates: bool  # Whether quality gates were passed
    improvement_summary: Dict[str, float]  # Metric improvements
    reliability_bins: Dict[str, List[float]]  # Reliability curve data
    warnings: List[str]  # Quality warnings


@dataclass(frozen=True)
class CalibrationMapping:
    """
    Calibration mapping function with metadata.

    Tracks whether mapping passed quality gates and provides
    fallback to identity when needed.
    """

    mapping_type: str  # "identity", "platt", "isotonic"
    params: dict  # Parameters for the mapping
    metrics: CalibrationMetrics
    passed_gates: bool

    def apply(self, x: float) -> float:
        """
        Apply calibration mapping to a confidence score.

        Args:
            x: Raw confidence score (0.0-1.0)

        Returns:
            Calibrated confidence score
        """
        if self.mapping_type == "identity" or not self.passed_gates:
            return x

        elif self.mapping_type == "platt":
            # Apply Platt scaling (logistic regression)
            A = self.params.get("A", 0.0)
            B = self.params.get("B", 1.0)
            # Sigmoid: 1 / (1 + exp(-(Ax + B)))
            return float(1.0 / (1.0 + np.exp(-(A * x + B))))

        elif self.mapping_type == "isotonic":
            # Apply isotonic regression mapping
            X = self.params.get("X", [])
            Y = self.params.get("Y", [])
            if not X or not Y:
                return x

            # Linear interpolation for isotonic mapping
            return float(np.interp(x, X, Y))

        else:
            # Unknown mapping type - fallback to identity
            return x


class Calibrator:
    """
    Calibrator with quality gates for confidence mapping.

    Implements strict quality checks to prevent calibration
    when insufficient signal exists in the data.
    """

    def __init__(
        self,
        min_correlation: float = 0.1,
        min_samples: int = 50,
        min_variance: float = 0.01,
        max_ece_increase: float = 0.05,
    ):
        """
        Initialize calibrator with quality gate thresholds.

        Args:
            min_correlation: Minimum |correlation| required
            min_samples: Minimum sample count required
            min_variance: Minimum target variance required
            max_ece_increase: Maximum allowed ECE increase
        """
        self.min_correlation = min_correlation
        self.min_samples = min_samples
        self.min_variance = min_variance
        self.max_ece_increase = max_ece_increase

    def fit(
        self,
        raw_scores: Iterable[float],
        targets: Iterable[float],
        method: str = "auto",
    ) -> CalibrationMapping:
        """
        Fit calibration mapping with quality gates.

        Args:
            raw_scores: Raw confidence scores
            targets: Target reliability values
            method: Calibration method ("auto", "platt", "isotonic", "identity")

        Returns:
            CalibrationMapping that passes quality gates or identity
        """
        # Convert to arrays and validate
        raw_scores = np.array(list(raw_scores))
        targets = np.array(list(targets))

        # Validate input lengths match
        if len(raw_scores) != len(targets):
            return CalibrationMapping(
                mapping_type="identity",
                params={},
                metrics=CalibrationMetrics(
                    ece=1.0, brier=1.0, correlation=0.0, variance=0.0, sample_count=0
                ),
                passed_gates=False,
            )

        # Calculate baseline metrics
        metrics = self._calculate_metrics(raw_scores, targets)

        # Check quality gates
        gates_passed = self._check_quality_gates(metrics)

        if not gates_passed or method == "identity":
            # Return identity mapping
            return CalibrationMapping(
                mapping_type="identity",
                params={},
                metrics=metrics,
                passed_gates=False,
            )

        # Fit calibration based on method
        if method == "auto":
            # Try methods in order of complexity
            for try_method in ["platt", "isotonic"]:
                mapping = self._fit_method(try_method, raw_scores, targets, metrics)
                if mapping and self._validate_mapping(mapping, raw_scores, targets):
                    return mapping
            # Fallback to identity if nothing works
            return CalibrationMapping(
                mapping_type="identity",
                params={},
                metrics=metrics,
                passed_gates=False,
            )

        else:
            # Fit specific method
            mapping = self._fit_method(method, raw_scores, targets, metrics)
            if mapping and self._validate_mapping(mapping, raw_scores, targets):
                return mapping
            else:
                # Fallback to identity
                return CalibrationMapping(
                    mapping_type="identity",
                    params={},
                    metrics=metrics,
                    passed_gates=False,
                )

    def _calculate_metrics(
        self, raw_scores: np.ndarray, targets: np.ndarray
    ) -> CalibrationMetrics:
        """Calculate calibration metrics."""
        # Handle edge cases
        if len(raw_scores) == 0:
            return CalibrationMetrics(
                ece=1.0,
                brier=1.0,
                correlation=0.0,
                variance=0.0,
                sample_count=0,
            )

        # Correlation
        if len(set(raw_scores)) > 1 and len(set(targets)) > 1:
            correlation = np.corrcoef(raw_scores, targets)[0, 1]
        else:
            correlation = 0.0

        # Variance
        variance = np.var(targets)

        # ECE (Expected Calibration Error)
        ece = self._calculate_ece(raw_scores, targets)

        # Brier score
        brier = np.mean((raw_scores - targets) ** 2)

        return CalibrationMetrics(
            ece=ece,
            brier=brier,
            correlation=correlation if not np.isnan(correlation) else 0.0,
            variance=variance,
            sample_count=len(raw_scores),
        )

    def _calculate_ece(
        self, predictions: np.ndarray, targets: np.ndarray, n_bins: int = 10
    ) -> float:
        """
        Calculate Expected Calibration Error.

        Args:
            predictions: Predicted probabilities
            targets: True binary outcomes or probabilities
            n_bins: Number of bins for calibration

        Returns:
            ECE value
        """
        if len(predictions) == 0:
            return 1.0

        # Create bins
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        ece = 0.0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Find predictions in this bin
            in_bin = (predictions > bin_lower) & (predictions <= bin_upper)
            if not np.any(in_bin):
                continue

            # Calculate accuracy and confidence in bin
            bin_accuracy = np.mean(targets[in_bin])
            bin_confidence = np.mean(predictions[in_bin])
            bin_size = np.sum(in_bin)

            # Weighted ECE contribution
            ece += (bin_size / len(predictions)) * abs(bin_accuracy - bin_confidence)

        return ece

    def _check_quality_gates(self, metrics: CalibrationMetrics) -> bool:
        """Check if metrics pass quality gates."""
        # Sample count gate
        if metrics.sample_count < self.min_samples:
            return False

        # Variance gate
        if metrics.variance < self.min_variance:
            return False

        # Correlation gate
        if abs(metrics.correlation) < self.min_correlation:
            return False

        return True

    def _fit_method(
        self,
        method: str,
        raw_scores: np.ndarray,
        targets: np.ndarray,
        baseline_metrics: CalibrationMetrics,
    ) -> Optional[CalibrationMapping]:
        """Fit a specific calibration method."""
        try:
            if method == "platt":
                # Fit Platt scaling (logistic regression)
                lr = LogisticRegression(solver="lbfgs", max_iter=1000)
                lr.fit(raw_scores.reshape(-1, 1), targets)

                # Extract parameters
                A = float(lr.coef_[0])
                B = float(lr.intercept_[0])

                return CalibrationMapping(
                    mapping_type="platt",
                    params={"A": A, "B": B},
                    metrics=baseline_metrics,
                    passed_gates=True,
                )

            elif method == "isotonic":
                # Fit isotonic regression
                iso = IsotonicRegression(out_of_bounds="clip")
                iso.fit(raw_scores, targets)

                # Extract mapping points
                X = list(iso.X_thresholds_)
                Y = list(iso.y_thresholds_)

                return CalibrationMapping(
                    mapping_type="isotonic",
                    params={"X": X, "Y": Y},
                    metrics=baseline_metrics,
                    passed_gates=True,
                )

            else:
                return None

        except Exception:
            # Fitting failed - return None
            return None

    def _validate_mapping(
        self,
        mapping: CalibrationMapping,
        raw_scores: np.ndarray,
        targets: np.ndarray,
    ) -> bool:
        """
        Validate that mapping doesn't degrade calibration.

        Args:
            mapping: Fitted mapping
            raw_scores: Original scores
            targets: Target values

        Returns:
            True if mapping is acceptable
        """
        # Apply mapping
        calibrated = np.array([mapping.apply(x) for x in raw_scores])

        # Calculate new ECE
        new_ece = self._calculate_ece(calibrated, targets)

        # Check if ECE increased too much
        ece_increase = new_ece - mapping.metrics.ece
        if ece_increase > self.max_ece_increase:
            return False

        # Check for monotonicity (calibration should preserve ranking)
        if len(raw_scores) > 1:
            # Sort by raw scores
            sorted_indices = np.argsort(raw_scores)
            # sorted_raw = raw_scores[sorted_indices]  # Not used
            sorted_calibrated = calibrated[sorted_indices]

            # Check if calibrated scores are also sorted (allowing small violations)
            differences = np.diff(sorted_calibrated)
            violations = np.sum(differences < -0.01)  # Small tolerance
            if violations > len(differences) * 0.1:  # Allow 10% violations
                return False

        return True

    def evaluate_calibration(
        self,
        raw_scores: Iterable[float],
        targets: Iterable[float],
        mapping: Optional[CalibrationMapping] = None,
    ) -> CalibrationReport:
        """
        Generate comprehensive calibration evaluation report.

        Args:
            raw_scores: Raw confidence scores
            targets: Target reliability values
            mapping: Optional calibration mapping to evaluate

        Returns:
            Detailed calibration report with metrics and analysis
        """
        raw_scores = np.array(list(raw_scores))
        targets = np.array(list(targets))

        # Calculate baseline metrics
        baseline_metrics = self._calculate_metrics(raw_scores, targets)

        # Apply calibration if mapping provided
        if mapping:
            calibrated_scores = np.array([mapping.apply(x) for x in raw_scores])
            calibrated_metrics = self._calculate_metrics(calibrated_scores, targets)
            mapping_type = mapping.mapping_type
            passed_gates = mapping.passed_gates
        else:
            calibrated_metrics = baseline_metrics
            mapping_type = "none"
            passed_gates = False

        # Calculate improvements
        improvement_summary = {
            "ece_improvement": baseline_metrics.ece - calibrated_metrics.ece,
            "brier_improvement": baseline_metrics.brier - calibrated_metrics.brier,
            "correlation_improvement": calibrated_metrics.correlation
            - baseline_metrics.correlation,
        }

        # Generate reliability curve data
        reliability_bins = self._generate_reliability_curve(
            raw_scores, targets, n_bins=10
        )

        # Generate quality warnings
        warnings = []
        if baseline_metrics.sample_count < self.min_samples:
            warnings.append(
                f"Sample count ({baseline_metrics.sample_count}) below "
                f"minimum ({self.min_samples})"
            )
        if baseline_metrics.variance < self.min_variance:
            warnings.append(
                f"Target variance ({baseline_metrics.variance:.4f}) below "
                f"minimum ({self.min_variance})"
            )
        if abs(baseline_metrics.correlation) < self.min_correlation:
            warnings.append(
                f"Correlation ({baseline_metrics.correlation:.4f}) below "
                f"minimum ({self.min_correlation})"
            )
        if improvement_summary["ece_improvement"] < 0:
            warnings.append("Calibration increased ECE (degraded calibration)")

        return CalibrationReport(
            baseline_metrics=baseline_metrics,
            calibrated_metrics=calibrated_metrics,
            mapping_type=mapping_type,
            passed_quality_gates=passed_gates,
            improvement_summary=improvement_summary,
            reliability_bins=reliability_bins,
            warnings=warnings,
        )

    def _generate_reliability_curve(
        self, predictions: np.ndarray, targets: np.ndarray, n_bins: int = 10
    ) -> Dict[str, List[float]]:
        """Generate reliability curve data for plotting."""
        if len(predictions) == 0:
            return {
                "bin_centers": [],
                "reliability": [],
                "confidence": [],
                "counts": [],
            }

        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_centers = []
        reliability = []
        confidence = []
        counts = []

        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            # Find predictions in this bin
            if i == n_bins - 1:  # Last bin includes right boundary
                in_bin = (predictions >= bin_lower) & (predictions <= bin_upper)
            else:
                in_bin = (predictions >= bin_lower) & (predictions < bin_upper)

            if np.sum(in_bin) > 0:
                bin_centers.append((bin_lower + bin_upper) / 2)
                reliability.append(np.mean(targets[in_bin]))
                confidence.append(np.mean(predictions[in_bin]))
                counts.append(np.sum(in_bin))

        return {
            "bin_centers": bin_centers,
            "reliability": reliability,
            "confidence": confidence,
            "counts": counts,
        }
