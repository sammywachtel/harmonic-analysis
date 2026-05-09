"""Audio-subpackage data types.

Three frozen dataclasses passed between `_key_estimation`, `_cadence`, and
`_region`. Frozen so a stale reference in one stage can't mutate state in
another — these objects fan out across the pipeline and immutability is
cheaper than chasing aliasing bugs at 2am.

`KeyInfo.diatonic_pitch_classes` is a derived field: it's a function of
`tonic` + `mode` and shouldn't be passed in by callers. The standard idiom
for derived fields on a frozen dataclass is `field(init=False)` plus
`__post_init__` with `object.__setattr__`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ._profiles import PC_OF_NOTE, PITCH_CLASSES  # noqa: F401

# Diatonic interval patterns relative to tonic. Major = Ionian, "minor" here
# means natural minor / Aeolian. Harmonic and melodic minor variants are not
# represented — toolkit's mode_map hardcodes Ionian/Aeolian only and WU3
# extends mode support.
_DIATONIC_INTERVALS_MAJOR = (0, 2, 4, 5, 7, 9, 11)
_DIATONIC_INTERVALS_MINOR = (0, 2, 3, 5, 7, 8, 10)


def _compute_diatonic_pcs(tonic: str, mode: str) -> frozenset[int]:
    """Return the pitch-class set of the diatonic scale for ``tonic``/``mode``.

    Accepts the toolkit-style mode names ("Ionian"/"Aeolian"), the raw
    "major"/"minor" labels K-S internally uses, or "N/A" (zero-energy
    sentinel — returns an empty set rather than raising).
    """
    if tonic == "N/A":
        return frozenset()

    mode_lower = mode.lower()
    if mode_lower in ("major", "ionian"):
        intervals = _DIATONIC_INTERVALS_MAJOR
    elif mode_lower in ("minor", "aeolian"):
        intervals = _DIATONIC_INTERVALS_MINOR
    else:
        # Unsupported mode (dorian, etc.) — return empty rather than guess.
        # WU3 extends this. Until then, treat as "no diatonic info."
        return frozenset()

    # Accept both sharp and flat spellings ("A#" or "Bb"). Raises KeyError
    # on garbage input, which is what we want — silent fallback hides bugs.
    tonic_pc = PC_OF_NOTE[tonic]
    return frozenset((tonic_pc + step) % 12 for step in intervals)


@dataclass(frozen=True)
class KeyInfo:
    """Result of K-S key estimation.

    ``diatonic_pitch_classes`` is computed from ``tonic`` + ``mode`` in
    ``__post_init__`` and shouldn't be supplied at construction time.
    """

    tonic: str
    mode: str
    key_signature: str
    confidence: float
    diatonic_pitch_classes: frozenset[int] = field(init=False)

    def __post_init__(self) -> None:
        # Frozen dataclasses block normal assignment; use the documented
        # object.__setattr__ escape hatch. This is the canonical idiom for
        # derived fields on a frozen dataclass. mypy --strict accepts it
        # without a type: ignore (verified locally with the project's
        # current mypy config).
        object.__setattr__(
            self,
            "diatonic_pitch_classes",
            _compute_diatonic_pcs(self.tonic, self.mode),
        )


@dataclass(frozen=True)
class CadenceInfo:
    """Result of cadence detection on a chroma segment."""

    detected: bool
    strength: float


@dataclass(frozen=True)
class RegionInfo:
    """Result of region classification (stable / modulation / modal_shift)."""

    type: str
    confidence: float
    borrowed: List[str]
