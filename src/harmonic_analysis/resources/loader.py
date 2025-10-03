"""
Resource loading utilities using importlib.resources for reliable packaging.

This module provides functions to load JSON and other resource files
included with the harmonic_analysis package, ensuring they work correctly
when the package is installed via pip, built as a wheel, or run from source.
"""

import json
from pathlib import Path
from typing import Any, Dict

try:
    # Python 3.9+
    from importlib import resources as resources_module
except ImportError:
    # Python 3.8 fallback
    import importlib_resources as resources_module  # type: ignore[import-not-found,no-redef]  # noqa: E501


def load_json(name: str) -> Dict[str, Any]:
    """
    Load a JSON resource file from the resources package.

    Args:
        name: Name of the JSON file (e.g., "patterns.json", "glossary.json")

    Returns:
        Dictionary containing the parsed JSON data

    Raises:
        FileNotFoundError: If the resource file doesn't exist
        json.JSONDecodeError: If the file isn't valid JSON
    """
    try:
        with (
            resources_module.files("harmonic_analysis.resources")
            .joinpath(name)
            .open("r", encoding="utf-8") as f
        ):
            result: Dict[str, Any] = json.load(f)
            return result
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Resource file '{name}' not found in harmonic_analysis.resources"
        )
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in resource file '{name}': {e}", e.doc, e.pos
        )


def get_resource_path(name: str) -> Path:
    """
    Get the filesystem path to a resource file.

    Args:
        name: Name of the resource file

    Returns:
        Path to the resource file

    Note:
        This should be used sparingly, as it may not work with all packaging methods.
        Prefer load_json() for JSON files.
    """
    traversable = resources_module.files("harmonic_analysis.resources").joinpath(name)
    # Convert to Path if possible for better type compatibility
    if hasattr(traversable, "__fspath__"):
        return Path(str(traversable))  # Force conversion to string first
    # Fallback for cases where conversion isn't possible
    return Path(str(traversable))


def load_patterns() -> Dict[str, Any]:
    """Load the harmonic patterns library."""
    return load_json("patterns.json")


def load_glossary() -> Dict[str, Any]:
    """Load the music theory glossary."""
    return load_json("glossary.json")
