#!/usr/bin/env python3
"""
Confidence Calibration Service for Harmonic Analysis

This service applies sophisticated 4-stage confidence calibration to improve the
reliability of harmonic analysis confidence scores. It implements the advanced
calibration pipeline described in music-alg-3a-calibration.md.

## 4-Stage Calibration Pipeline:

**Stage 0: Data Hygiene**
- Deduplication and evidence filtering
- Stratified cross-validation setup
- Value clamping and winsorization

**Stage 1: Platt Scaling (Global Bias Correction)**
- Logistic calibration: y = sigmoid(a * logit(x) + b)
- Corrects systematic over/under-confidence
- Applied globally per track (functional/modal)

**Stage 2: Isotonic Regression (Shape Correction)**
- Non-linear monotonic mapping
- Corrects calibration curve shape distortions
- Preserves rank ordering of confidences

**Stage 3: Bucket Models (Variance Control)**
- Route progressions to specialized buckets:
  - functional_simple: Basic I-V-I patterns
  - modal_marked: Clear modal characteristics (b7, modal patterns)
  - chromatic_borrowed: Non-diatonic elements
  - ambiguous_sparse: Short/unclear progressions
  - melodic_short: Scale/melody analysis
- Apply bucket-specific calibration parameters

**Stage 4: Uncertainty-Aware Adjustment**
- Compute uncertainty scores from routing features
- Down-weight confidence for high-uncertainty cases
- Shrink uncertain predictions toward 0.5

## Usage:

```python
# Initialize with calibration mapping
service = CalibrationService("path/to/calibration_mapping.json")

# Calibrate a confidence score
features = {
    "chord_count": 4,
    "is_melody": False,
    "outside_key_ratio": 0.1,
    "evidence_strength": 0.8,
    "foil_I_V_I": True
}

calibrated = service.calibrate_confidence(
    raw_confidence=0.85,
    track="functional",  # or "modal", "melody"
    features=features
)
```

## Routing Features:

**Harmony Features:**
- chord_count: Number of chords in progression
- outside_key_ratio: Ratio of non-diatonic elements
- evidence_strength: Strength of harmonic evidence
- foil_I_V_I: Whether progression matches I-V-I pattern
- has_flat7, has_flat3, etc.: Modal characteristic markers
- chord_density: Harmonic complexity measure

**Melody Features:**
- is_melody: Boolean flag for melody vs harmony
- note_count: Number of notes in melody
- ks_gap: Key signature similarity gap
- cadence_strength: Strength of melodic cadences
- chromatic_runs: Count of chromatic passages

Author: Claude Code
Version: 1.0.0
Last Updated: 2025-09-13
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class CalibrationService:
    """
    Production-ready confidence calibration service.

    This service implements a sophisticated 4-stage calibration pipeline that
    significantly improves confidence score reliability by correcting bias,
    shape distortions, and uncertainty-related issues.

    Key Features:
    - Pure Python implementation (no external ML dependencies at runtime)
    - Bucket-based routing for specialized calibration
    - Uncertainty-aware confidence adjustment
    - Comprehensive error handling and validation
    - Detailed debugging and introspection capabilities

    Performance:
    - Target: MAE ≤ 0.10 (Mean Absolute Error)
    - Target: Bias ±0.05 (systematic offset)
    - Handles 10+ progression types with specialized calibration
    """

    def __init__(self, mapping_path: Optional[str] = None):
        """
        Initialize calibration service.

        Args:
            mapping_path: Path to calibration mapping JSON file.
                         If None, service operates in pass-through mode.

        Example:
            service = CalibrationService("assets/calibration_mapping.json")
        """
        self.mapping: Dict[str, Any] = {}
        self.is_loaded = False

        if mapping_path:
            try:
                self.load_mapping(mapping_path)
            except Exception as e:
                raise ValueError(
                    f"Failed to load calibration mapping from {mapping_path}: {e}"
                )

    def load_mapping(self, mapping_path: str) -> None:
        """
        Load and validate calibration mapping from JSON file.

        Args:
            mapping_path: Path to calibration mapping JSON

        Raises:
            FileNotFoundError: If mapping file doesn't exist
            ValueError: If mapping format is invalid

        Expected JSON Schema:
        {
            "version": "2025-09-13-advanced",
            "created_at": "2025-09-13T...",
            "tracks": {
                "functional": {
                    "GLOBAL": {"platt": {...}, "isotonic": {...}, "uncertainty": {...}},
                    "buckets": {"bucket_name": {...}}
                },
                "modal": {...}
            }
        }
        """
        path_obj = Path(mapping_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Calibration mapping not found: {mapping_path}")

        with open(path_obj, "r") as f:
            self.mapping = json.load(f)

        # Validate mapping structure
        if not isinstance(self.mapping, dict):
            raise ValueError("Calibration mapping must be a JSON object")

        if "tracks" not in self.mapping:
            raise ValueError("Calibration mapping missing 'tracks' section")

        tracks = self.mapping["tracks"]
        if not isinstance(tracks, dict):
            raise ValueError("'tracks' section must be a dictionary")

        # Validate each track has required structure
        for track_name, track_data in tracks.items():
            if not isinstance(track_data, dict):
                raise ValueError(f"Track '{track_name}' must be a dictionary")
            if "GLOBAL" not in track_data:
                raise ValueError(f"Track '{track_name}' missing 'GLOBAL' configuration")

        self.is_loaded = True
        print(
            f"✅ Loaded calibration mapping: {len(tracks)} tracks, version"
            f" {self.mapping.get('version', 'unknown')}"
        )

    def route_bucket(self, track: str, features: Dict[str, Any]) -> str:
        """
        Route progression to appropriate calibration bucket based on musical
        characteristics.

        This implements the Stage 3 bucket routing logic that routes different types of
        progressions to specialized calibration models for improved accuracy.

        Args:
            track: Analysis track ("functional", "modal", "melody")
            features: Dictionary of routing features extracted from the progression

        Returns:
            Bucket name for specialized calibration

        Routing Logic:
        - melodic_short: Melodies with < 8 notes
        - functional_simple: Basic I-V-I progressions with ≤ 4 chords
        - modal_marked: Progressions with modal characteristics (b7, #4, b3, b6)
        - chromatic_borrowed: High outside-key ratio or chromatic elements
        - secondary_dominant: High chord density suggesting V/V patterns
        - ambiguous_sparse: Short progressions (< 4 chords) without clear patterns
        """
        if features.get("is_melody", False):
            # Melody routing
            note_count = features.get("note_count", 0)
            if note_count < 8:
                return "melodic_short"
            ks_gap = features.get("ks_gap", 0.0)
            if ks_gap < 0.1:
                return "melodic_ambiguous"
            chromatic_ratio = features.get("outside_key_ratio", 0.0)
            if chromatic_ratio > 0.3:
                return "melodic_chromatic"
            return "melodic_clear"
        else:
            # Harmony routing
            chord_count = features.get("chord_count", 0)
            outside_key_ratio = features.get("outside_key_ratio", 0.0)

            # Simple progressions
            if features.get("foil_I_V_I", False) and chord_count <= 4:
                return "functional_simple"

            # Modal characteristics
            modal_markers = ["has_flat7", "has_sharp4", "has_flat3", "has_flat6"]
            if any(features.get(marker, False) for marker in modal_markers):
                return "modal_marked"

            # Chromatic/borrowed elements
            if (
                outside_key_ratio > 0.2
                or features.get("has_flat2", False)
                or features.get("has_flat5", False)
            ):
                return "chromatic_borrowed"

            # Secondary dominants (placeholder - would need better detection)
            if features.get("chord_density", 0.0) > 0.8:
                return "secondary_dominant"

            # Sparse/ambiguous
            if chord_count < 4:
                return "ambiguous_sparse"

            return "functional_simple"

    def apply_platt_scaling(
        self, confidence: float, platt_params: Dict[str, float]
    ) -> float:
        """
        Apply Platt scaling for global bias correction (Stage 1).

        Platt scaling applies a logistic transformation: y = sigmoid(a * logit(x) + b)
        This corrects systematic over-confidence or under-confidence in the model.

        Args:
            confidence: Raw confidence score in [0,1]
            platt_params: Dictionary with 'a' (slope) and 'b' (intercept) parameters

        Returns:
            Bias-corrected confidence in [0,1]

        Mathematical Details:
        - Convert confidence to logit space: logit(p) = log(p / (1-p))
        - Apply linear transformation: logit_cal = a * logit(p) + b
        - Convert back to probability: p_cal = sigmoid(logit_cal)
        """
        if not platt_params:
            return confidence

        a = platt_params.get("a", 1.0)
        b = platt_params.get("b", 0.0)

        # Convert to logit, apply linear transformation, convert back
        epsilon = 1e-6
        confidence = max(epsilon, min(1.0 - epsilon, confidence))
        logit = math.log(confidence / (1.0 - confidence))
        calibrated_logit = a * logit + b
        calibrated = 1.0 / (1.0 + math.exp(-calibrated_logit))

        return calibrated

    def apply_isotonic_regression(
        self, confidence: float, isotonic_params: Dict[str, List[float]]
    ) -> float:
        """
        Apply isotonic regression for shape correction (Stage 2).

        Isotonic regression creates a monotonic mapping that corrects calibration curve
        shape while preserving the rank ordering of confidence scores.

        Args:
            confidence: Platt-scaled confidence score
            isotonic_params: Dictionary with 'x' (input points) and 'y' (output points)

        Returns:
            Shape-corrected confidence via piecewise linear interpolation

        Implementation:
        - Uses learned breakpoints from isotonic regression training
        - Performs linear interpolation between adjacent breakpoints
        - Clamps values outside the learned range to boundary values
        """
        if (
            not isotonic_params
            or "x" not in isotonic_params
            or "y" not in isotonic_params
        ):
            return confidence

        x_points = isotonic_params["x"]
        y_points = isotonic_params["y"]

        if len(x_points) != len(y_points) or len(x_points) < 2:
            return confidence

        # Clamp to range
        if confidence <= x_points[0]:
            return y_points[0]
        if confidence >= x_points[-1]:
            return y_points[-1]

        # Find the interval and interpolate
        for i in range(len(x_points) - 1):
            if x_points[i] <= confidence <= x_points[i + 1]:
                # Linear interpolation
                t = (confidence - x_points[i]) / (x_points[i + 1] - x_points[i])
                return y_points[i] + t * (y_points[i + 1] - y_points[i])

        return confidence

    def compute_uncertainty(self, track: str, features: Dict[str, Any]) -> float:
        """
        Compute uncertainty score for Stage 4 adjustment.

        Uncertainty estimation based on musical characteristics that correlate with
        analysis difficulty and ambiguity. Higher uncertainty leads to more conservative
        (closer to 0.5) confidence scores.

        Args:
            track: Analysis track ("functional", "modal", "melody")
            features: Dictionary of routing features

        Returns:
            Uncertainty score in [0,1] where:
            - 0.0: Very certain (clear, unambiguous progression)
            - 1.0: Very uncertain (sparse, ambiguous, or complex progression)

        Uncertainty Factors:
        **Melody:**
        - Key signature gap (lower = more uncertain)
        - Note count (fewer = more uncertain)
        - Cadence strength (weaker = more uncertain)

        **Harmony:**
        - Outside-key ratio (higher = more uncertain)
        - Evidence strength (lower = more uncertain)
        - Chord count (fewer = more uncertain)
        """
        if features.get("is_melody", False):
            # Melody uncertainty
            ks_gap = features.get("ks_gap", 1.0)
            note_count = features.get("note_count", 12)
            cadence_strength = features.get("cadence_strength", 0.0)

            uncertainty = (
                (1.0 - ks_gap)
                + (1.0 / (1.0 + note_count / 4.0))
                + (1.0 - cadence_strength)
            )
            return float(min(uncertainty / 3.0, 1.0))  # Normalize
        else:
            # Harmony uncertainty
            outside_key_ratio = features.get("outside_key_ratio", 0.0)
            evidence_strength = features.get("evidence_strength", 1.0)
            chord_count = features.get("chord_count", 4)

            # More outside-key notes = more uncertain
            # Fewer chords = more uncertain
            # Lower evidence strength = more uncertain
            uncertainty = (
                outside_key_ratio
                + (1.0 / (1.0 + evidence_strength))
                + (1.0 / (1.0 + chord_count / 4.0))
            )
            return float(min(uncertainty / 3.0, 1.0))  # Normalize

    def apply_uncertainty_adjustment(
        self,
        confidence: float,
        track: str,
        features: Dict[str, Any],
        uncertainty_params: Dict[str, float],
    ) -> float:
        """
        Apply uncertainty-aware confidence adjustment (Stage 4).

        This stage shrinks confidence scores toward 0.5 for high-uncertainty cases,
        making the model more conservative when analysis is difficult or ambiguous.

        Args:
            confidence: Shape-corrected confidence from Stage 2
            track: Analysis track
            features: Routing features for uncertainty computation
            uncertainty_params: Learned parameters with 'alpha' and 'lambda_max'

        Returns:
            Uncertainty-adjusted final confidence

        Formula:
        - uncertainty = compute_uncertainty(track, features)
        - lambda = min(alpha * uncertainty, lambda_max)
        - adjusted = (1 - lambda) * confidence + lambda * 0.5

        This ensures high-uncertainty predictions are more conservative while
        preserving confident predictions for clear cases.
        """
        if not uncertainty_params:
            return confidence

        alpha = uncertainty_params.get("alpha", 0.5)
        lambda_max = uncertainty_params.get("lambda_max", 0.25)

        uncertainty = self.compute_uncertainty(track, features)
        lambda_val = min(alpha * uncertainty, lambda_max)

        # Shrink toward 0.5
        adjusted = (1.0 - lambda_val) * confidence + lambda_val * 0.5
        return adjusted

    def calibrate_confidence(
        self, raw_confidence: float, track: str, features: Dict[str, Any]
    ) -> float:
        """
        Apply complete 4-stage calibration pipeline to a raw confidence score.

        This is the main entry point for confidence calibration. It applies all four
        calibration stages in sequence to produce a well-calibrated confidence score.

        Args:
            raw_confidence: Raw model confidence in [0,1] from analysis engine
            track: Analysis track - one of:
                  - "functional": Functional harmony analysis
                  - "modal": Modal analysis
                  - "melody": Scale/melody analysis
            features: Dictionary of routing features used for bucket classification
                     and uncertainty estimation. See class docstring for feature list.

        Returns:
            Calibrated confidence in [0,1] with improved reliability

        Pipeline Stages:
        1. **Bucket Routing**: Route to specialized calibration bucket
        2. **Platt Scaling**: Apply logistic bias correction
        3. **Isotonic Regression**: Apply shape correction
        4. **Uncertainty Adjustment**: Shrink uncertain predictions toward 0.5

        Example:
            features = {
                "chord_count": 4,
                "outside_key_ratio": 0.1,
                "evidence_strength": 0.8,
                "foil_I_V_I": True,
                "has_flat7": False
            }

            calibrated = service.calibrate_confidence(0.85, "functional", features)

        Fallback Behavior:
        If no calibration mapping is loaded, returns clamped raw confidence.
        """
        # Validate inputs
        if not isinstance(raw_confidence, (int, float)):
            raise ValueError(
                f"raw_confidence must be numeric, got {type(raw_confidence)}"
            )
        if not 0.0 <= raw_confidence <= 1.0:
            raise ValueError(f"raw_confidence must be in [0,1], got {raw_confidence}")
        if track not in ["functional", "modal", "melody"]:
            raise ValueError(
                f"track must be 'functional', 'modal', or 'melody', got '{track}'"
            )
        if not isinstance(features, dict):
            raise ValueError(f"features must be a dictionary, got {type(features)}")

        # Fallback if no mapping loaded or track not found
        if not self.mapping or track not in self.mapping.get("tracks", {}):
            if not self.is_loaded:
                print("⚠️ No calibration mapping loaded, using raw confidence")
            return max(1e-4, min(1.0 - 1e-4, raw_confidence))

        # Route to bucket
        bucket = self.route_bucket(track, features)

        # Get mapping for this track/bucket combination
        track_mapping = self.mapping["tracks"][track]

        # Try bucket-specific mapping first, fall back to GLOBAL
        if "buckets" in track_mapping and bucket in track_mapping["buckets"]:
            mapping = track_mapping["buckets"][bucket]
        else:
            mapping = track_mapping.get("GLOBAL", {})

        confidence = raw_confidence

        # Stage 1: Platt scaling (bias correction)
        if "platt" in mapping:
            confidence = self.apply_platt_scaling(confidence, mapping["platt"])

        # Stage 2: Isotonic regression (shape correction)
        if "isotonic" in mapping:
            confidence = self.apply_isotonic_regression(confidence, mapping["isotonic"])

        # Stage 4: Uncertainty adjustment (Stage 3 is handled by bucket routing)
        uncertainty_params = mapping.get("uncertainty") or track_mapping.get(
            "GLOBAL", {}
        ).get("uncertainty", {})

        # Skip uncertainty adjustment if using identity mapping
        if uncertainty_params and uncertainty_params.get("method") != "identity":
            confidence = self.apply_uncertainty_adjustment(
                confidence, track, features, uncertainty_params
            )

        # Final clamping
        return max(1e-4, min(1.0 - 1e-4, confidence))

    def get_bucket_info(self, track: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed bucket routing information for debugging and analysis.

        This method provides introspection into the calibration process, showing
        which bucket was selected and what calibration parameters will be used.

        Args:
            track: Analysis track
            features: Routing features dictionary

        Returns:
            Dictionary with routing details:
            - track: Analysis track used
            - bucket: Selected calibration bucket
            - uncertainty: Computed uncertainty score
            - features: Input features (for reference)
            - has_bucket_mapping: Whether bucket-specific calibration exists
            - uses_global: Whether falling back to GLOBAL calibration

        Example Output:
            {
                "track": "functional",
                "bucket": "chromatic_borrowed",
                "uncertainty": 0.23,
                "features": {...},
                "has_bucket_mapping": True,
                "uses_global": False
            }
        """
        bucket = self.route_bucket(track, features)
        uncertainty = self.compute_uncertainty(track, features)

        return {
            "track": track,
            "bucket": bucket,
            "uncertainty": uncertainty,
            "features": features,
            "has_bucket_mapping": (
                track in self.mapping.get("tracks", {})
                and "buckets" in self.mapping["tracks"][track]
                and bucket in self.mapping["tracks"][track]["buckets"]
            ),
            "uses_global": not (
                track in self.mapping.get("tracks", {})
                and "buckets" in self.mapping["tracks"][track]
                and bucket in self.mapping["tracks"][track]["buckets"]
            ),
        }

    def get_available_tracks(self) -> List[str]:
        """
        Get list of available calibration tracks.

        Returns:
            List of track names that have calibration mappings loaded

        Example:
            tracks = service.get_available_tracks()
            # Returns: ["functional", "modal"]
        """
        if not self.mapping or "tracks" not in self.mapping:
            return []
        return list(self.mapping["tracks"].keys())

    def get_available_buckets(self, track: str) -> List[str]:
        """
        Get list of available calibration buckets for a track.

        Args:
            track: Analysis track name

        Returns:
            List of bucket names with specialized calibration

        Example:
            buckets = service.get_available_buckets("functional")
            # Returns: ["chromatic_borrowed", "modal_marked"]
        """
        if (
            not self.mapping
            or "tracks" not in self.mapping
            or track not in self.mapping["tracks"]
            or "buckets" not in self.mapping["tracks"][track]
        ):
            return []
        return list(self.mapping["tracks"][track]["buckets"].keys())

    def validate_features(self, features: Dict[str, Any]) -> List[str]:
        """
        Validate routing features and return list of warnings.

        Args:
            features: Feature dictionary to validate

        Returns:
            List of warning messages (empty if all valid)

        Example:
            warnings = service.validate_features(features)
            if warnings:
                print("Feature warnings:", warnings)
        """
        warnings = []

        # Required vs recommended features based on is_melody flag
        if features.get("is_melody", False):
            # Melody features
            recommended = ["note_count", "ks_gap", "cadence_strength"]
            for feature in recommended:
                if feature not in features:
                    warnings.append(f"Missing recommended melody feature: {feature}")

            # Validate note_count
            note_count = features.get("note_count", 0)
            if not isinstance(note_count, (int, float)) or note_count < 0:
                warnings.append(
                    f"Invalid note_count: {note_count} (should be positive number)"
                )

        else:
            # Harmony features
            recommended = ["chord_count", "outside_key_ratio", "evidence_strength"]
            for feature in recommended:
                if feature not in features:
                    warnings.append(f"Missing recommended harmony feature: {feature}")

            # Validate chord_count
            chord_count = features.get("chord_count", 0)
            if not isinstance(chord_count, (int, float)) or chord_count < 1:
                warnings.append(f"Invalid chord_count: {chord_count} (should be >= 1)")

            # Validate ratios are in [0,1]
            for ratio_field in ["outside_key_ratio", "evidence_strength"]:
                if ratio_field in features:
                    value = features[ratio_field]
                    if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                        warnings.append(
                            f"Invalid {ratio_field}: {value} (should be in [0,1])"
                        )

        return warnings

    def get_calibration_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded calibration mapping.

        Returns:
            Dictionary with calibration mapping statistics

        Example Output:
            {
                "version": "2025-09-13-advanced",
                "created_at": "2025-09-13T...",
                "total_tracks": 2,
                "total_buckets": 3,
                "tracks": {
                    "functional": {"global": True, "buckets": ["chromatic_borrowed"]},
                    "modal": {"global": True, "buckets": ["chromatic_borrowed"]}
                }
            }
        """
        if not self.mapping:
            return {"loaded": False, "error": "No calibration mapping loaded"}

        stats = {
            "loaded": True,
            "version": self.mapping.get("version", "unknown"),
            "created_at": self.mapping.get("created_at", "unknown"),
            "total_tracks": 0,
            "total_buckets": 0,
            "tracks": {},
        }

        if "tracks" in self.mapping:
            tracks = self.mapping["tracks"]
            stats["total_tracks"] = len(tracks)

            total_buckets = 0
            for track_name, track_data in tracks.items():
                buckets = list(track_data.get("buckets", {}).keys())
                total_buckets += len(buckets)
                stats["tracks"][track_name] = {
                    "global": "GLOBAL" in track_data,
                    "buckets": buckets,
                }

            stats["total_buckets"] = total_buckets

        return stats


# Convenience function for standalone usage
def calibrate_confidence(
    raw_confidence: float,
    track: str,
    features: Dict[str, Any],
    mapping_path: Optional[str] = None,
) -> float:
    """Standalone function to calibrate a single confidence value."""
    service = CalibrationService(mapping_path)
    return service.calibrate_confidence(raw_confidence, track, features)


if __name__ == "__main__":
    """
    Comprehensive test suite for CalibrationService.

    Run this module directly to test all functionality:
    python -m harmonic_analysis.services.calibration_service
    """
    print("🧪 Testing CalibrationService")
    print("=" * 50)

    # Test 1: Basic initialization and stats
    print("\n1️⃣ Testing initialization...")
    service = CalibrationService()
    stats = service.get_calibration_stats()
    print(f"Stats without mapping: {stats}")

    # Test 2: Feature validation
    print("\n2️⃣ Testing feature validation...")

    # Valid harmony features
    harmony_features = {
        "chord_count": 4,
        "is_melody": False,
        "outside_key_ratio": 0.1,
        "evidence_strength": 0.8,
        "foil_I_V_I": True,
        "has_flat7": False,
        "chord_density": 0.6,
    }

    warnings = service.validate_features(harmony_features)
    print(f"Harmony feature warnings: {warnings}")

    # Valid melody features
    melody_features = {
        "is_melody": True,
        "note_count": 12,
        "ks_gap": 0.85,
        "cadence_strength": 0.7,
        "chromatic_runs": 1,
    }

    warnings = service.validate_features(melody_features)
    print(f"Melody feature warnings: {warnings}")

    # Invalid features
    invalid_features = {
        "chord_count": -1,  # Invalid
        "outside_key_ratio": 1.5,  # Invalid (>1.0)
        "evidence_strength": "high",  # Invalid type
    }

    warnings = service.validate_features(invalid_features)
    print(f"Invalid feature warnings: {warnings}")

    # Test 3: Bucket routing
    print("\n3️⃣ Testing bucket routing...")

    test_cases = [
        ("functional", harmony_features, "Simple I-V-I functional"),
        (
            "modal",
            {"chord_count": 3, "has_flat7": True, "is_melody": False},
            "Modal with b7",
        ),
        ("melody", melody_features, "Standard melody"),
        (
            "functional",
            {"chord_count": 6, "outside_key_ratio": 0.4, "is_melody": False},
            "Chromatic borrowed",
        ),
        ("functional", {"chord_count": 2, "is_melody": False}, "Ambiguous sparse"),
    ]

    for track, features, description in test_cases:
        bucket_info = service.get_bucket_info(track, features)  # type: ignore
        print(f"  {description}:")
        print(f"    Track: {bucket_info['track']}, Bucket: {bucket_info['bucket']}")
        print(f"    Uncertainty: {bucket_info['uncertainty']:.3f}")

    # Test 4: Calibration without mapping (pass-through mode)
    print("\n4️⃣ Testing calibration without mapping...")

    test_confidences = [0.1, 0.5, 0.85, 0.99]
    for raw_conf in test_confidences:
        calibrated = service.calibrate_confidence(
            raw_conf, "functional", harmony_features
        )
        print(f"  {raw_conf:.2f} → {calibrated:.3f}")

    # Test 5: Error handling
    print("\n5️⃣ Testing error handling...")

    try:
        service.calibrate_confidence(
            "invalid", "functional", harmony_features  # type: ignore
        )
    except ValueError as e:
        print(f"  ✅ Caught expected error: {e}")

    try:
        service.calibrate_confidence(0.5, "invalid_track", harmony_features)
    except ValueError as e:
        print(f"  ✅ Caught expected error: {e}")

    try:
        service.calibrate_confidence(1.5, "functional", harmony_features)
    except ValueError as e:
        print(f"  ✅ Caught expected error: {e}")

    # Test 6: Try loading a mapping (if available)
    print("\n6️⃣ Testing mapping load (if available)...")

    potential_paths = [
        "assets/calibration_mapping.json",
        "../tools/calibration/calibration_mapping.json",
        "tools/calibration/calibration_mapping.json",
    ]

    for path in potential_paths:
        try:
            test_service = CalibrationService(path)
            stats = test_service.get_calibration_stats()
            print(f"  ✅ Loaded mapping from {path}:")
            print(f"     Version: {stats.get('version')}")
            print(f"     Tracks: {stats.get('total_tracks')}")
            print(f"     Buckets: {stats.get('total_buckets')}")

            # Test calibration with mapping
            calibrated = test_service.calibrate_confidence(
                0.75, "functional", harmony_features
            )
            print(f"     Calibrated 0.75 → {calibrated:.3f}")
            break
        except (FileNotFoundError, ValueError):
            continue
    else:
        print("  ⚠️ No calibration mapping found at standard paths")

    print("\n✅ All tests completed!")
    print("\n📚 Usage Example:")
    print(
        """
    from harmonic_analysis.services.calibration_service import CalibrationService

    # Initialize with mapping
    service = CalibrationService("path/to/calibration_mapping.json")

    # Calibrate a confidence score
    features = {
        "chord_count": 4,
        "outside_key_ratio": 0.1,
        "evidence_strength": 0.8,
        "foil_I_V_I": True,
        "is_melody": False
    }

    calibrated = service.calibrate_confidence(0.85, "functional", features)
    print(f"Calibrated confidence: {calibrated:.3f}")

    # Get routing information
    info = service.get_bucket_info("functional", features)
    print(f"Routed to bucket: {info['bucket']}")
    """
    )
