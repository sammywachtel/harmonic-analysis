"""
Chord parsing and logic for music theory analysis.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from ..types import ChordFunction
from .scales import NOTE_TO_PITCH_CLASS


@dataclass
class ChordMatch:
    """Result of chord parsing and analysis."""

    chord_symbol: str
    root: str
    root_pitch: int
    quality: str
    bass_note: Optional[str] = None
    bass_pitch: Optional[int] = None
    extensions: Optional[List[str]] = None
    inversion: int = 0  # 0 = root position

    def __post_init__(self) -> None:
        if self.extensions is None:
            self.extensions = []


class ChordParser:
    """Parser for chord symbols into structured data."""

    # Regex patterns for chord parsing
    CHORD_PATTERN = re.compile(
        r"^([A-G][#b]?)"  # Root note
        + r"(maj|min|m|dim|aug|\+|°|ø)?"  # Quality
        + r"(\d+)?"  # Extension
        + r"(.*?)"  # Other extensions/alterations
        + r"(?:/([A-G][#b]?))?$"  # Slash bass
    )

    def __init__(self) -> None:
        self.quality_mappings = {
            "": "major",
            "maj": "major",
            "M": "major",
            "m": "minor",
            "min": "minor",
            "-": "minor",
            "dim": "diminished",
            "°": "diminished",
            "ø": "half_diminished",
            "aug": "augmented",
            "+": "augmented",
        }

    def parse_chord(self, chord_symbol: str) -> ChordMatch:
        """
        Parse a chord symbol into structured components.

        Args:
            chord_symbol: Chord symbol to parse (e.g., "Cm7", "F#dim", "C/E")

        Returns:
            ChordMatch object with parsed components

        Raises:
            ValueError: If chord symbol cannot be parsed
        """
        chord_symbol = chord_symbol.strip()
        if not chord_symbol:
            raise ValueError("Empty chord symbol")

        match = self.CHORD_PATTERN.match(chord_symbol)
        if not match:
            raise ValueError(f"Cannot parse chord symbol: {chord_symbol}")

        root, quality_str, extension, other, bass = match.groups()

        # Parse root note
        if root not in NOTE_TO_PITCH_CLASS:
            raise ValueError(f"Invalid root note: {root}")

        root_pitch = NOTE_TO_PITCH_CLASS[root]

        # Parse quality
        quality = self.quality_mappings.get(quality_str or "", "major")

        # Parse bass note if present
        bass_note = None
        bass_pitch = None
        inversion = 0

        if bass:
            if bass not in NOTE_TO_PITCH_CLASS:
                raise ValueError(f"Invalid bass note: {bass}")
            bass_note = bass
            bass_pitch = NOTE_TO_PITCH_CLASS[bass]
            inversion = self._calculate_inversion(root_pitch, bass_pitch, quality)

        # Parse extensions
        extensions = []
        if extension:
            extensions.append(extension)

        # Parse other alterations (simplified for now)
        if other:
            extensions.extend(self._parse_alterations(other))

        return ChordMatch(
            chord_symbol=chord_symbol,
            root=root,
            root_pitch=root_pitch,
            quality=quality,
            bass_note=bass_note,
            bass_pitch=bass_pitch,
            extensions=extensions,
            inversion=inversion,
        )

    def _calculate_inversion(
        self, root_pitch: int, bass_pitch: int, quality: str
    ) -> int:
        """Calculate inversion number based on root and bass notes."""
        interval = (bass_pitch - root_pitch) % 12

        # Simplified inversion detection
        if interval == 0:
            return 0  # Root position
        elif interval == 4:  # Major third
            return 1  # First inversion
        elif interval == 3:  # Minor third
            return 1  # First inversion
        elif interval == 7:  # Perfect fifth
            return 2  # Second inversion
        else:
            return 1  # Default to first inversion for unknown intervals

    def _parse_alterations(self, alterations: str) -> List[str]:
        """Parse chord alterations and extensions."""
        # Simplified parsing - can be expanded
        extensions = []
        if "sus" in alterations:
            extensions.append("sus")
        if "add" in alterations:
            extensions.append("add")
        return extensions


def parse_chord_progression(progression_input: str) -> List[str]:
    """
    Parse a chord progression string into individual chord symbols.

    Args:
        progression_input: Space or pipe-separated chord symbols

    Returns:
        List of individual chord symbols
    """
    if not progression_input.strip():
        raise ValueError("Empty chord progression")

    # Handle various separators
    chords = progression_input.replace("|", " ").split()
    chords = [chord.strip() for chord in chords if chord.strip()]

    if not chords:
        raise ValueError("No valid chords found in progression")

    return chords


def find_chord_matches(chord_symbols: List[str]) -> List[ChordMatch]:
    """
    Parse multiple chord symbols into ChordMatch objects.

    Args:
        chord_symbols: List of chord symbols to parse

    Returns:
        List of ChordMatch objects
    """
    parser = ChordParser()
    matches = []

    for chord_symbol in chord_symbols:
        try:
            match = parser.parse_chord(chord_symbol)
            matches.append(match)
        except ValueError:
            # For now, create a basic match for unparseable chords
            matches.append(
                ChordMatch(
                    chord_symbol=chord_symbol,
                    root=chord_symbol[0] if chord_symbol else "C",
                    root_pitch=0,
                    quality="unknown",
                )
            )

    return matches


def determine_chord_function(
    chord_match: ChordMatch, key_center: str, mode: str = "major"
) -> ChordFunction:
    """
    Determine the harmonic function of a chord in a given key.

    Args:
        chord_match: Parsed chord information
        key_center: Tonal center for analysis
        mode: Mode context ("major" or "minor")

    Returns:
        ChordFunction enum value
    """
    if key_center not in NOTE_TO_PITCH_CLASS:
        return ChordFunction.CHROMATIC

    key_pitch = NOTE_TO_PITCH_CLASS[key_center]
    chord_pitch = chord_match.root_pitch

    # Calculate scale degree
    scale_degree = (chord_pitch - key_pitch) % 12

    # Simplified function mapping
    if mode == "major":
        function_map = {
            0: ChordFunction.TONIC,  # I
            2: ChordFunction.PREDOMINANT,  # ii
            4: ChordFunction.TONIC,  # iii (relative minor)
            5: ChordFunction.SUBDOMINANT,  # IV
            7: ChordFunction.DOMINANT,  # V
            9: ChordFunction.TONIC,  # vi (relative minor)
            11: ChordFunction.LEADING_TONE,  # vii°
        }
    else:  # minor mode
        function_map = {
            0: ChordFunction.TONIC,  # i
            2: ChordFunction.PREDOMINANT,  # ii°
            3: ChordFunction.TONIC,  # III
            5: ChordFunction.SUBDOMINANT,  # iv
            7: ChordFunction.DOMINANT,  # V
            8: ChordFunction.SUBDOMINANT,  # VI
            10: ChordFunction.SUBDOMINANT,  # VII
        }

    return function_map.get(scale_degree, ChordFunction.CHROMATIC)
