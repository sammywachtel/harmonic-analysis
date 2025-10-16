"""
Key signature interpretation and conversion logic.

Converts between key signatures (sharps/flats) and key names (major/minor).
Handles both directions:
- Key signature (e.g., 2 sharps) → Key name (e.g., "D major" or "B minor")
- Key hint string (e.g., "D major") → Key signature (e.g., 2 sharps)

Useful for interpreting uploaded MIDI/MusicXML files where key signatures
may be ambiguous between major and relative minor keys.

Ported from demo/lib/key_conversion.py to core library for library-wide use.
"""


def convert_key_signature_to_mode(
    key_signature_sharps_flats: int, prefer_minor: bool = False
) -> str:
    """
    Convert a key signature (number of sharps/flats) to a specific major or minor key.

    Opening move: Look up the key name from circle of fifths mapping.
    Each key signature corresponds to a major key and its relative minor
    (3 semitones below). The prefer_minor flag lets us choose which one.

    Args:
        key_signature_sharps_flats: Number of sharps (positive) or flats (negative)
            Range: -7 to +7
            Examples: 0 = C major/A minor
                      2 = D major/B minor
                     -2 = Bb major/G minor
        prefer_minor: If True, return relative minor; if False, return major

    Returns:
        Key name like "D major" or "B minor"

    Examples:
        >>> convert_key_signature_to_mode(2, False)
        'D major'
        >>> convert_key_signature_to_mode(2, True)
        'B minor'
        >>> convert_key_signature_to_mode(-2, False)
        'Bb major'
        >>> convert_key_signature_to_mode(-2, True)
        'G minor'
        >>> convert_key_signature_to_mode(0, False)
        'C major'
        >>> convert_key_signature_to_mode(0, True)
        'A minor'
    """
    # Main play: Major keys by sharps/flats (circle of fifths)
    # Flats: Cb (-7) → Gb → Db → Ab → Eb → Bb → F (-1)
    # Natural: C (0)
    # Sharps: G (+1) → D → A → E → B → F# → C# (+7)
    major_keys = {
        -7: "Cb",
        -6: "Gb",
        -5: "Db",
        -4: "Ab",
        -3: "Eb",
        -2: "Bb",
        -1: "F",
        0: "C",
        1: "G",
        2: "D",
        3: "A",
        4: "E",
        5: "B",
        6: "F#",
        7: "C#",
    }

    # Relative minor keys (3 semitones below major)
    # Each major key has a relative minor with the same key signature
    minor_keys = {
        -7: "Ab",
        -6: "Eb",
        -5: "Bb",
        -4: "F",
        -3: "C",
        -2: "G",
        -1: "D",
        0: "A",
        1: "E",
        2: "B",
        3: "F#",
        4: "C#",
        5: "G#",
        6: "D#",
        7: "A#",
    }

    # Safety check: fallback to C major or A minor for invalid input
    if key_signature_sharps_flats not in major_keys:
        # Unknown key signature, default to C major or A minor
        return "A minor" if prefer_minor else "C major"

    # Victory lap: return the requested key (major or minor)
    if prefer_minor:
        return f"{minor_keys[key_signature_sharps_flats]} minor"
    else:
        return f"{major_keys[key_signature_sharps_flats]} major"


def parse_key_signature_from_hint(key_hint: str) -> int:
    """
    Parse a key hint string to extract number of sharps/flats.

    Opening move: Check for explicit sharp/flat count first (e.g., "2 sharps").
    If not found, look for key name patterns (e.g., "D major", "B minor").

    Main play: Use comprehensive mappings of key names to their sharps/flats.
    Handles both major and minor keys with various input formats.

    Args:
        key_hint: String like "D major", "B minor", "2 sharps", "D", "d major"
            Case-insensitive, flexible format
            Examples: "D major", "D", "d", "Dmaj", "B minor", "2 sharps"

    Returns:
        Number of sharps (positive) or flats (negative)
        Range: -7 to +7
        Returns 0 for empty/invalid input (C major/A minor)

    Examples:
        >>> parse_key_signature_from_hint("D major")
        2
        >>> parse_key_signature_from_hint("B minor")
        2
        >>> parse_key_signature_from_hint("Bb major")
        -2
        >>> parse_key_signature_from_hint("2 sharps")
        2
        >>> parse_key_signature_from_hint("3 flats")
        -3
        >>> parse_key_signature_from_hint("")
        0
    """
    # Edge case: empty input
    if not key_hint:
        return 0

    key_hint_lower = key_hint.lower()

    # Opening move: Check for explicit sharp/flat count
    # Handles patterns like "2 sharps", "3 flats", "sharp 2", etc.
    if "sharp" in key_hint_lower:
        try:
            count = int("".join(filter(str.isdigit, key_hint)))
            return count
        except ValueError:
            pass
    elif "flat" in key_hint_lower:
        try:
            count = int("".join(filter(str.isdigit, key_hint)))
            return -count
        except ValueError:
            pass

    # Main play: Map key names to sharps/flats (major keys)
    # These mappings follow the circle of fifths
    major_key_map = {
        "c": 0,
        "g": 1,
        "d": 2,
        "a": 3,
        "e": 4,
        "b": 5,
        "f#": 6,
        "c#": 7,
        "f": -1,
        "bb": -2,
        "eb": -3,
        "ab": -4,
        "db": -5,
        "gb": -6,
        "cb": -7,
    }

    # Map key names to sharps/flats (minor keys - same as relative major)
    # A minor = 0 sharps (same as C major)
    # E minor = 1 sharp (same as G major)
    # B minor = 2 sharps (same as D major)
    minor_key_map = {
        "a": 0,
        "e": 1,
        "b": 2,
        "f#": 3,
        "c#": 4,
        "g#": 5,
        "d#": 6,
        "a#": 7,
        "d": -1,
        "g": -2,
        "c": -3,
        "f": -4,
        "bb": -5,
        "eb": -6,
        "ab": -7,
    }

    # Extract key name - check for major keys first
    # Sort by length descending to match longest keys first (e.g., "F#" before "F")
    sorted_major_keys = sorted(major_key_map.keys(), key=len, reverse=True)
    for key_name in sorted_major_keys:
        # Use word boundary matching to avoid partial matches
        # E.g., "a major" should match "a" not "ab"
        if "major" in key_hint_lower:
            # Check if the key name appears as a standalone token
            if key_hint_lower.startswith(key_name + " ") or key_hint_lower == key_name:
                return major_key_map[key_name]

    # Then check for minor keys
    sorted_minor_keys = sorted(minor_key_map.keys(), key=len, reverse=True)
    for key_name in sorted_minor_keys:
        if "minor" in key_hint_lower:
            # Check if the key name appears as a standalone token
            if key_hint_lower.startswith(key_name + " ") or key_hint_lower == key_name:
                return minor_key_map[key_name]

    # Victory lap: fallback to no sharps or flats (C major/A minor)
    return 0
