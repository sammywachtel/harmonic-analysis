"""
Evidence model for unified pattern engine.

This module defines the internal evidence representation used by the pattern engine
to track contributions from different analysis types (functional, modal, etc.).
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Evidence:
    """
    Internal evidence representation from pattern matches.

    This is distinct from the public EvidenceDTO and contains richer internal state
    for aggregation and scoring. Converted to EvidenceDTO when exposed in the API.
    """

    pattern_id: str
    """Unique identifier of the pattern that generated this evidence."""

    track_weights: Dict[str, float]
    """Contribution weights by analysis track (e.g., {"functional": 0.8, "modal": 0.3})."""

    features: Dict[str, float]
    """Feature values extracted from the match (e.g., {"outside_key_ratio": 0.2})."""

    raw_score: float
    """Raw confidence score from the pattern's confidence function (0.0-1.0)."""

    uncertainty: Optional[float]
    """Optional uncertainty measure for probabilistic patterns."""

    span: Tuple[int, int]
    """Chord indices covered by this evidence [start_idx, end_idx)."""

    def overlaps(self, other: "Evidence") -> bool:
        """Check if this evidence overlaps with another in chord span."""
        return not (self.span[1] <= other.span[0] or other.span[1] <= self.span[0])

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "track_weights": self.track_weights,
            "features": self.features,
            "raw_score": self.raw_score,
            "uncertainty": self.uncertainty,
            "span": list(self.span),
        }
