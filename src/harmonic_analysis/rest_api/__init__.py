"""
REST API package for harmonic analysis.

Provides FastAPI-based REST endpoints for:
- Chord progression analysis
- Roman numeral analysis
- Melody analysis
- Scale analysis
- File upload (MusicXML/MIDI)
- Glossary lookups

Quick start:
    >>> from harmonic_analysis.rest_api.main import create_app
    >>> app = create_app()
    >>> # Run with: uvicorn harmonic_analysis.rest_api.main:app --reload
"""

from .main import app, create_app

__all__ = ["create_app", "app"]
