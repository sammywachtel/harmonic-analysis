"""
Roman Numeral to Chord Symbol Converter

Converts Roman numeral notation to chord symbols
for analysis by the harmonic analysis library.
"""

import re
from typing import List, Optional

from .scales import NOTE_TO_PITCH_CLASS, PITCH_CLASS_NAMES

# Enharmonic equivalents - prefer flats for flat Roman numerals
ENHARMONIC_FLATS = {"C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb"}

# Roman numeral to degree mapping
ROMAN_DEGREE_MAP = {
    # Major key romans (uppercase = major quality, used in major keys)
    "I": 0,
    "II": 2,
    "III": 4,
    "IV": 5,
    "V": 7,
    "VI": 9,
    "VII": 11,
    # Minor key romans (lowercase = minor quality, used in both major and minor keys)
    "i": 0,
    "ii": 2,
    "iii": 4,
    "iv": 5,
    "v": 7,
    "vi": 9,
    "vii": 11,
    # Special cases with accidentals (major versions)
    "bII": 1,
    "bIII": 3,
    "bVI": 8,
    "bVII": 10,
    "#IV": 6,
    "#V": 8,
    # Special cases with accidentals (minor versions)
    "bii": 1,
    "biii": 3,
    "bvi": 8,
    "bvii": 10,
    "#iv": 6,
    "#v": 8,
}

# Basic chord quality patterns
CHORD_QUALITY_MAP = {
    # Major romans -> major chords
    "I": "",
    "II": "",
    "III": "",
    "IV": "",
    "V": "",
    "VI": "",
    # Minor romans -> minor chords
    "i": "m",
    "ii": "m",
    "iii": "m",
    "iv": "m",
    "v": "m",
    "vi": "m",
    # Diminished
    "vii": "dim",
    "ii°": "dim",
    "viio": "dim",
    "vii°": "dim",
    # Augmented
    "III+": "+",
    "VI+": "+",
}


def convert_roman_numerals_to_chords(
    roman_progression: str, parent_key: str
) -> List[str]:
    """
    Convert Roman numeral progression to chord symbols.

    Args:
        roman_progression: Space-separated Roman numerals (e.g., "V/ii ii6 V64/ii")
        parent_key: Parent key (e.g., "C major", "A minor")

    Returns:
        List of chord symbols (e.g., ["A7", "Dm6", "G7/B", "Dm", "F/A", "G", "C"])

    Examples:
        >>> convert_roman_numerals_to_chords("V/ii ii V I", "C major")
        ["A7", "Dm", "G", "C"]

        >>> convert_roman_numerals_to_chords("i iv V i", "A minor")
        ["Am", "Dm", "E", "Am"]
    """
    if not parent_key:
        raise ValueError("Parent key is required for Roman numeral conversion")

    # Extract key root and mode
    key_parts = parent_key.split()
    if len(key_parts) < 2:
        raise ValueError(f"Invalid parent key format: {parent_key}")

    key_root = key_parts[0]
    key_mode = key_parts[1].lower()

    if key_root not in NOTE_TO_PITCH_CLASS:
        raise ValueError(f"Invalid key root: {key_root}")

    if key_mode not in ["major", "minor"]:
        raise ValueError(f"Invalid key mode: {key_mode}")

    # Parse Roman numerals
    roman_tokens = roman_progression.strip().split()
    chord_symbols = []

    for token in roman_tokens:
        try:
            chord_symbol = _convert_single_roman_numeral(token, key_root, key_mode)
            chord_symbols.append(chord_symbol)
        except Exception:
            # If conversion fails, return the original token as fallback
            chord_symbols.append(token)

    return chord_symbols


def _convert_single_roman_numeral(roman: str, key_root: str, key_mode: str) -> str:
    """Convert a single Roman numeral to chord symbol."""

    # Handle secondary dominants (V/ii, V7/vi, etc.)
    if "/" in roman:
        return _convert_secondary_dominant(roman, key_root, key_mode)

    # Handle inversions (I6, V64, etc.) and figured bass (I⁶, V⁶⁴, etc.)
    inversion = None
    base_roman = roman

    # Check for figured bass notation (⁶, ⁶⁴, ⁴²)
    if "⁶⁴" in roman:
        inversion = "64"
        base_roman = roman.replace("⁶⁴", "")
    elif "⁶" in roman:
        inversion = "6"
        base_roman = roman.replace("⁶", "")
    elif "⁴²" in roman:
        inversion = "42"
        base_roman = roman.replace("⁴²", "")
    # Check for regular inversion numbers (6, 64, 42)
    elif re.search(r"\d", roman):
        inversion_match = re.search(r"(\d+)", roman)
        if inversion_match:
            inversion = inversion_match.group(1)
            base_roman = re.sub(r"\d+", "", roman)

    # Clean up base roman (remove accidentals for lookup)
    clean_roman = _clean_roman_for_lookup(base_roman)

    # Get scale degree
    scale_degree = ROMAN_DEGREE_MAP.get(clean_roman)
    if scale_degree is None:
        # Try with opposite case for flexible parsing
        alt_case = clean_roman.swapcase()
        scale_degree = ROMAN_DEGREE_MAP.get(alt_case)
        if scale_degree is None:
            raise ValueError(f"Unknown Roman numeral: {clean_roman}")

    # Calculate root note
    key_pitch = NOTE_TO_PITCH_CLASS[key_root]
    root_pitch = (key_pitch + scale_degree) % 12
    root_note = PITCH_CLASS_NAMES[root_pitch]

    # Use flat enharmonic if Roman numeral contains flat
    if "b" in roman and root_note in ENHARMONIC_FLATS:
        root_note = ENHARMONIC_FLATS[root_note]

    # Determine chord quality
    chord_quality = _get_chord_quality(base_roman, key_mode)

    # Handle seventh chords
    seventh = ""
    if "7" in roman and "64" not in roman and "42" not in roman:
        seventh = "7"

    # Build chord symbol
    chord_symbol = f"{root_note}{chord_quality}{seventh}"

    # Add inversion if present
    if inversion:
        bass_note = _calculate_bass_note(root_note, chord_quality, inversion, key_root)
        if bass_note:
            chord_symbol += f"/{bass_note}"

    return chord_symbol


def _convert_secondary_dominant(roman: str, key_root: str, key_mode: str) -> str:
    """Convert secondary dominants like V/ii, V7/vi, V64/ii to chord symbols."""
    parts = roman.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid secondary dominant format: {roman}")

    dominant_part, target_part = parts

    # Handle inversions in the dominant part (V64/ii, V7/vi, etc.)
    # Need to distinguish inversions (6, 64, 42) from chord extensions (7, 9, 11, 13)
    inversion = None
    base_dominant = dominant_part

    # Look for figured bass notation first (⁶⁴, ⁶, ⁴²)
    if "⁶⁴" in dominant_part:
        inversion = "64"
        base_dominant = dominant_part.replace("⁶⁴", "")
    elif "⁶" in dominant_part:
        inversion = "6"
        base_dominant = dominant_part.replace("⁶", "")
    elif "⁴²" in dominant_part:
        inversion = "42"
        base_dominant = dominant_part.replace("⁴²", "")
    else:
        # Look for regular numeric inversion patterns (6, 64, 42, 43)
        inversion_match = re.search(
            r"(64|42|43|6)(?![789])", dominant_part
        )  # Don't match 67, 69, etc.
        if inversion_match:
            inversion = inversion_match.group(1)
            base_dominant = re.sub(r"(64|42|43|6)(?![789])", "", dominant_part)

    # Handle figured bass on target part (non-standard but handle as fallback)
    clean_target = target_part
    target_figured_bass = None
    if "⁶⁴" in clean_target:
        target_figured_bass = "64"
        clean_target = clean_target.replace("⁶⁴", "")
    elif "⁶" in clean_target:
        target_figured_bass = "6"
        clean_target = clean_target.replace("⁶", "")
    elif "⁴²" in clean_target:
        target_figured_bass = "42"
        clean_target = clean_target.replace("⁴²", "")

    # If figured bass was on target, apply it to dominant instead
    if target_figured_bass and not inversion:
        inversion = target_figured_bass

    # Convert target to find what we're tonicizing
    target_degree = ROMAN_DEGREE_MAP.get(clean_target)
    if target_degree is None:
        alt_case = clean_target.swapcase()
        target_degree = ROMAN_DEGREE_MAP.get(alt_case)
        if target_degree is None:
            raise ValueError(f"Unknown target Roman numeral: {clean_target}")

    # Calculate target chord root
    key_pitch = NOTE_TO_PITCH_CLASS[key_root]
    target_root_pitch = (key_pitch + target_degree) % 12

    # Secondary dominant is perfect fifth above target (7 semitones)
    dominant_root_pitch = (target_root_pitch + 7) % 12
    dominant_root = PITCH_CLASS_NAMES[dominant_root_pitch]

    # Add seventh if explicitly specified (V7/ii) or if inversion requires it
    if "7" in base_dominant:
        seventh = "7"
    elif inversion in ["42", "43"]:  # Third inversion only exists for seventh chords
        seventh = "7"
    else:
        seventh = ""

    # Build chord symbol
    chord_symbol = f"{dominant_root}{seventh}"

    # Add inversion if present
    if inversion:
        bass_note = _calculate_bass_note(
            dominant_root, "", inversion, key_root
        )  # Major chord quality for dominants
        if bass_note:
            chord_symbol += f"/{bass_note}"

    return chord_symbol


def _clean_roman_for_lookup(roman: str) -> str:
    """Clean Roman numeral for lookup in degree map."""
    # Remove common modifiers but keep case and accidentals
    cleaned = re.sub(r"[°+o\(\)]", "", roman)
    return cleaned


def _get_chord_quality(roman: str, key_mode: str) -> str:
    """Determine chord quality from Roman numeral."""
    # Check for explicit quality markers
    if "°" in roman or "o" in roman or "dim" in roman.lower():
        return "dim"
    if "+" in roman or "aug" in roman.lower():
        return "+"
    if "M" in roman:
        return ""  # Major

    # Remove accidentals to get the core Roman numeral for quality determination
    core_roman = re.sub(r"^[b#]+", "", roman)  # Remove leading accidentals

    # Use case of the core Roman numeral to determine quality
    if core_roman.isupper():
        return ""  # Major
    elif core_roman.islower():
        return "m"  # Minor
    else:
        # Mixed case - check first character of core roman
        return "m" if core_roman and core_roman[0].islower() else ""


def _calculate_bass_note(
    root: str, quality: str, inversion: str, key_root: Optional[str] = None
) -> Optional[str]:
    """Calculate bass note for chord inversions."""
    root_pitch = NOTE_TO_PITCH_CLASS[root]

    def _get_enharmonic_for_key(note_name: str, key_root: str) -> str:
        """Choose appropriate enharmonic based on key signature."""
        if key_root and note_name in ENHARMONIC_FLATS:
            # Use flats for flat keys (F, Bb, Eb, Ab, Db, Gb, Cb)
            flat_keys = ["F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"]
            if key_root in flat_keys:
                return ENHARMONIC_FLATS[note_name]
        return note_name

    if inversion == "6":  # First inversion
        # Bass is third of chord
        third_interval = 3 if quality == "m" else 4
        bass_pitch = (root_pitch + third_interval) % 12
        bass_note = PITCH_CLASS_NAMES[bass_pitch]
        return _get_enharmonic_for_key(bass_note, key_root or "C")
    elif inversion == "64":  # Second inversion
        # Bass is fifth of chord
        bass_pitch = (root_pitch + 7) % 12
        bass_note = PITCH_CLASS_NAMES[bass_pitch]
        return _get_enharmonic_for_key(bass_note, key_root or "C")
    elif inversion == "43":  # Second inversion of seventh chord (4/3)
        # Bass is fifth of chord
        bass_pitch = (root_pitch + 7) % 12
        bass_note = PITCH_CLASS_NAMES[bass_pitch]
        return _get_enharmonic_for_key(bass_note, key_root or "C")
    elif inversion == "42":  # Third inversion of seventh chord (4/2)
        # Bass is seventh of chord
        bass_pitch = (root_pitch + 10) % 12  # Minor seventh
        bass_note = PITCH_CLASS_NAMES[bass_pitch]
        return _get_enharmonic_for_key(bass_note, key_root or "C")

    return None


def is_roman_numeral_progression(progression: str) -> bool:
    """
    Detect if a progression contains Roman numerals vs chord symbols.

    Args:
        progression: Input string to check

    Returns:
        True if contains Roman numerals, False if chord symbols

    Examples:
        >>> is_roman_numeral_progression("V/ii ii V I")
        True
        >>> is_roman_numeral_progression("C Am F G")
        False
    """
    tokens = progression.strip().split()
    if not tokens:
        return False

    roman_indicators = 0
    chord_symbol_indicators = 0

    for token in tokens:
        # Check for Roman numeral patterns
        if re.match(r"^[ivxIVX]+", token):
            roman_indicators += 1
        elif re.match(r"^[bv#]+[ivxIVX]+", token):  # Accidental + roman
            roman_indicators += 1
        elif "/" in token and re.search(r"[ivxIVX]", token):  # Secondary dominants
            roman_indicators += 1
        # Check for chord symbol patterns
        elif re.match(r"^[A-G][#b]?", token):  # Starts with note name
            chord_symbol_indicators += 1

    # Return True if more Roman numeral indicators than chord symbols
    return roman_indicators > chord_symbol_indicators
