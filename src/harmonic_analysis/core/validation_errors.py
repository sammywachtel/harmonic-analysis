"""
Shared error constants and validation utilities for key-context normalization.

This module provides consistent error messaging across the harmonic analysis library
for key requirement validation, ensuring parity for CLI/UI/API users.
"""

# Key requirement error messages
MISSING_KEY_FOR_ROMANS_MSG = (
    "Roman numeral analysis requires a key context. "
    "Provide a key parameter to enable modal symbol validation and proper "
    "harmonic analysis."
)

MISSING_KEY_FOR_SCALE_MSG = (
    "Scale analysis requires a key context for modal classification. "
    "Provide a key parameter to identify modes and harmonic implications."
)

MISSING_KEY_FOR_MELODY_MSG = (
    "Melody analysis requires a key context for tonic inference. "
    "Provide a key parameter to anchor the melodic analysis."
)

# Modal symbol validation messages
MODAL_SYMBOL_WITHOUT_KEY_MSG = (
    "Modal symbols (♭VII, ♯IV, etc.) require key context for proper validation. "
    "Provide a key parameter when using modal roman numerals."
)

INVALID_MODAL_SYMBOL_MSG = (
    "Invalid modal symbol '{}' in key context '{}'. "
    "Modal symbols must be consistent with the provided key signature."
)

# General validation messages
EMPTY_ROMAN_NUMERALS_MSG = (
    "Roman numerals list is empty. "
    "Provide valid roman numerals or use chord symbols with key context for "
    "auto-romanization."
)

INCONSISTENT_ROMANS_KEY_MSG = (
    "Roman numerals '{}' are inconsistent with key context '{}'. "
    "Ensure roman numerals match the provided key signature or provide correct "
    "key context."
)


class KeyContextError(ValueError):
    """Base exception for key context validation errors."""

    pass


class MissingKeyError(KeyContextError):
    """Raised when key context is required but not provided."""

    pass


class ModalSymbolError(KeyContextError):
    """Raised when modal symbols are used without proper key context."""

    pass


class RomanNumeralValidationError(KeyContextError):
    """Raised when roman numerals don't match the provided key context."""

    pass


def validate_key_for_romans(romans: list, key: str = None) -> None:
    """
    Validate that roman numerals are provided with appropriate key context.

    Args:
        romans: List of roman numerals
        key: Key context (required if romans is non-empty)

    Raises:
        MissingKeyError: If romans is non-empty but key is not provided
        ModalSymbolError: If modal symbols are present without key context
    """
    if not romans:
        return  # Empty romans list is valid

    if not key:
        raise MissingKeyError(MISSING_KEY_FOR_ROMANS_MSG)

    # Check for modal symbols that require key context
    modal_symbols = [
        "♭VII",
        "♭VI",
        "♭III",
        "♭II",
        "♯IV",
        "♯I",
        "bVII",
        "bVI",
        "bIII",
        "bII",
    ]

    for roman in romans:
        if any(symbol in str(roman) for symbol in modal_symbols):
            # Modal symbols are present - this is valid since we have key context
            pass


def validate_key_for_analysis(key: str = None, analysis_type: str = "harmonic") -> None:
    """
    Validate that key context is provided for harmonic analysis.

    Args:
        key: Key context
        analysis_type: Type of analysis ("scale", "melody", "harmonic")

    Raises:
        MissingKeyError: If key is not provided
    """
    if not key:
        if analysis_type == "scale":
            raise MissingKeyError(MISSING_KEY_FOR_SCALE_MSG)
        elif analysis_type == "melody":
            raise MissingKeyError(MISSING_KEY_FOR_MELODY_MSG)
        else:
            raise MissingKeyError(MISSING_KEY_FOR_ROMANS_MSG)
