"""
Music21 integration module for harmonic-analysis library.

This module provides adapters and formatters for integrating with music21,
enabling file I/O (MusicXML, MIDI) and score annotation capabilities while
maintaining the library's lightweight internal representation.

Hybrid Architecture:
- Uses music21 only at I/O boundaries
- Converts to/from internal string-based representation
- Zero modifications to core analysis engine

Main Components:
- Music21Adapter: Parse music files → internal format
- Music21OutputFormatter: Analysis results → annotated scores
"""

from typing import TYPE_CHECKING

# Lazy imports to avoid requiring music21 unless actually used
if TYPE_CHECKING:
    from .music21_adapter import Music21Adapter

__all__ = ["Music21Adapter"]


def get_adapter():  # type: ignore[no-untyped-def]
    """Get Music21Adapter instance (lazy import)."""
    from .music21_adapter import Music21Adapter

    return Music21Adapter()


def get_formatter():  # type: ignore[no-untyped-def]
    """Get Music21OutputFormatter instance (lazy import)."""
    # Future implementation - placeholder for now
    raise NotImplementedError("Music21OutputFormatter not yet implemented")
