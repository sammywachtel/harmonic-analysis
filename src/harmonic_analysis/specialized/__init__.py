"""
Specialized modules for advanced music analysis.

This package contains specialized functionality for power users and specific use cases:
- MIDI integration and chord parsing
- Advanced algorithmic analysis
- Chromatic harmony analysis
- Music theory utilities

Most users should use the main API instead of importing from this package directly.
"""

# Specialized modules are not automatically imported to keep the main API clean
# Users must explicitly import: from harmonic_analysis.specialized import midi

__all__ = [
    "algorithms",
    "chromatic",
    "midi",
    "theory",
]
