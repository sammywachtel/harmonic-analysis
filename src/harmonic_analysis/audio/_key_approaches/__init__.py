"""Key-detection approach implementations.

Each module exports one class implementing ``KeyDetectionApproach``. The
adapter-level orchestrator picks which ones to run based on the
``key_detection`` parameter; this package just provides the toolbox.

iteration_01 ships four defaults; iteration_02 adds ``pattern_engine``
and ``hmm`` opt-ins.
"""

from __future__ import annotations

from typing import Dict, Type

from .._key_ensemble import KeyDetectionApproach
from .bass_dominance import BassDominanceApproach
from .boundary_chords import BoundaryChordsApproach
from .cadential import CadentialApproach
from .template_correlation import TemplateCorrelationApproach

__all__ = [
    "BassDominanceApproach",
    "BoundaryChordsApproach",
    "CadentialApproach",
    "TemplateCorrelationApproach",
    "DEFAULT_APPROACH_REGISTRY",
]


# Name → class lookup. The adapter consults this to instantiate approaches
# by name (string-driven) rather than by import. Adding a new approach is
# a one-line registration; old call sites keep working.
DEFAULT_APPROACH_REGISTRY: Dict[str, Type[KeyDetectionApproach]] = {
    "template_correlation": TemplateCorrelationApproach,
    "boundary_chords": BoundaryChordsApproach,
    "bass_dominance": BassDominanceApproach,
    "cadential": CadentialApproach,
}
