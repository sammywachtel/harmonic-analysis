"""
Legacy confidence baseline validation test.

This module provides regression testing for confidence scores using a simpler
calibration approach compared to our new 4-stage calibration system. While the
new test_calibration_baseline_validation.py handles sophisticated calibration
validation, this test serves as a regression check and fallback validation.

Key Differences from Modern Calibration Tests:
- Uses simple affine transform calibration (y = ax + b) instead of 4-stage pipeline
- Focuses on historical baseline preservation rather than theoretical accuracy
- Loads calibration mapping from simpler JSON format if available
- Provides per-case and dataset-level MAE validation with configurable tolerances

This test is complementary (not redundant) to the new calibration tests:
- Serves as regression safety net for confidence scoring changes
- Validates basic confidence behavior with simpler calibration model
- Provides fallback validation when sophisticated calibration isn't available
- Maintains compatibility with existing baseline datasets and tooling

Environment Variables for Tuning:
- HA_PER_CASE_TOL: Per-case tolerance (default: 0.12)
- HA_MAE_TOL: Mean Absolute Error tolerance (default: 0.10)
- HA_CALIBRATION_MAPPING_PATH: Path to simple calibration mapping JSON
- HA_CONFIDENCE_BASELINE_PATH: Path to confidence baseline dataset
"""

import json
import os

import pytest

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
from tests.helpers import calibration as calib

# Tolerances can be tuned via env vars
PER_CASE_TOL = float(os.environ.get("HA_PER_CASE_TOL", "0.12"))
MAE_TOL = float(os.environ.get("HA_MAE_TOL", "0.10"))

# Standard calibration mapping file location
MAPPING_JSON = "src/harmonic_analysis/assets/calibration_mapping.json"


def _apply_calibration_local(x: float, typ: str, mapping: dict) -> float:
    """Fallback calibration: y = a*x + b, clamped to [0,1].

    Simple linear calibration transform as fallback when sophisticated 4-stage
    calibration system isn't available. This preserves historical test behavior.

    Args:
        x: Raw confidence score to calibrate
        typ: Analysis type ("functional", "modal", or falls back to "default")
        mapping: Simple calibration mapping with structure:
                {"functional": {"a": 1.0, "b": 0.0}, "modal": {...}, "default": {...}}

    Returns:
        Calibrated confidence score clamped to [0.0, 1.0] range

    Note: This is much simpler than the 4-stage calibration pipeline and serves
    primarily for regression testing and fallback scenarios.
    """
    m = (mapping or {}).get(typ) or (mapping or {}).get("default")
    if not isinstance(m, dict):
        return float(x)
    a = float(m.get("a", 1.0))
    b = float(m.get("b", 0.0))
    y = a * float(x) + b
    # clamp
    if y < 0.0:
        return 0.0
    if y > 1.0:
        return 1.0
    return y


BASELINE_JSON = "src/harmonic_analysis/assets/confidence_baseline.json"


current_directory = os.getcwd()


def test_confidence_against_baseline():
    """Test confidence scores against historical baseline with optional simple calibration.

    This is the main regression test for confidence scoring behavior. It:
    1. Loads baseline dataset with expected confidence scores
    2. Optionally applies simple linear calibration if mapping file exists
    3. Runs PatternAnalysisService on each baseline case
    4. Compares actual vs expected confidence with configurable tolerances
    5. Validates both per-case accuracy and dataset-level MAE

    Key Features:
    - Skips test if baseline JSON not found (with helpful error message)
    - Handles both DTO and dict-based result formats for compatibility
    - Supports configurable tolerances via environment variables
    - Provides detailed failure messages for debugging
    - Falls back gracefully when calibration mapping unavailable

    This test complements (doesn't replace) the sophisticated 4-stage calibration
    validation, serving as a simpler regression safety net.
    """
    # Ensure required files exist - fail test if missing since they should be in the repository
    if not os.path.exists(BASELINE_JSON):
        pytest.fail(
            f"Required baseline file not found: {BASELINE_JSON}. "
            f"This file should be part of the repository for functionality testing. "
            f"Run 'python tools/calibration/calibration_pipeline.py generate' to generate it or ensure it's committed to git."
        )

    if not os.path.exists(MAPPING_JSON):
        pytest.fail(
            f"Required calibration mapping not found: {MAPPING_JSON}. "
            f"This file should be part of the repository for functionality testing."
        )

    baseline = calib.load_baseline(BASELINE_JSON)
    # Load required calibration mapping from standard location
    try:
        # Prefer helper if available
        if hasattr(calib, "load_mapping"):
            mapping = calib.load_mapping(MAPPING_JSON)
        else:
            with open(MAPPING_JSON, "r") as f:
                mapping = json.load(f)
    except Exception as e:
        pytest.fail(f"Failed to load calibration mapping from {MAPPING_JSON}: {e}")
    svc = PatternAnalysisService()

    results = []
    for row in baseline:
        chords = row["chords"].split()
        parent_key = row.get("parent_key") or None

        # run analysis
        res = svc.analyze_with_patterns(
            chords, profile="classical", best_cover=False, key_hint=parent_key
        )

        # DTO-first extraction (raw confidence before calibration)
        if hasattr(res, "primary") and hasattr(res.primary, "confidence"):
            raw_actual = float(res.primary.confidence or 0.0)
        else:
            pa = (
                (res.get("primary") or res.get("primary_analysis") or {})
                if isinstance(res, dict)
                else {}
            )
            raw_actual = float(pa.get("confidence") or 0.0)

        # Apply calibration mapping by analysis type (defaults to functional)
        analysis_type = (row.get("type") or "functional").lower()
        if hasattr(calib, "apply_calibration"):
            actual = float(calib.apply_calibration(raw_actual, analysis_type, mapping))
        else:
            actual = _apply_calibration_local(raw_actual, analysis_type, mapping)

        expected = row.get("expected_confidence")
        if expected in ("", None):
            # If no expected recorded, we treat baseline actual as expected
            expected = float(row.get("actual_confidence") or 0.0)

        diff = abs(actual - float(expected))

        # per-case assertion
        assert (
            diff <= PER_CASE_TOL
        ), f"{row['name']}: |actual({actual:.3f}) - expected({expected:.3f})| = {diff:.3f} > {PER_CASE_TOL:.3f}"

        results.append({"name": row["name"], "diff": diff})

    # Dataset-level MAE
    dataset_mae = sum(r["diff"] for r in results) / max(1, len(results))
    assert (
        dataset_mae <= MAE_TOL
    ), f"MAE {dataset_mae:.3f} > {MAE_TOL:.3f} across {len(results)} cases"
