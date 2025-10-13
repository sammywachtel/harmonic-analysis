"""
Key signature interpretation and conversion logic.

Converts between key signatures (sharps/flats) and key names (major/minor).
Handles both directions:
- Key signature (e.g., 2 sharps) → Key name (e.g., "D major" or "B minor")
- Key hint string (e.g., "D major") → Key signature (e.g., 2 sharps)

Useful for interpreting uploaded MIDI/MusicXML files where key signatures
may be ambiguous between major and relative minor keys.
"""


def convert_key_signature_to_mode(
    key_signature_sharps_flats: int, prefer_minor: bool = False
) -> str:
    """
    Convert a key signature (number of sharps/flats) to a specific major or minor key.

    Args:
        key_signature_sharps_flats: Number of sharps (positive) or flats (negative)
        prefer_minor: If True, return relative minor; if False, return major

    Returns:
        Key name like "D major" or "B minor"

    Examples:
        convert_key_signature_to_mode(2, False) -> "D major"
        convert_key_signature_to_mode(2, True) -> "B minor"
        convert_key_signature_to_mode(-2, False) -> "Bb major"
        convert_key_signature_to_mode(-2, True) -> "G minor"
    """
    # Major keys by sharps/flats
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

    if key_signature_sharps_flats not in major_keys:
        # Unknown key signature, default to C major or A minor
        return "A minor" if prefer_minor else "C major"

    if prefer_minor:
        return f"{minor_keys[key_signature_sharps_flats]} minor"
    else:
        return f"{major_keys[key_signature_sharps_flats]} major"


def parse_key_signature_from_hint(key_hint: str) -> int:
    """
    Parse a key hint string to extract number of sharps/flats.

    Args:
        key_hint: String like "D major", "B minor", "2 sharps", etc.

    Returns:
        Number of sharps (positive) or flats (negative)
    """
    if not key_hint:
        return 0

    key_hint_lower = key_hint.lower()

    # Check for explicit sharp/flat count
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

    # Map key names to sharps/flats (major keys)
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

    # Extract key name
    for key_name in major_key_map.keys():
        if key_name in key_hint_lower and "major" in key_hint_lower:
            return major_key_map[key_name]

    for key_name in minor_key_map.keys():
        if key_name in key_hint_lower and "minor" in key_hint_lower:
            return minor_key_map[key_name]

    # Default: no sharps or flats
    return 0
