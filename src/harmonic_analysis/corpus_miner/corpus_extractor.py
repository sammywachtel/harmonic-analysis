"""
Corpus Extractor - Simplified production version for unified target construction.
"""

import logging
from typing import List

from .types import ExtractionConfig, MusicalContext


class CorpusExtractor:
    """
    Simplified corpus extraction for production use.

    Returns mock data when music21 is unavailable, which is sufficient
    for the unified target construction system.
    """

    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def extract_corpus_samples(self) -> List[MusicalContext]:
        """
        Extract musical contexts from configured corpus sources.

        In production, returns representative mock samples that demonstrate
        the variety of musical contexts needed for calibration.
        """
        # For production, we use representative samples that cover
        # the main analysis scenarios
        samples = [
            # Diatonic simple - perfect authentic cadence
            MusicalContext(
                key="C major",
                chords=["C", "F", "G", "C"],
                roman_numerals=["I", "IV", "V", "I"],
                melody=["C5", "F5", "G5", "C5"],
                metadata={"source": "mock", "difficulty": "simple"},
            ),
            # Modal complex - Dorian progression
            MusicalContext(
                key="D dorian",
                chords=["Dm", "C", "Dm", "Gm"],
                roman_numerals=["i", "♭VII", "i", "iv"],
                melody=["D5", "C5", "D5", "G5"],
                metadata={"source": "mock", "difficulty": "modal"},
            ),
            # Chromatic moderate - secondary dominant
            MusicalContext(
                key="G major",
                chords=["G", "E7", "Am", "D7"],
                roman_numerals=["I", "V/vi", "vi", "V"],
                melody=["G5", "E5", "A5", "D5"],
                metadata={"source": "mock", "difficulty": "chromatic"},
            ),
            # Jazz progression
            MusicalContext(
                key="F major",
                chords=["Fmaj7", "Dm7", "Gm7", "C7"],
                roman_numerals=["Imaj7", "vi7", "ii7", "V7"],
                melody=["F5", "D5", "G5", "C5"],
                metadata={"source": "mock", "difficulty": "jazz"},
            ),
        ]

        # Generate transpositions
        transposed = []
        for sample in samples:
            keys_to_use = self.config.transposition_keys or []
            for key in keys_to_use[:2]:  # Limit for production
                if key != sample.key.split()[0]:
                    transposed.append(self._transpose_mock(sample, key))

        samples.extend(transposed)
        self.logger.info(f"Extracted {len(samples)} corpus samples (mock)")
        return samples

    def _transpose_mock(
        self, sample: MusicalContext, target_key: str
    ) -> MusicalContext:
        """Create a transposed version of a sample."""
        # Simplified transposition for mock data
        return MusicalContext(
            key=f"{target_key} "
            f"{sample.key.split()[1] if ' ' in sample.key else 'major'}",
            chords=sample.chords,  # Would transpose in real implementation
            roman_numerals=sample.roman_numerals,  # These stay the same
            melody=sample.melody,  # Would transpose in real implementation
            metadata={**sample.metadata, "transposed_from": sample.key},
        )
