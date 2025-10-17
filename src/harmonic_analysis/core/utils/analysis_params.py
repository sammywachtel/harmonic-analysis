"""
Analysis parameter calculation utilities.

Provides functions for calculating appropriate analysis parameters based on
musical context, such as tempo-aware window sizing for chord detection.
"""


def calculate_initial_window(tempo_bpm: float) -> float:
    """
    Calculate initial analysis window size based on tempo.

    CRITICAL: Returns only musically sensible note values:
        - 0.5 QL = eighth note
        - 1.0 QL = quarter note
        - 2.0 QL = half note
        - 4.0 QL = whole note

    This ensures chord detection windows align with musical phrasing.
    Faster tempos use smaller windows (more frequent changes), while
    slower tempos use larger windows (sustained harmonies).

    Args:
        tempo_bpm: Tempo in beats per minute

    Returns:
        Window size quantized to musical note values

    Tempo guidelines:
        - Very fast (>140 BPM): 1.0 QL (quarter note) - Fast jazz, rapid changes
        - Fast (100-140 BPM): 2.0 QL (half note) - Pop, upbeat classical
        - Moderate (60-100 BPM): 2.0 QL (half note) - Ballads, most classical
        - Slow (<60 BPM): 4.0 QL (whole note) - Slow choral, very sustained

    Example:
        >>> window = calculate_initial_window(120)  # Fast tempo
        >>> print(f"Window size: {window} QL")
        Window size: 2.0 QL
    """
    if tempo_bpm > 140:
        window = 1.0
        category = "Very fast"
        note_name = "quarter note"
    elif tempo_bpm > 100:
        window = 2.0
        category = "Fast"
        note_name = "half note"
    elif tempo_bpm > 60:
        window = 2.0
        category = "Moderate"
        note_name = "half note"
    else:
        window = 4.0
        category = "Slow"
        note_name = "whole note"

    print(
        f"DEBUG: Tempo-based window calculation: {tempo_bpm} BPM → "
        f"{window} QL = {note_name} ({category})"
    )
    return window
