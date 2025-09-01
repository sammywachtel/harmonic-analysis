"""
Chord inversion analysis utilities.

Centralized implementation for detecting and labeling chord inversions
with figured bass notation. Used by both functional and modal analyzers.
"""

from typing import Dict, Optional, Union


def analyze_chord_inversion(
    root_pitch: Union[int, str, None],
    bass_pitch: Union[int, str, None],
    chord_name: str = "",
) -> Dict[str, Union[int, str]]:
    """
    Analyze chord inversion and generate figured bass notation.

    Args:
        root_pitch: Root note pitch class (0-11) or note name
        bass_pitch: Bass note pitch class (0-11) or note name
        chord_name: Optional chord name for seventh chord detection

    Returns:
        Dictionary with:
            - inversion: 0 (root), 1 (first), 2 (second), 3 (third)
            - figured_bass: Superscript notation ("", "⁶", "⁶⁴", "⁴²")
    """
    # Handle None or missing bass note (root position)
    if bass_pitch is None or bass_pitch == root_pitch:
        return {"inversion": 0, "figured_bass": ""}

    # Ensure we have numeric pitch classes
    if not isinstance(root_pitch, int) or not isinstance(bass_pitch, int):
        # If conversion needed, return default first inversion
        # (This shouldn't happen if the library is used correctly)
        return {"inversion": 1, "figured_bass": "⁶"}

    # Calculate interval from root to bass (in semitones)
    interval = (bass_pitch - root_pitch) % 12

    # Determine inversion type based on interval
    if interval in [3, 4]:  # Minor third or major third
        return {"inversion": 1, "figured_bass": "⁶"}
    elif interval == 7:  # Perfect fifth
        return {"inversion": 2, "figured_bass": "⁶⁴"}
    elif interval in [10, 11]:  # Minor seventh or major seventh
        # Check if this is actually a seventh chord
        if "7" in chord_name:
            return {"inversion": 3, "figured_bass": "⁴²"}
        else:
            # Might be an enharmonic fifth or other interval
            return {"inversion": 2, "figured_bass": "⁶⁴"}
    else:
        # Unknown interval, default to first inversion
        # This handles augmented/diminished intervals
        return {"inversion": 1, "figured_bass": "⁶"}


def get_bass_pitch_from_slash_chord(
    chord_symbol: str, note_to_pitch_class: Dict[str, int]
) -> Optional[int]:
    """
    Extract bass note pitch class from slash chord notation.

    Args:
        chord_symbol: Chord symbol potentially with slash notation (e.g., "D/A")
        note_to_pitch_class: Mapping of note names to pitch classes

    Returns:
        Bass note pitch class or None if no slash notation
    """
    if "/" not in chord_symbol:
        return None

    try:
        bass_note_name = chord_symbol.split("/")[1].strip()
        # Handle enharmonic spellings
        bass_note_name = bass_note_name.replace("♯", "#").replace("♭", "b")
        return note_to_pitch_class.get(bass_note_name)
    except (IndexError, AttributeError):
        return None
