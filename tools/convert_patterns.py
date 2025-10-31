#!/usr/bin/env python3
"""
Convert patterns from old format (patterns.json) to new unified format.
"""
import json
from pathlib import Path
from typing import Any, Dict, List


def convert_pattern(old_pattern: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a pattern from old format to unified format.

    Old format:
        - family: "jazz_pop" → track: ["functional"]
        - sequence with roman_root_any_of → matchers.roman_seq
        - window: {min, max} → matchers.window: {len, overlap_ok}
        - score: {base} → evidence: {weight}

    New format requires:
        - scope: ["harmonic"]
        - track: ["functional"|"modal"|"chromatic"]
        - matchers with roman_seq/chord_seq/etc
        - evidence with weight and confidence_fn
        - metadata with tags, priority, description
    """
    pattern_id = old_pattern["id"]
    name = old_pattern["name"]
    family = old_pattern.get("family", "functional")

    # Map family to track
    family_to_track = {
        "jazz_pop": "functional",
        "cadence": "functional",
        "pd_d_chain": "functional",
        "prolongation": "functional",
        "schema": "functional",
        "sequence": "functional",
        "mixture_modal": "modal",
        "chromatic_pd": "chromatic",
    }
    track = family_to_track.get(family, "functional")

    # Extract roman numerals from sequence
    sequence = old_pattern.get("sequence", [])
    roman_seq = []
    for item in sequence:
        # Take first roman numeral option
        roman_options = item.get("roman_root_any_of", [])
        if roman_options:
            roman_seq.append(roman_options[0])

    # Convert window
    window_old = old_pattern.get("window", {})
    window_len = window_old.get("min", window_old.get("max", len(roman_seq)))

    # Convert score to evidence
    score = old_pattern.get("score", {})
    weight = score.get("base", 0.8)

    # Build new pattern
    new_pattern = {
        "id": f"{track}.{pattern_id}",
        "name": name,
        "scope": ["harmonic"],
        "track": [track],
        "matchers": {
            "roman_seq": roman_seq,
            "constraints": {"key_context": "diatonic"},
            "window": {"len": window_len, "overlap_ok": False},
        },
        "evidence": {
            "weight": weight,
            "features": ["pattern_match"],
            "confidence_fn": "logistic_default",
        },
        "metadata": {
            "tags": [track, family],
            "priority": 75,
            "description": f"{name} - converted from legacy patterns.json",
            "aliases": [],
        },
    }

    return new_pattern


def main():
    """Convert important missing patterns."""
    script_dir = Path(__file__).parent
    old_patterns_path = (
        script_dir.parent
        / "src"
        / "harmonic_analysis"
        / "core"
        / "pattern_engine"
        / "patterns.json"
    )

    # Load old patterns
    with open(old_patterns_path, "r", encoding="utf-8") as f:
        old_patterns = json.load(f)

    # Priority patterns to convert (jazz, pop, and important functional patterns)
    priority_ids = [
        "jazz_iiviV",  # The one the user needs!
        "jazz_iiV_I",
        "jazz_backdoor",
        "jazz_backdoor_variant",
        "jazz_tritone_sub_chain",
        "pop_I_V_vi_IV",
        "pop_I_vi_IV_V",
        "pop_vi_IV_I_V",
        "pop_bVI_bVII_I",
        "blues_cadence",
        "cadence_deceptive",
        "ii_V_I_root_macro",
    ]

    converted = []
    for pattern in old_patterns:
        if pattern["id"] in priority_ids:
            try:
                new_pattern = convert_pattern(pattern)
                converted.append(new_pattern)
                print(f"✅ Converted: {pattern['id']} → {new_pattern['id']}")
            except Exception as e:
                print(f"❌ Failed to convert {pattern['id']}: {e}")

    # Output converted patterns
    output = {"converted_patterns": converted, "count": len(converted)}

    output_path = script_dir / "converted_patterns.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Converted {len(converted)} patterns")
    print(f"📝 Saved to: {output_path}")

    return converted


if __name__ == "__main__":
    main()
