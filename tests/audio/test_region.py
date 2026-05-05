"""Unit tests for ``classify_region_type``.

Covers AC5 region scenarios: stable, modulation, modal_shift. Each
scenario is a separate test — the classifier branches on cadence + key
data, and a single combined test would mask which branch failed.
"""

from __future__ import annotations

from harmonic_analysis.audio._region import classify_region_type
from harmonic_analysis.audio._types import CadenceInfo, KeyInfo, RegionInfo


def _key(tonic: str, mode: str, *, confidence: float = 0.9) -> KeyInfo:
    full_mode = "major" if mode in ("Ionian", "major") else "minor"
    return KeyInfo(
        tonic=tonic,
        mode=mode,
        key_signature=f"{tonic} {full_mode}",
        confidence=confidence,
    )


def test_classify_region_type_returns_regioninfo() -> None:
    # AC4 smoke: pure-numpy/no-music21, returns the dataclass.
    g = _key("C", "Ionian")
    result = classify_region_type(g, g, 0.9, CadenceInfo(detected=True, strength=0.7))
    assert isinstance(result, RegionInfo)
    assert isinstance(result.type, str)
    assert isinstance(result.confidence, float)
    assert isinstance(result.borrowed, list)


def test_classify_region_type_stable_when_keys_match() -> None:
    # AC5 — stable region. Same key signature → return immediately.
    g = _key("C", "Ionian")
    cad = CadenceInfo(detected=True, strength=0.8)
    result = classify_region_type(g, g, 0.95, cad)
    assert result.type == "stable"
    assert result.confidence == 0.95
    assert result.borrowed == []


def test_classify_region_type_modulation_with_strong_cadence() -> None:
    # AC5 — modulation. New key, high confidence, strong cadence → all
    # three modulation criteria satisfied.
    global_key = _key("C", "Ionian")
    local_key = _key("G", "Ionian")
    cad = CadenceInfo(detected=True, strength=0.75)
    result = classify_region_type(global_key, local_key, 0.85, cad)
    assert result.type == "modulation"
    # Borrowed: G major has F# where C major has F. Set difference is {6}.
    assert "F#" in result.borrowed
    # Confidence is 50/50 weighted average: 0.85 * 0.5 + 0.75 * 0.5 = 0.80.
    assert abs(result.confidence - 0.80) < 0.01


def test_classify_region_type_modal_shift_when_cadence_weak() -> None:
    # AC5 — modal-shift. Different key (parallel mode), weak cadence so
    # modulation criteria fail → fall through to modal_shift bucket.
    global_key = _key("C", "Ionian")
    local_key = _key("C", "Aeolian")  # parallel C minor
    cad = CadenceInfo(detected=False, strength=0.0)
    result = classify_region_type(global_key, local_key, 0.7, cad)
    assert result.type == "modal_shift"
    # C major vs C minor differ on Eb, Ab, Bb (pcs 3, 8, 10).
    assert set(result.borrowed) == {"D#", "G#", "A#"}
    # Confidence: 1.0 - 3 * 0.15 = 0.55.
    assert abs(result.confidence - 0.55) < 0.01


def test_classify_region_type_modal_shift_with_high_confidence_no_cadence() -> None:
    # Even with high local-key confidence, missing cadence kills the
    # modulation classification — by design of the toolkit's heuristic.
    global_key = _key("C", "Ionian")
    local_key = _key("G", "Ionian")
    cad = CadenceInfo(detected=False, strength=0.0)  # no cadence
    result = classify_region_type(global_key, local_key, 0.95, cad)
    assert result.type == "modal_shift"


def test_classify_region_type_borrowed_pcs_are_sorted_for_determinism() -> None:
    # frozenset iteration order is undefined; the implementation sorts so
    # callers get a deterministic list. Verify that contract.
    global_key = _key("C", "Ionian")
    local_key = _key("C", "Aeolian")
    cad = CadenceInfo(detected=False, strength=0.0)
    result = classify_region_type(global_key, local_key, 0.7, cad)
    # Sorted by pitch class: D# (3), G# (8), A# (10).
    assert result.borrowed == ["D#", "G#", "A#"]
