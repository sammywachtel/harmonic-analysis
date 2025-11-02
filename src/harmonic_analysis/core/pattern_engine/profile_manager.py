"""
Profile management for multi-style harmonic analysis.

This module provides the ProfileManager class which loads and manages analysis profiles
(jazz, classical, pop, modal) from JSON configuration. Each profile defines substitution
rules and typicality weights for pattern matching.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Profile:
    """
    Configuration for a harmonic analysis style profile.

    Each profile defines how patterns should be matched and weighted for a particular
    musical style (e.g., jazz, classical, pop, modal).

    Attributes:
        name: Internal identifier (e.g., "jazz", "classical")
        display_name: Human-readable name (e.g., "Jazz", "Classical")
        enabled: Whether this profile is active for analysis
        substitutions: Roman numeral substitutions allowed in this style
                      (e.g., {"V": ["♭II7", "V7", "V9"]} allows tritone sub)
        typicality_weights: Pattern ID weights indicating how typical a
                           pattern is for this style (0.0-1.0).
                           Supports wildcards (e.g., "modal.*")
    """

    name: str
    display_name: str
    enabled: bool = True
    substitutions: Dict[str, List[str]] = field(default_factory=dict)
    typicality_weights: Dict[str, float] = field(default_factory=dict)

    def get_typicality_weight(self, pattern_id: str) -> float:
        """
        Get the typicality weight for a pattern in this style.

        Supports exact matches and wildcard patterns (e.g., "modal.*" matches
        "modal.dorian_vamp", "modal.mixolydian_cadence", etc.).

        Args:
            pattern_id: The pattern identifier (e.g., "functional.jazz_iiviV")

        Returns:
            Weight from 0.0 to 1.0 indicating how typical this pattern is for the style.
            Returns 0.5 if no match found (neutral typicality).
        """
        # First, check for exact match
        if pattern_id in self.typicality_weights:
            return self.typicality_weights[pattern_id]

        # Then check for wildcard matches
        for weight_pattern, weight_value in self.typicality_weights.items():
            # Support wildcard at the end (e.g., "modal.*")
            if weight_pattern.endswith(".*"):
                prefix = weight_pattern[:-2]  # Remove ".*"
                if pattern_id.startswith(prefix + "."):
                    return weight_value

        # Default to neutral weight if no match
        return 0.5

    def get_substitutes(self, roman_numeral: str) -> List[str]:
        """
        Get allowed substitutions for a roman numeral in this style.

        Args:
            roman_numeral: The roman numeral to get substitutions for (e.g., "V", "ii")

        Returns:
            List of allowed substitutions, or empty list if none defined
        """
        return self.substitutions.get(roman_numeral, [])


class ProfileManager:
    """
    Loads and manages harmonic analysis style profiles.

    This class is responsible for:
    - Loading profiles from profiles.json
    - Validating profile schema
    - Providing access to enabled profiles
    - Looking up substitutions and typicality weights
    """

    def __init__(self, profiles_path: Optional[Path] = None):
        """
        Initialize the ProfileManager.

        Args:
            profiles_path: Path to profiles.json. If None, uses default location
                          (resources/patterns/ directory).
        """
        if profiles_path is None:
            profiles_path = (
                Path(__file__).parent.parent.parent
                / "resources"
                / "patterns"
                / "profiles.json"
            )

        self.profiles_path = profiles_path
        self._profiles: List[Profile] = []
        self._load_profiles()

    def _load_profiles(self) -> None:
        """
        Load profiles from JSON file.

        Raises:
            FileNotFoundError: If profiles.json doesn't exist
            ValueError: If JSON is invalid or schema validation fails
        """
        if not self.profiles_path.exists():
            raise FileNotFoundError(f"Profiles file not found: {self.profiles_path}")

        try:
            with open(self.profiles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in profiles file: {e}") from e

        # Validate top-level structure
        if not isinstance(data, dict):
            raise ValueError("Profiles file must contain a JSON object")

        if "profiles" not in data:
            raise ValueError("Profiles file must contain a 'profiles' array")

        if not isinstance(data["profiles"], list):
            raise ValueError("'profiles' must be an array")

        # Load and validate each profile
        self._profiles = []
        for idx, profile_data in enumerate(data["profiles"]):
            try:
                profile = self._validate_and_create_profile(profile_data)
                self._profiles.append(profile)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid profile at index {idx}: {e}") from e

    def _validate_and_create_profile(self, data: dict) -> Profile:
        """
        Validate profile data and create a Profile instance.

        Args:
            data: Profile data dictionary from JSON

        Returns:
            Validated Profile instance

        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If field types are incorrect
        """
        # Validate required fields
        if "name" not in data:
            raise ValueError("Profile missing required field: name")
        if "display_name" not in data:
            raise ValueError("Profile missing required field: display_name")

        # Validate field types
        if not isinstance(data["name"], str):
            raise TypeError("Profile 'name' must be a string")
        if not isinstance(data["display_name"], str):
            raise TypeError("Profile 'display_name' must be a string")

        # Optional fields with defaults
        enabled = data.get("enabled", True)
        if not isinstance(enabled, bool):
            raise TypeError("Profile 'enabled' must be a boolean")

        substitutions = data.get("substitutions", {})
        if not isinstance(substitutions, dict):
            raise TypeError("Profile 'substitutions' must be an object")

        # Validate substitutions structure
        for key, value in substitutions.items():
            if not isinstance(key, str):
                raise TypeError(f"Substitution key '{key}' must be a string")
            if not isinstance(value, list):
                raise TypeError(f"Substitution value for '{key}' must be an array")
            if not all(isinstance(v, str) for v in value):
                raise TypeError(f"All substitution values for '{key}' must be strings")

        typicality_weights = data.get("typicality_weights", {})
        if not isinstance(typicality_weights, dict):
            raise TypeError("Profile 'typicality_weights' must be an object")

        # Validate typicality weights structure
        for key, value in typicality_weights.items():
            if not isinstance(key, str):
                raise TypeError(f"Typicality weight key '{key}' must be a string")
            if not isinstance(value, (int, float)):
                raise TypeError(f"Typicality weight value for '{key}' must be a number")
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"Typicality weight for '{key}' must be "
                    f"between 0.0 and 1.0, got {value}"
                )

        return Profile(
            name=data["name"],
            display_name=data["display_name"],
            enabled=enabled,
            substitutions=substitutions,
            typicality_weights=typicality_weights,
        )

    def get_enabled_profiles(self) -> List[Profile]:
        """
        Get all enabled profiles.

        Returns:
            List of enabled Profile instances
        """
        return [p for p in self._profiles if p.enabled]

    def get_profile(self, name: str) -> Optional[Profile]:
        """
        Get a specific profile by name.

        Args:
            name: Profile name (e.g., "jazz", "classical")

        Returns:
            Profile instance if found, None otherwise
        """
        for profile in self._profiles:
            if profile.name == name:
                return profile
        return None

    def get_profile_names(self) -> List[str]:
        """
        Get names of all loaded profiles.

        Returns:
            List of profile names
        """
        return [p.name for p in self._profiles]

    def get_enabled_profile_names(self) -> List[str]:
        """
        Get names of all enabled profiles.

        Returns:
            List of enabled profile names
        """
        return [p.name for p in self._profiles if p.enabled]
