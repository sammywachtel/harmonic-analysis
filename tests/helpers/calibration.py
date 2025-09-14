from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple


# -----------------------------
# Data containers and utilities
# -----------------------------
@dataclass
class CaseResult:
    """
    Container for a single baseline-comparison result.
      - name: human-readable case name (e.g., "G Mixolydian bVII")
      - expected: expected confidence from baseline (0..1) or None if unknown
      - actual: observed confidence from the library (0..1)
      - diff: actual - expected (positive means we're higher than baseline)
    """

    name: str
    expected: float | None
    actual: float
    diff: float


def mae(cases: List[CaseResult]) -> float:
    """
    Mean Absolute Error across a list of CaseResult.
    Returns 0.0 for an empty list.
    """
    if not cases:
        return 0.0
    return sum(abs(c.diff) for c in cases) / len(cases)


# -----------------------------
# Baseline I/O
# -----------------------------
def load_baseline(path: str) -> List[Dict[str, Any]]:
    """
    Load a baseline JSON produced by the calibration notebook or script.

    Expected schema (minimal):
    {
      "baseline": [
        {
          "name": "G Mixolydian with bVII",
          "type": "modal",                # "functional" | "modal" (optional; defaults to "functional")
          "chords": ["G","F","G"],        # progression used to compute expected
          "expected": 0.62                # target confidence in [0,1]
        },
        ...
      ]
    }

    Unknown keys are ignored. Returns the list under "baseline" (or empty list).
    """
    with open(path, "r") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("baseline"), list):
        return data["baseline"]
    # Allow raw list as a convenience
    if isinstance(data, list):
        return data
    return []


# -----------------------------
# Calibration mapping I/O
# -----------------------------
def _normalize_affine(
    d: Mapping[str, Any] | List[float] | Tuple[float, float],
) -> Tuple[float, float, float, float]:
    """
    Normalize an affine calibration spec to (a, b, clip_min, clip_max).

    Accepted forms for `d`:
      - {"a": 0.95, "b": 0.02}
      - {"scale": 0.95, "shift": 0.02}
      - {"k": 0.95, "m": 0.02}
      - {"a": 1.0, "b": 0.0, "clip": [0.0, 1.0]}
      - [a, b]
      - (a, b)

    Defaults to identity with clip [0,1] if missing.
    """
    a = 1.0
    b = 0.0
    clip_min, clip_max = 0.0, 1.0

    if isinstance(d, (list, tuple)) and len(d) >= 2:
        a, b = float(d[0]), float(d[1])
    elif isinstance(d, Mapping):
        # multiple common aliases
        if "a" in d:
            a = float(d["a"])
        elif "scale" in d:
            a = float(d["scale"])
        elif "k" in d:
            a = float(d["k"])

        if "b" in d:
            b = float(d["b"])
        elif "shift" in d:
            b = float(d["shift"])
        elif "m" in d:
            b = float(d["m"])

        if "clip" in d and isinstance(d["clip"], (list, tuple)) and len(d["clip"]) == 2:
            clip_min, clip_max = float(d["clip"][0]), float(d["clip"][1])
        else:
            if "clip_min" in d:
                clip_min = float(d["clip_min"])
            if "clip_max" in d:
                clip_max = float(d["clip_max"])
    # else: leave identity defaults

    # Sanity: ensure clip_min <= clip_max
    if clip_min > clip_max:
        clip_min, clip_max = clip_max, clip_min

    return a, b, clip_min, clip_max


def load_mapping(path: str | None) -> Dict[str, Dict[str, float | List[float]]]:
    """
    Load a calibration mapping JSON. Returns {} if `path` is None or the file doesn't exist.

    Expected schema examples:
    {
      "functional": {"a": 0.98, "b": 0.01, "clip": [0,1]},
      "modal":      {"scale": 0.92, "shift": 0.02}
    }
    or
    {
      "default": [0.95, 0.02]
    }

    The function does not validate ranges beyond basic shape checks.
    """
    if not path:
        return {}
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    return data


def apply_calibration(
    x: float, mapping: Optional[Dict[str, Any]] = None, kind: str = "functional"
) -> float:
    """
    Apply an optional affine calibration y = a*x + b with clamping.

    - x: raw confidence in [0,1] (not strictly required; we clamp after transform)
    - mapping: dict returned by load_mapping(). If None/empty, returns clamped x.
    - kind: "functional" or "modal" (used to select the sub-mapping).
            Falls back to "default" if present, otherwise identity.

    Returns calibrated confidence in [0,1].
    """
    if not mapping:
        return max(0.0, min(1.0, x))

    spec = None
    if kind in mapping:
        spec = mapping[kind]
    elif "default" in mapping:
        spec = mapping["default"]

    a, b, clip_min, clip_max = _normalize_affine(spec if spec is not None else {})
    y = a * float(x) + b
    # Clamp
    if y < clip_min:
        y = clip_min
    elif y > clip_max:
        y = clip_max
    # Ensure [0,1] as the outer safety net
    return max(0.0, min(1.0, y))


# -----------------------------
# Optional helpers for tests
# -----------------------------
def build_case_results(
    baseline_rows: List[Dict[str, Any]],
    actuals: List[float],
    mapping: Optional[Dict[str, Any]] = None,
) -> List[CaseResult]:
    """
    Convenience function used by tests:
      - baseline_rows: rows from load_baseline()
      - actuals: list of raw confidences produced by the analyzer (same order)
      - mapping: optional calibration mapping from load_mapping()

    Returns a parallel list of CaseResult with calibration applied (if provided).
    """
    results: List[CaseResult] = []
    for row, actual in zip(baseline_rows, actuals):
        typ = str(row.get("type", "functional"))
        expected = row.get("expected")
        calibrated = apply_calibration(actual, mapping, typ)
        results.append(
            CaseResult(
                name=str(row.get("name", "case")),
                expected=float(expected) if expected is not None else None,
                actual=calibrated,
                diff=(calibrated - float(expected)) if expected is not None else 0.0,
            )
        )
    return results
