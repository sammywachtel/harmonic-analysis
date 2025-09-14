"""
Resource loading package for harmonic analysis library.

This package provides reliable access to data files (patterns, glossary, etc.)
using importlib.resources for proper packaging support.
"""

from .loader import get_resource_path, load_glossary, load_json, load_patterns

__all__ = ["load_json", "load_patterns", "load_glossary", "get_resource_path"]
