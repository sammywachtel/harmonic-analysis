"""
Type definitions for corpus miner module.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class LabelSource(Enum):
    """Source of reliability label."""

    ADJUDICATION_HEURISTIC = "adjudication_heuristic"
    TRUSTED_ANNOTATION = "trusted_annotation"
    EXPERT_CONSENSUS = "expert_consensus"
    WEAK_SUPERVISION = "weak_supervision"


class DifficultyStratum(Enum):
    """Difficulty stratification for calibration."""

    DIATONIC_SIMPLE = "diatonic_simple"
    CHROMATIC_MODERATE = "chromatic_moderate"
    MODAL_COMPLEX = "modal_complex"
    ATONAL_DIFFICULT = "atonal_difficult"


@dataclass
class MusicalContext:
    """Normalized musical context for pattern analysis."""

    key: str
    chords: List[str]
    roman_numerals: List[str]
    melody: List[str]
    metadata: Dict[str, Any]


@dataclass
class PatternMatch:
    """Pattern match with evidence features."""

    pattern_id: str
    span: Tuple[int, int]
    raw_score: float
    evidence_features: Dict[str, Any]


@dataclass
class LabeledSample:
    """Corpus sample with unified reliability target."""

    context: Dict[str, Any]
    matches: List[PatternMatch]
    label: float  # p(correct | evidence)
    label_source: LabelSource
    difficulty_stratum: DifficultyStratum
    confidence_breakdown: Dict[str, float]


@dataclass
class ExtractionConfig:
    """Configuration for corpus extraction."""

    corpus_sources: List[str] = None
    max_samples_per_source: int = 100
    transposition_keys: List[str] = None
    min_chord_count: int = 4
    max_chord_count: int = 16

    def __post_init__(self):
        if self.corpus_sources is None:
            self.corpus_sources = ["bach/chorales", "jazz/standards"]
        if self.transposition_keys is None:
            self.transposition_keys = ["C", "D", "F", "G"]


@dataclass
class AdjudicationRules:
    """Configuration for adjudication heuristics."""

    strong_evidence_threshold: float = 0.9
    weak_evidence_threshold: float = 0.3
    consensus_patterns: List[str] = None
    contradiction_patterns: List[str] = None

    def __post_init__(self):
        if self.consensus_patterns is None:
            self.consensus_patterns = [
                "cadence.authentic.perfect",
                "cadence.plagal",
                "modal.dorian.i_bVII",
            ]
        if self.contradiction_patterns is None:
            self.contradiction_patterns = [
                "atonal.twelve_tone",
                "chromatic.extreme_dissonance",
            ]


@dataclass
class CalibrationBucket:
    """Calibration bucket for stratified reliability estimation."""

    stratum: DifficultyStratum
    pattern_family: str
    min_score: float
    max_score: float
    samples: List[LabeledSample]
    empirical_reliability: Optional[float] = None
    sample_count: int = 0
    label_variance: float = 0.0


@dataclass
class TargetStatistics:
    """Statistics for target quality assessment."""

    total_samples: int
    label_distribution: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    pattern_family_distribution: Dict[str, int]
    reliability_range: Tuple[float, float]
    correlation_stats: Dict[str, float]
