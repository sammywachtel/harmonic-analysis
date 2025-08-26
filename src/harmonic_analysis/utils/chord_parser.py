"""
Chord Logic and Parsing

Comprehensive chord detection and analysis including:
- Complex chord symbol parsing (major, minor, diminished, augmented, 7ths, etc.)
- Partial chord detection (2-note and 3-note combinations)
- Suspended chord handling (sus2, sus4)
- Add chord recognition
- Inversion detection
- Confidence scoring
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Pitch class to note name mapping
NOTE_NAMES = ["C", "C♯", "D", "E♭", "E", "F", "F♯", "G", "A♭", "A", "B♭", "B"]
NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_NAMES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Note to pitch class mapping
NOTE_TO_PITCH_CLASS = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "F": 5,
    "E#": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}


@dataclass
class ChordTemplate:
    """Template for chord detection"""

    intervals: List[int]
    symbol: str
    name: str
    min_notes: int = 3
    confidence: float = 1.0


@dataclass
class ChordMatch:
    """Result of chord detection"""

    chord_symbol: str
    chord_name: str
    root: int  # Pitch class
    root_name: str
    intervals: List[int]
    confidence: float
    inversion: str
    bass_note: int
    is_partial: bool = False
    missing_notes: Optional[List[str]] = None
    completion_suggestion: Optional[str] = None
    pedagogical_note: Optional[str] = None


class ChordParser:
    """Comprehensive chord parsing and detection"""

    def __init__(self) -> None:
        # Define chord templates
        self.chord_templates = {
            # Basic triads
            "major": ChordTemplate([0, 4, 7], "", "Major"),
            "minor": ChordTemplate([0, 3, 7], "m", "Minor"),
            "diminished": ChordTemplate([0, 3, 6], "°", "Diminished"),
            "augmented": ChordTemplate([0, 4, 8], "+", "Augmented"),
            # Suspended chords (complete)
            "sus2": ChordTemplate([0, 2, 7], "sus2", "Suspended 2nd"),
            "sus4": ChordTemplate([0, 5, 7], "sus4", "Suspended 4th"),
            # Partial suspended chords (2-note combinations)
            "sus2Partial": ChordTemplate(
                [0, 2], "sus2(no5)", "Suspended 2nd (no 5th)", 2, 0.75
            ),
            "sus4Partial": ChordTemplate(
                [0, 5], "sus4(no5)", "Suspended 4th (no 5th)", 2, 0.75
            ),
            # Partial triads (2-note combinations)
            "majorPartial": ChordTemplate([0, 4], "(no5)", "Major (no 5th)", 2, 0.70),
            "minorPartial": ChordTemplate([0, 3], "m(no5)", "Minor (no 5th)", 2, 0.70),
            "fifthPartial": ChordTemplate([0, 7], "5", "Power Chord (5th)", 2, 0.85),
            # Partial seventh chords (3-note combinations missing one tone)
            "dom7NoFifth": ChordTemplate(
                [0, 4, 10], "7(no5)", "Dominant 7th (no 5th)", 3, 0.80
            ),
            "min7NoFifth": ChordTemplate(
                [0, 3, 10], "m7(no5)", "Minor 7th (no 5th)", 3, 0.80
            ),
            "maj7NoFifth": ChordTemplate(
                [0, 4, 11], "maj7(no5)", "Major 7th (no 5th)", 3, 0.80
            ),
            # Incomplete sus chords with extensions
            "sus2Add7": ChordTemplate(
                [0, 2, 10], "sus2(add7)", "Suspended 2nd add 7th", 3, 0.75
            ),
            "sus4Add7": ChordTemplate(
                [0, 5, 10], "sus4(add7)", "Suspended 4th add 7th", 3, 0.75
            ),
            # Add chords (retaining 3rd + added note)
            "majorAdd4": ChordTemplate([0, 4, 5], "(add4)", "Major add 4th"),
            "minorAdd4": ChordTemplate([0, 3, 5], "m(add4)", "Minor add 4th"),
            # Seventh chords
            "major7": ChordTemplate([0, 4, 7, 11], "maj7", "Major 7th"),
            "minor7": ChordTemplate([0, 3, 7, 10], "m7", "Minor 7th"),
            "dominant7": ChordTemplate([0, 4, 7, 10], "7", "Dominant 7th"),
            "diminished7": ChordTemplate([0, 3, 6, 9], "dim7", "Diminished 7th"),
            "halfDiminished7": ChordTemplate(
                [0, 3, 6, 10], "m7♭5", "Half-Diminished 7th"
            ),
            "augmented7": ChordTemplate([0, 4, 8, 10], "7+", "Augmented 7th"),
            "minorMaj7": ChordTemplate([0, 3, 7, 11], "m(maj7)", "Minor Major 7th"),
        }

    def find_chord_matches(self, note_numbers: List[int]) -> List[ChordMatch]:
        """
        Find the best chord matches for a given set of MIDI note numbers

        Args:
            note_numbers: Array of MIDI note numbers

        Returns:
            Array of possible chord matches, sorted by confidence
        """
        if len(note_numbers) < 2:
            return []  # Need at least 2 notes for chord analysis

        # Convert to pitch classes and remove duplicates
        pitch_classes = list(set(note % 12 for note in note_numbers))
        pitch_classes.sort()

        matches = []

        # Try each pitch class as a potential root
        for root_pitch in pitch_classes:
            # Calculate intervals from this root
            intervals = [(pc - root_pitch + 12) % 12 for pc in pitch_classes]

            # Check against each chord template
            for chord_type, template in self.chord_templates.items():
                min_notes_required = template.min_notes

                # Skip if we don't have enough notes for this template
                if len(note_numbers) < min_notes_required:
                    continue

                # Special handling for 3-note patterns
                has_all_intervals = self._check_pattern_match(
                    intervals,
                    template.intervals,
                    pitch_classes,
                    root_pitch,
                    chord_type,
                    len(note_numbers),
                )

                if has_all_intervals:
                    root_name = NOTE_NAMES[root_pitch]
                    chord_symbol = root_name + template.symbol

                    # Calculate confidence
                    confidence = self._calculate_confidence(
                        intervals,
                        template.intervals,
                        len(note_numbers),
                        chord_type,
                        template,
                    )

                    # Check for inversion - use LOWEST MIDI note number
                    lowest_midi_note = min(note_numbers)
                    bass_note = lowest_midi_note % 12
                    inversion = (
                        f"/{NOTE_NAMES[bass_note]}" if bass_note != root_pitch else ""
                    )

                    # Determine if partial and get pedagogical info
                    (
                        is_partial,
                        missing_notes,
                        completion,
                        pedagogical,
                    ) = self._get_chord_info(
                        chord_type, intervals, root_pitch, len(note_numbers)
                    )

                    matches.append(
                        ChordMatch(
                            chord_symbol=chord_symbol + inversion,
                            chord_name=template.name,
                            root=root_pitch,
                            root_name=root_name,
                            intervals=intervals,
                            confidence=confidence,
                            inversion=inversion,
                            bass_note=bass_note,
                            is_partial=is_partial,
                            missing_notes=missing_notes if missing_notes else None,
                            completion_suggestion=completion if completion else None,
                            pedagogical_note=pedagogical if pedagogical else None,
                        )
                    )

        # Sort by confidence (highest first) and return top matches
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:5]  # Return top 5 matches

    def _check_pattern_match(
        self,
        intervals: List[int],
        template_intervals: List[int],
        pitch_classes: List[int],
        root_pitch: int,
        chord_type: str,
        note_count: int,
    ) -> bool:
        """Check if intervals match template with special pattern handling"""

        # Basic check - all template intervals present
        has_all_intervals = all(
            interval in intervals for interval in template_intervals
        )

        # Special handling for 3-note patterns
        if note_count == 3:
            sorted_pitches = sorted(pitch_classes)

            # A-C-D pattern (pitches 9, 0, 2): minor 3rd + 4th from A
            if sorted_pitches == [0, 2, 9]:
                if "sus" in chord_type:
                    has_all_intervals = False  # Block all sus variants
                elif chord_type == "minorAdd4" and root_pitch == 9:  # A root
                    has_all_intervals = True  # Force match for Am(add4)

            # A-C#-D pattern (pitches 9, 1, 2): major 3rd + 4th from A
            elif sorted_pitches == [1, 2, 9]:
                if chord_type == "sus4Partial" and root_pitch == 9:  # A root
                    has_all_intervals = True
                elif chord_type == "majorAdd4" and root_pitch == 9:  # A root
                    has_all_intervals = True

            # Fallback to interval-based logic
            else:
                # Major 3rd + 4th pattern
                if 0 in intervals and 4 in intervals and 5 in intervals:
                    if chord_type == "majorAdd4":
                        has_all_intervals = False  # Don't match add4
                    elif chord_type == "sus4Partial":
                        has_all_intervals = True  # Force match for sus4 partial

                # Minor 3rd + 4th pattern
                elif 0 in intervals and 3 in intervals and 5 in intervals:
                    if chord_type in ["sus4", "sus4Partial"]:
                        has_all_intervals = False  # Don't match sus
                    elif chord_type == "minorAdd4":
                        has_all_intervals = True  # Force match for minor add4

        return has_all_intervals

    def _calculate_confidence(
        self,
        played_intervals: List[int],
        template_intervals: List[int],
        note_count: int,
        chord_type: str,
        template: ChordTemplate,
    ) -> float:
        """Calculate confidence score for chord match"""

        total_template_notes = len(template_intervals)
        matching_notes = sum(
            1 for interval in template_intervals if interval in played_intervals
        )
        extra_notes = len(played_intervals) - total_template_notes

        # Use predefined confidence from template if available
        confidence = (
            template.confidence
            if hasattr(template, "confidence")
            else (matching_notes / total_template_notes)
        )

        # Adjust confidence for partial chords (2-note combinations)
        if note_count == 2 and total_template_notes == 2:
            # Use template confidence for exact matches of partial chords
            # (like majorPartial)
            confidence = (
                (
                    template.confidence
                    if hasattr(template, "confidence") and template.confidence
                    else 0.85
                )
                if matching_notes == 2
                else confidence
            )
        elif note_count == 2 and total_template_notes > 2:
            confidence *= 0.7  # Partial match of larger chord

        # Penalize for extra notes
        if extra_notes > 0:
            confidence -= extra_notes * 0.08

        # Bonus for exact match
        if len(played_intervals) == total_template_notes and extra_notes == 0:
            confidence += 0.1

        # Special confidence adjustments for specific patterns
        if note_count == 3 and 4 in played_intervals and 5 in played_intervals:
            # Major 3rd + 4th - favor sus4 interpretation
            if 5 in template_intervals and 4 not in template_intervals:
                confidence = 0.92  # Sus4 template
            elif 4 in template_intervals and 5 in template_intervals:
                confidence = 0.75  # Major add4 template
        elif note_count == 3 and 3 in played_intervals and 5 in played_intervals:
            # Minor 3rd + 4th - favor add4 interpretation
            if 3 in template_intervals and 5 in template_intervals:
                confidence = 0.88  # Minor add4 template

        return max(0, min(1, confidence))  # Clamp between 0 and 1

    def _get_chord_info(
        self, chord_type: str, intervals: List[int], root_pitch: int, note_count: int
    ) -> Tuple[bool, List[str], str, str]:
        """Get chord information for partial chords and pedagogical notes"""

        is_partial = "Partial" in chord_type or note_count < 3
        missing_notes = []
        completion_suggestion = ""
        pedagogical_note = ""

        root_name = NOTE_NAMES[root_pitch]

        if chord_type == "sus4Partial" and len(intervals) == 2:
            missing_notes = [NOTE_NAMES[(root_pitch + 7) % 12]]  # Missing 5th
            completion_suggestion = (
                f"{root_name}-{NOTE_NAMES[(root_pitch + 5) % 12]}-"
                f"{NOTE_NAMES[(root_pitch + 7) % 12]}"
            )
            pedagogical_note = (
                "Suspended 4th chord - the 4th creates tension that "
                "typically resolves down to the 3rd"
            )

        elif chord_type == "sus2Partial" and len(intervals) == 2:
            missing_notes = [NOTE_NAMES[(root_pitch + 7) % 12]]  # Missing 5th
            completion_suggestion = (
                f"{root_name}-{NOTE_NAMES[(root_pitch + 2) % 12]}-"
                f"{NOTE_NAMES[(root_pitch + 7) % 12]}"
            )
            pedagogical_note = "Suspended 2nd chord - creates an open, unresolved sound"

        elif chord_type == "majorAdd4":
            pedagogical_note = (
                "Major triad with added 4th - retains major 3rd while "
                "adding 4th degree tension"
            )

        elif chord_type == "minorAdd4":
            pedagogical_note = (
                "Minor chord with added 4th - retains minor 3rd while "
                "adding upper tension. Common in folk and contemporary styles."
            )

        elif chord_type == "majorPartial":
            missing_notes = [NOTE_NAMES[(root_pitch + 7) % 12]]  # Missing 5th
            completion_suggestion = (
                f"{root_name}-{NOTE_NAMES[(root_pitch + 4) % 12]}-"
                f"{NOTE_NAMES[(root_pitch + 7) % 12]}"
            )
            pedagogical_note = (
                "Major triad without 5th - emphasizes the major 3rd "
                "character. Often used in tight voicings."
            )

        elif chord_type == "minorPartial":
            missing_notes = [NOTE_NAMES[(root_pitch + 7) % 12]]  # Missing 5th
            completion_suggestion = (
                f"{root_name}-{NOTE_NAMES[(root_pitch + 3) % 12]}-"
                f"{NOTE_NAMES[(root_pitch + 7) % 12]}"
            )
            pedagogical_note = (
                "Minor triad without 5th - emphasizes the minor 3rd "
                "character. Creates a more focused harmonic color."
            )

        elif chord_type == "fifthPartial":
            missing_notes = [
                NOTE_NAMES[(root_pitch + 3) % 12],
                NOTE_NAMES[(root_pitch + 4) % 12],
            ]
            completion_suggestion = (
                f"{root_name}-{NOTE_NAMES[(root_pitch + 4) % 12]}-"
                f"{NOTE_NAMES[(root_pitch + 7) % 12]} (major) or "
                f"{root_name}-{NOTE_NAMES[(root_pitch + 3) % 12]}-"
                f"{NOTE_NAMES[(root_pitch + 7) % 12]} (minor)"
            )
            pedagogical_note = (
                "Power chord - perfect 5th interval creates strong, "
                "neutral harmony. Common in rock and metal music."
            )

        elif chord_type in ["dom7NoFifth", "min7NoFifth", "maj7NoFifth"]:
            missing_notes = [NOTE_NAMES[(root_pitch + 7) % 12]]  # Missing 5th
            completion_suggestion = (
                f"Add {NOTE_NAMES[(root_pitch + 7) % 12]} to complete the seventh chord"
            )
            pedagogical_note = (
                "Seventh chord without 5th - emphasizes the essential "
                "harmonic function (root, 3rd, 7th) while saving space "
                "in dense arrangements."
            )

        elif chord_type in ["sus2Add7", "sus4Add7"]:
            missing_notes = [NOTE_NAMES[(root_pitch + 7) % 12]]  # Missing 5th
            completion_suggestion = (
                f"Add {NOTE_NAMES[(root_pitch + 7) % 12]} for fuller voicing"
            )
            pedagogical_note = (
                "Suspended chord with 7th - combines suspension tension "
                "with seventh harmony. Creates sophisticated, unresolved sound."
            )

        # Special handling for 3-note combinations
        if note_count == 3 and 4 in intervals and 5 in intervals:
            if chord_type == "sus4Partial":
                missing_notes = [NOTE_NAMES[(root_pitch + 7) % 12]]
                completion_suggestion = (
                    f"{root_name}-{NOTE_NAMES[(root_pitch + 5) % 12]}-"
                    f"{NOTE_NAMES[(root_pitch + 7) % 12]}"
                )
                pedagogical_note = (
                    "Partial sus4 chord - the 4th creates harmonic tension "
                    "typically resolved to the 3rd. Missing 5th is common "
                    "in contemporary voicings."
                )

        elif note_count == 3 and 3 in intervals and 5 in intervals:
            if chord_type == "minorAdd4":
                pedagogical_note = (
                    "Minor chord with added 4th - retains minor 3rd while "
                    "adding upper tension. Common in folk and contemporary styles."
                )

        return is_partial, missing_notes, completion_suggestion, pedagogical_note

    def parse_chord_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Parse a chord symbol into its components

        Args:
            symbol: Chord symbol string (e.g., 'Cmaj7', 'F#m7b5')

        Returns:
            Dictionary with chord components or None if parsing fails
        """
        if not symbol or not symbol.strip():
            return None

        clean_symbol = symbol.strip()

        # Extract root note
        root_match = re.match(r"^([A-G][#b♯♭]?)", clean_symbol)
        if not root_match:
            return None

        root_note = root_match.group(1)

        # Normalize sharps and flats
        root_note = root_note.replace("♯", "#").replace("♭", "b")

        # Get pitch class
        pitch_class = NOTE_TO_PITCH_CLASS.get(root_note)
        if pitch_class is None:
            return None

        # Extract remainder (quality and extensions)
        remainder = clean_symbol[len(root_note) :]

        # Determine chord quality
        quality = self._parse_chord_quality(remainder)

        # Extract bass note if present (for inversions)
        bass_note = None
        if "/" in remainder:
            bass_match = re.search(r"/([A-G][#b♯♭]?)", remainder)
            if bass_match:
                bass_note = bass_match.group(1).replace("♯", "#").replace("♭", "b")
                remainder = remainder[: remainder.index("/")]

        # Extract extensions
        extensions = self._parse_extensions(remainder)

        return {
            "root": root_note,
            "pitch_class": pitch_class,
            "quality": quality,
            "extensions": extensions,
            "bass_note": bass_note,
            "original": symbol,
        }

    def _parse_chord_quality(self, suffix: str) -> str:
        """Parse chord quality from suffix"""

        suffix_lower = suffix.lower()

        # Check for specific qualities (order matters for overlapping patterns)
        if "m7b5" in suffix_lower or "ø" in suffix or "m7♭5" in suffix_lower:
            return "half_diminished"
        elif "dim7" in suffix_lower:
            return "diminished7"
        elif "dim" in suffix_lower or "°" in suffix:
            return "diminished"
        elif "7+" in suffix or "+7" in suffix:
            return "augmented7"
        elif "aug" in suffix_lower or "+" in suffix:
            return "augmented"
        elif "m(maj7)" in suffix_lower or "mM7" in suffix:
            return "minor_major7"
        elif "maj7" in suffix_lower or "M7" in suffix:
            return "major7"
        elif "dom7" in suffix_lower:
            return "dominant7"
        elif "m7" in suffix_lower:
            return "minor7"
        elif "7" in suffix:
            return "dominant7"
        elif "sus4" in suffix_lower:
            return "sus4"
        elif "sus2" in suffix_lower:
            return "sus2"
        elif "sus" in suffix_lower:
            return "sus4"  # Default sus to sus4
        elif suffix.startswith("m") and not suffix.startswith("maj"):
            return "minor"
        else:
            return "major"

    def _parse_extensions(self, suffix: str) -> List[str]:
        """Parse chord extensions from suffix"""

        extensions = []

        # Common extensions
        if "9" in suffix:
            extensions.append("9")
        if "11" in suffix:
            extensions.append("11")
        if "13" in suffix:
            extensions.append("13")
        if "add" in suffix.lower():
            add_match = re.search(r"add(\d+)", suffix.lower())
            if add_match:
                extensions.append(f"add{add_match.group(1)}")

        return extensions

    def detect_partial_sus_chords(self, note_numbers: List[int]) -> List[ChordMatch]:
        """
        Specialized function for detecting partial suspended chords
        Handles specific cases like A-C#-D and A-C-D

        Args:
            note_numbers: MIDI note numbers

        Returns:
            List of chord matches for partial sus chords
        """
        if len(note_numbers) != 3:
            return []

        matches = []
        pitch_classes = list(set(note % 12 for note in note_numbers))
        pitch_classes.sort()

        # Try each pitch class as root
        for root_pitch in pitch_classes:
            intervals = [(pc - root_pitch + 12) % 12 for pc in pitch_classes]
            root_name = NOTE_NAMES[root_pitch]

            # Case 1: Root + Major 3rd + 4th (like A-C#-D)
            if 0 in intervals and 4 in intervals and 5 in intervals:
                matches.append(
                    ChordMatch(
                        chord_symbol=f"{root_name}sus4(no5)",
                        chord_name="Suspended 4th (no 5th)",
                        root=root_pitch,
                        root_name=root_name,
                        intervals=intervals,
                        confidence=0.88,
                        inversion="",
                        bass_note=root_pitch,
                        is_partial=True,
                        missing_notes=[NOTE_NAMES[(root_pitch + 7) % 12]],
                        completion_suggestion=(
                            f"{root_name}-{NOTE_NAMES[(root_pitch + 5) % 12]}-"
                            f"{NOTE_NAMES[(root_pitch + 7) % 12]}"
                        ),
                        pedagogical_note=(
                            "Partial sus4 chord - the 4th creates harmonic tension "
                            "typically resolved to the 3rd. Missing 5th is common "
                            "in contemporary voicings."
                        ),
                    )
                )

            # Case 2: Root + Minor 3rd + 4th (like A-C-D)
            if 0 in intervals and 3 in intervals and 5 in intervals:
                matches.append(
                    ChordMatch(
                        chord_symbol=f"{root_name}m(add4)",
                        chord_name="Minor add 4th",
                        root=root_pitch,
                        root_name=root_name,
                        intervals=intervals,
                        confidence=0.85,
                        inversion="",
                        bass_note=root_pitch,
                        pedagogical_note=(
                            "Minor chord with added 4th - retains minor 3rd while "
                            "adding upper tension. Common in folk and "
                            "contemporary styles."
                        ),
                    )
                )

        return matches


def parse_chord_progression(input_str: str) -> List[str]:
    """
    Parse chord progression string into individual chord symbols

    Args:
        input_str: Chord progression string (e.g., "Am F C G" or "Am | F | C | G")

    Returns:
        List of chord symbols
    """
    # Remove measure separators and split by spaces
    return [
        chord
        for chord in input_str.replace("|", " ").replace(",", " ").split()
        if chord
    ]


# Convenience functions for common use cases
def find_chords_from_midi(midi_notes: List[int]) -> List[ChordMatch]:
    """Find chord matches from MIDI note numbers"""
    parser = ChordParser()
    return parser.find_chord_matches(midi_notes)


def parse_chord(symbol: str) -> Optional[Dict[str, Any]]:
    """Parse a chord symbol"""
    parser = ChordParser()
    return parser.parse_chord_symbol(symbol)
