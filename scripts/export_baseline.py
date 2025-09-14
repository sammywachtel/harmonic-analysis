#!/usr/bin/env python3
"""
Export a confidence baseline by running the library over a JSON test suite.
Improved version with pattern name extraction and better DTO/dict handling.

Usage:
  python scripts/export_baseline.py \
      --tests tests/data/generated/comprehensive-multi-layer-tests.json \
      --out tools/calibration/confidence_baseline.json
"""

import argparse
import json
from typing import Any, Dict, List

# Import your project modules
try:
    from harmonic_analysis.analysis_types import AnalysisOptions
    from harmonic_analysis.services.pattern_analysis_service import (
        PatternAnalysisService,
    )
except Exception as e:
    raise SystemExit(f"[export_baseline] Could not import project modules: {e}")


def extract_pattern_names(result):
    """Extract pattern names from either DTO or dict format."""
    # DTO path
    primary = getattr(result, "primary", None)
    if primary and getattr(primary, "patterns", None):
        return [p.name for p in primary.patterns if getattr(p, "name", None)]

    # dict path - only if result is actually a dict
    if isinstance(result, dict):
        pms = (result or {}).get("pattern_matches") or []
        return [pm.get("name") for pm in pms if pm.get("name")]

    return []


def extract_confidences(result):
    """Extract functional and modal confidences from either DTO or dict format."""
    # DTO path
    primary = getattr(result, "primary", None)
    if primary:
        f_conf = float(getattr(primary, "functional_confidence", 0.0) or 0.0)
        m_conf = float(getattr(primary, "modal_confidence", 0.0) or 0.0)
        return f_conf, m_conf

    # dict path - only if result is actually a dict
    if isinstance(result, dict):
        fa = (result or {}).get("functional_analysis") or {}
        f_conf = float(
            fa.get("confidence") or result.get("functional_confidence") or 0.0
        )
        m_conf = float(
            (result.get("modal") or {}).get("confidence")
            or result.get("modal_confidence")
            or 0.0
        )
        return f_conf, m_conf

    return 0.0, 0.0


def compute_bucket(
    case: Dict[str, Any], chords: List[str], pattern_names: List[str], primary: Any
) -> str:
    """Compute bucket classification for routing features."""
    category = case.get("category", "")

    # Scale/melody cases
    if not chords or len(chords) == 0:
        note_count = len(case.get("notes", []))
        if note_count < 8:
            return "melodic_short"
        # TODO: Add more sophisticated melody bucket routing
        return "melodic_clear"

    # Harmony cases - simple heuristics for now
    chord_str = " ".join(chords).lower()

    # Check for simple progressions
    if any(simple in chord_str for simple in ["c f g c", "i iv v i", "i v i"]):
        return "functional_simple"

    # Check for modal markers in pattern names
    modal_patterns = [
        "mixolydian",
        "dorian",
        "lydian",
        "phrygian",
        "locrian",
        "aeolian",
    ]
    if any(modal in " ".join(pattern_names).lower() for modal in modal_patterns):
        return "modal_marked"

    # Check for chromatic/borrowed elements
    if any(chromatic in chord_str for chromatic in ["#", "b", "dim", "aug"]):
        return "chromatic_borrowed"

    # Check for secondary dominants
    if "/" in chord_str or "secondary" in " ".join(pattern_names).lower():
        return "secondary_dominant"

    # Default fallback
    if len(chords) < 4:
        return "ambiguous_sparse"

    return "functional_simple"  # Default


def compute_routing_features(
    case: Dict[str, Any], chords: List[str], primary: Any
) -> Dict[str, Any]:
    """Compute routing features for calibration buckets and uncertainty."""
    features = {}

    # Common features
    features["chord_count"] = len(chords)

    # Scale/melody features
    if not chords or len(chords) == 0:
        notes = case.get("notes", [])
        features["note_count"] = len(notes)
        features["unique_pitch_count"] = (
            len(set(n.split(":")[0] if ":" in str(n) else str(n)[0] for n in notes))
            if notes
            else 0
        )
        features["is_melody"] = True
        # TODO: Add ks_sim_max, ks_gap, cadence_strength, chromatic_runs
        features["ks_sim_max"] = 0.0  # Placeholder
        features["ks_gap"] = 0.0  # Placeholder
        features["cadence_strength"] = 0.0  # Placeholder
        features["chromatic_runs"] = 0  # Placeholder
    else:
        # Harmony features
        features["is_melody"] = False

        # Simple heuristics for routing features (TODO: extract from actual analysis)
        chord_str = " ".join(chords).lower()
        features["outside_key_ratio"] = sum(1 for c in chord_str if c in "#b") / max(
            len(chords), 1
        )
        features["evidence_strength"] = len(chords) / 8.0  # Normalize by typical length
        features["foil_I_V_I"] = "i v i" in chord_str or "c g c" in chord_str

        # Characteristic degrees presence
        features["has_flat2"] = "b2" in chord_str or "db" in chord_str
        features["has_sharp4"] = "#4" in chord_str or "f#" in chord_str
        features["has_flat3"] = "b3" in chord_str or "eb" in chord_str
        features["has_flat6"] = "b6" in chord_str or "ab" in chord_str
        features["has_flat7"] = "b7" in chord_str or "bb" in chord_str
        features["has_flat5"] = "b5" in chord_str or "gb" in chord_str

        features["chord_density"] = len([c for c in chord_str if c.isalpha()]) / max(
            len(chord_str), 1
        )

    return features


def _run_case(svc: PatternAnalysisService, case: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single test case and produce a normalized record for baseline analysis."""
    chords: List[str] = case.get("chords", [])
    parent_key = case.get("parent_key")
    profile = case.get("profile", "classical")
    expected_func = (case.get("expected_functional") or {}).get("confidence")
    expected_modal = (case.get("expected_modal") or {}).get("confidence")

    # Handle scale_melody cases (no chords) differently
    if not chords or len(chords) == 0:
        # For melody cases, create a minimal record without running analysis
        routing_features = compute_routing_features(case, chords, None)
        bucket = compute_bucket(case, chords, [], None)

        # Generate meaningful name for melody cases
        test_name = (
            case.get("name")
            or case.get("description")
            or case.get("id")
            or f"{case.get('category', 'melody')}_{len(case.get('notes', []))}notes_"
            f"{hash(str(case.get('notes', [])))%10000}"
        )

        record = {
            "name": test_name,
            "category": case.get("category"),
            "chords": chords,
            "chords_str": "",
            "parent_key": parent_key,
            "profile": profile,
            "expected_functional_confidence": expected_func,
            "expected_modal_confidence": expected_modal,
            "primary_type": "melody",
            "primary_confidence": None,
            "functional_confidence": 0.0,
            "modal_confidence": 0.0,
            "key_signature": None,
            "mode": None,
            "pattern_names": [],
            "final_cadence_name": None,
            "track": "melody",
            "bucket": bucket,
            "routing_features": routing_features,
        }
        return record

    # Run the analysis (synchronously via thread to avoid event-loop issues)
    res = svc.analyze_with_patterns(
        chords, profile=profile, best_cover=False, key_hint=parent_key
    )

    # Expecting DTO AnalysisEnvelope; normalize defensively
    primary = getattr(res, "primary", None) or {}

    # Extract pattern names
    pattern_names = extract_pattern_names(res)

    # Extract final cadence name
    final_cadence_name = None
    if hasattr(primary, "final_cadence") and primary.final_cadence:
        final_cadence_name = getattr(primary.final_cadence, "name", None)
    elif isinstance(primary, dict):
        fc = primary.get("final_cadence") or {}
        final_cadence_name = fc.get("name") if isinstance(fc, dict) else None

    # Extract confidences using helper
    f_conf, m_conf = extract_confidences(res)

    # Extract other fields
    if isinstance(primary, dict):
        pt = primary.get("type")
        romans = primary.get("roman_numerals")
        conf = primary.get("confidence")
        ksig = primary.get("key_signature")
        mode = primary.get("mode")
    else:
        pt = getattr(primary, "type", None)
        romans = getattr(primary, "roman_numerals", None)
        conf = getattr(primary, "confidence", None)
        ksig = getattr(primary, "key_signature", None)
        mode = getattr(primary, "mode", None)

    # Compute routing features and bucket
    routing_features = compute_routing_features(case, chords, primary)
    bucket = compute_bucket(case, chords, pattern_names, primary)

    # Determine track (functional vs modal)
    track = "modal" if pt == "modal" else "functional"

    # Generate meaningful name from available fields
    test_name = (
        case.get("name")
        or case.get("description")
        or case.get("id")
        or f"{case.get('category', 'unknown')}_{len(chords)}ch_"
        f"{hash(str(chords))%10000}"
    )

    record = {
        "name": test_name,
        "category": case.get("category"),
        "chords": chords,
        "chords_str": " ".join(chords),
        "parent_key": parent_key,
        "profile": profile,
        "expected_functional_confidence": expected_func,
        "expected_modal_confidence": expected_modal,
        "primary_type": pt,
        "primary_confidence": conf,
        "functional_confidence": f_conf,
        "modal_confidence": m_conf,
        "key_signature": ksig,
        "mode": mode,
        "pattern_names": pattern_names,
        "final_cadence_name": final_cadence_name,
        # New fields for calibration
        "track": track,
        "bucket": bucket,
        "routing_features": routing_features,
    }
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", required=True, help="Path to JSON test suite")
    ap.add_argument("--out", required=True, help="Where to write baseline JSON")
    args = ap.parse_args()

    with open(args.tests, "r") as f:
        data = json.load(f)

    # Accept both {"test_cases": [...]} and a list [...]
    test_cases = data["test_cases"] if isinstance(data, dict) else data

    svc = PatternAnalysisService()
    rows = [_run_case(svc, tc) for tc in test_cases]

    out = {
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "method": "export_baseline_v2",
        "rows": rows,
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"[export_baseline] wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
