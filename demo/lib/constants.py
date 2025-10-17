"""Shared constants for the harmonic analysis demo."""

import re
from typing import Dict

# ============================================================================
# Optional Dependency Hints
# ============================================================================

OPTIONAL_DEP_HINTS: Dict[str, str] = {
    "scipy": "Install SciPy (e.g. 'pip install scipy' or 'pip install -r requirements.txt').",
    "sklearn": "Install scikit-learn (e.g. 'pip install scikit-learn' or 'pip install -r requirements.txt').",
    "jsonschema": "Install jsonschema (e.g. 'pip install jsonschema' or 'pip install -r requirements.txt').",
}

# ============================================================================
# Analysis Profile Options
# ============================================================================

PROFILE_OPTIONS = [
    "classical",
    "jazz",
    "pop",
    "folk",
    "choral",
]

# ============================================================================
# Key Options
# ============================================================================

KEY_OPTION_NONE = "None"

KEY_OPTIONS = [
    KEY_OPTION_NONE,
    "C major",
    "G major",
    "D major",
    "A major",
    "E major",
    "B major",
    "F# major",
    "C# major",
    "F major",
    "Bb major",
    "Eb major",
    "Ab major",
    "Db major",
    "Gb major",
    "Cb major",
    "A minor",
    "E minor",
    "B minor",
    "F# minor",
    "C# minor",
    "G# minor",
    "D# minor",
    "A# minor",
    "D minor",
    "G minor",
    "C minor",
    "F minor",
    "Bb minor",
    "Eb minor",
    "Ab minor",
]

# ============================================================================
# Error Messages
# ============================================================================

MISSING_SCALE_KEY_MSG = "Scale analysis requires a key context."
MISSING_MELODY_KEY_MSG = "Melody analysis requires a key context."

# ============================================================================
# Validation Regex Patterns
# ============================================================================

# Roman numeral validation (library doesn't own these yet)
ROMAN_RE = re.compile(r"^[ivIV]+(?:[#b♯♭]?[ivIV]+)?(?:[°ø+]?)(?:\d+)?$")
NOTE_RE = re.compile(r"^[A-Ga-g](?:#|b)?(?:\d+)?$")

# ============================================================================
# Music Theory Constants
# ============================================================================

# Note names used for chord detection
NOTE_NAMES_FOR_DETECTION = [
    "C",
    "C#",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
]
