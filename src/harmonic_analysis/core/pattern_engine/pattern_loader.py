"""
Pattern loader for unified pattern engine.

This module loads and validates pattern configurations from JSON files,
ensuring they conform to the expected schema.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema


class PatternLoader:
    """Loads and validates pattern definitions from JSON files."""

    # Default schema for pattern validation
    DEFAULT_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["version", "patterns"],
        "properties": {
            "version": {"type": "integer", "minimum": 1},
            "patterns": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "id",
                        "name",
                        "scope",
                        "track",
                        "matchers",
                        "evidence",
                    ],
                    "properties": {
                        "id": {"type": "string", "pattern": "^[a-zA-Z0-9._-]+$"},
                        "name": {"type": "string"},
                        "scope": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["harmonic", "melodic", "scale"],
                            },
                            "minItems": 1,
                        },
                        "track": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["functional", "modal", "chromatic"],
                            },
                            "minItems": 1,
                        },
                        "matchers": {
                            "type": "object",
                            "properties": {
                                "chord_seq": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "roman_seq": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "interval_seq": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                },
                                "mode": {"type": "string"},
                                "transposition_invariant": {"type": "boolean"},
                                "constraints": {"type": "object"},
                                "window": {"type": "object"},
                            },
                        },
                        "evidence": {
                            "type": "object",
                            "required": ["weight"],
                            "properties": {
                                "weight": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                },
                                "features": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "confidence_fn": {"type": "string"},
                            },
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "priority": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "description": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }

    def __init__(self, schema_path: Optional[Path] = None) -> None:
        """
        Initialize pattern loader.

        Args:
            schema_path: Optional path to custom schema file
        """
        if schema_path and schema_path.exists():
            with schema_path.open("r", encoding="utf-8") as f:
                self.schema = json.load(f)
        else:
            # Try to load the full schema from the package
            try:
                schema_file = Path(__file__).parent / "schemas" / "patterns.schema.json"
                if schema_file.exists():
                    with schema_file.open("r", encoding="utf-8") as f:
                        self.schema = json.load(f)
                else:
                    self.schema = self.DEFAULT_SCHEMA
            except (FileNotFoundError, json.JSONDecodeError):
                self.schema = self.DEFAULT_SCHEMA

    def load(self, path: Path) -> Dict[str, Any]:
        """
        Load and validate a patterns JSON file.

        Args:
            path: Path to patterns.json file

        Returns:
            Validated pattern data

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
            jsonschema.ValidationError: If JSON doesn't match schema
        """
        if not path.exists():
            raise FileNotFoundError(f"Pattern file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.validate(data)
        return data  # type: ignore[no-any-return]

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Validate pattern data against schema.

        Args:
            data: Pattern data to validate

        Raises:
            ValueError: If validation fails (with helpful error message)
        """
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            # Create helpful error message with context
            path_str = (
                " -> ".join(str(p) for p in e.absolute_path)
                if e.absolute_path
                else "root"
            )
            error_msg = f"Schema validation failed at '{path_str}': {e.message}"

            # Add suggestions for common errors
            if "is not of type" in e.message:
                if isinstance(e.schema, dict):
                    error_msg += f"\nExpected type: {e.schema.get('type', 'unknown')}"
            elif "is not one of" in e.message:
                if isinstance(e.schema, dict):
                    error_msg += f"\nAllowed values: {e.schema.get('enum', [])}"
            elif "is a required property" in e.message:
                missing_prop = (
                    e.message.split("'")[1] if "'" in e.message else "unknown"
                )
                error_msg += f"\nMissing required field: {missing_prop}"

            raise ValueError(error_msg) from e

    def load_patterns(self, path: Path) -> List[Dict[str, Any]]:
        """
        Load just the patterns array from a file.

        Args:
            path: Path to patterns.json file

        Returns:
            List of pattern definitions
        """
        data = self.load(path)
        return data.get("patterns", [])  # type: ignore[no-any-return]

    def merge_patterns(self, *paths: Path) -> Dict[str, Any]:
        """
        Merge patterns from multiple files.

        Later files override patterns with same ID.

        Args:
            *paths: Paths to pattern files

        Returns:
            Merged pattern data
        """
        merged = {"version": 1, "patterns": []}
        seen_ids = set()
        all_patterns = []

        for path in paths:
            data = self.load(path)
            # Use max version
            merged["version"] = max(merged["version"], data.get("version", 1))

            # Collect patterns, tracking IDs for deduplication
            for pattern in data.get("patterns", []):
                pattern_id = pattern.get("id")
                if pattern_id not in seen_ids:
                    all_patterns.append(pattern)
                    seen_ids.add(pattern_id)
                else:
                    # Replace existing pattern with same ID
                    for i, p in enumerate(all_patterns):
                        if p.get("id") == pattern_id:
                            all_patterns[i] = pattern
                            break

        merged["patterns"] = all_patterns
        self.validate(merged)
        return merged
