"""
Unit tests for ProfileManager and Profile classes.

Tests cover:
- Profile loading and validation
- Schema validation (required fields, types)
- Substitution lookups
- Typicality weight lookups with wildcard support
- Error handling for invalid profiles
"""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from harmonic_analysis.core.pattern_engine.profile_manager import (
    Profile,
    ProfileManager,
)


class TestProfile:
    """Test the Profile dataclass."""

    def test_profile_creation_minimal(self):
        """Profile can be created with just name and display_name."""
        profile = Profile(name="test", display_name="Test Profile")

        assert profile.name == "test"
        assert profile.display_name == "Test Profile"
        assert profile.enabled is True
        assert profile.substitutions == {}
        assert profile.typicality_weights == {}

    def test_profile_creation_full(self):
        """Profile can be created with all fields."""
        profile = Profile(
            name="jazz",
            display_name="Jazz",
            enabled=True,
            substitutions={"V": ["♭II7", "V7"], "ii": ["♭II7"]},
            typicality_weights={"functional.jazz_iiviV": 0.95, "modal.*": 0.30},
        )

        assert profile.name == "jazz"
        assert profile.display_name == "Jazz"
        assert profile.enabled is True
        assert profile.substitutions == {"V": ["♭II7", "V7"], "ii": ["♭II7"]}
        assert profile.typicality_weights == {
            "functional.jazz_iiviV": 0.95,
            "modal.*": 0.30,
        }

    def test_profile_is_frozen(self):
        """Profile is immutable (frozen dataclass)."""
        profile = Profile(name="test", display_name="Test")

        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.11+
            profile.name = "modified"

    def test_get_typicality_weight_exact_match(self):
        """get_typicality_weight returns exact match weight."""
        profile = Profile(
            name="jazz",
            display_name="Jazz",
            typicality_weights={
                "functional.jazz_iiviV": 0.95,
                "cadence.turnaround": 0.90,
            },
        )

        assert profile.get_typicality_weight("functional.jazz_iiviV") == 0.95
        assert profile.get_typicality_weight("cadence.turnaround") == 0.90

    def test_get_typicality_weight_wildcard_match(self):
        """get_typicality_weight supports wildcard patterns."""
        profile = Profile(
            name="jazz",
            display_name="Jazz",
            typicality_weights={
                "modal.*": 0.30,
                "functional.*": 0.85,
            },
        )

        # Wildcard matches
        assert profile.get_typicality_weight("modal.dorian_vamp") == 0.30
        assert profile.get_typicality_weight("modal.mixolydian_cadence") == 0.30
        assert profile.get_typicality_weight("functional.circle_of_fifths") == 0.85

    def test_get_typicality_weight_exact_takes_precedence(self):
        """Exact matches take precedence over wildcard matches."""
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={
                "modal.*": 0.30,
                "modal.dorian_vamp": 0.95,  # Specific override
            },
        )

        # Exact match wins
        assert profile.get_typicality_weight("modal.dorian_vamp") == 0.95
        # Wildcard for others
        assert profile.get_typicality_weight("modal.mixolydian_cadence") == 0.30

    def test_get_typicality_weight_no_match_returns_default(self):
        """get_typicality_weight returns 0.5 for unknown patterns."""
        profile = Profile(
            name="test",
            display_name="Test",
            typicality_weights={"known.pattern": 0.80},
        )

        # Unknown pattern gets default weight
        assert profile.get_typicality_weight("unknown.pattern") == 0.5
        assert profile.get_typicality_weight("completely.different") == 0.5

    def test_get_substitutes_existing(self):
        """get_substitutes returns correct substitutions."""
        profile = Profile(
            name="jazz",
            display_name="Jazz",
            substitutions={"V": ["♭II7", "V7", "V9"], "ii": ["♭II7", "ii7"]},
        )

        assert profile.get_substitutes("V") == ["♭II7", "V7", "V9"]
        assert profile.get_substitutes("ii") == ["♭II7", "ii7"]

    def test_get_substitutes_missing_returns_empty(self):
        """get_substitutes returns empty list for undefined numeral."""
        profile = Profile(
            name="jazz",
            display_name="Jazz",
            substitutions={"V": ["♭II7"]},
        )

        assert profile.get_substitutes("IV") == []
        assert profile.get_substitutes("vi") == []


class TestProfileManager:
    """Test the ProfileManager class."""

    def test_loads_default_profiles(self):
        """ProfileManager loads profiles from default location."""
        manager = ProfileManager()

        profiles = manager.get_enabled_profiles()
        assert len(profiles) >= 4  # jazz, classical, pop, modal

        names = [p.name for p in profiles]
        assert "jazz" in names
        assert "classical" in names
        assert "pop" in names
        assert "modal" in names

    def test_get_profile_by_name(self):
        """get_profile returns correct profile by name."""
        manager = ProfileManager()

        jazz = manager.get_profile("jazz")
        assert jazz is not None
        assert jazz.name == "jazz"
        assert jazz.display_name == "Jazz"

        classical = manager.get_profile("classical")
        assert classical is not None
        assert classical.name == "classical"

    def test_get_profile_missing_returns_none(self):
        """get_profile returns None for unknown profile."""
        manager = ProfileManager()

        assert manager.get_profile("nonexistent") is None
        assert manager.get_profile("xyz") is None

    def test_get_profile_names(self):
        """get_profile_names returns all profile names."""
        manager = ProfileManager()

        names = manager.get_profile_names()
        assert "jazz" in names
        assert "classical" in names
        assert "pop" in names
        assert "modal" in names

    def test_get_enabled_profile_names(self):
        """get_enabled_profile_names returns only enabled profiles."""
        manager = ProfileManager()

        enabled_names = manager.get_enabled_profile_names()
        assert "jazz" in enabled_names
        assert "classical" in enabled_names
        # Should only include enabled profiles
        assert all(manager.get_profile(name).enabled for name in enabled_names)

    def test_jazz_profile_has_tritone_substitution(self):
        """Jazz profile includes tritone substitution (V → ♭II7)."""
        manager = ProfileManager()
        jazz = manager.get_profile("jazz")

        assert jazz is not None
        v_subs = jazz.get_substitutes("V")
        assert "♭II7" in v_subs  # Tritone substitution

    def test_classical_profile_has_predominant_substitution(self):
        """Classical profile includes predominant substitution (IV → ii6)."""
        manager = ProfileManager()
        classical = manager.get_profile("classical")

        assert classical is not None
        iv_subs = classical.get_substitutes("IV")
        assert "ii6" in iv_subs

    def test_pop_profile_has_subdominant_substitutions(self):
        """Pop profile includes subdominant substitutions."""
        manager = ProfileManager()
        pop = manager.get_profile("pop")

        assert pop is not None
        iv_subs = pop.get_substitutes("IV")
        assert "ii" in iv_subs or "ii6" in iv_subs or "IV6" in iv_subs

    def test_modal_profile_has_mixolydian_substitution(self):
        """Modal profile includes Mixolydian substitution (bVII → V)."""
        manager = ProfileManager()
        modal = manager.get_profile("modal")

        assert modal is not None
        bvii_subs = modal.get_substitutes("bVII")
        assert "V" in bvii_subs

    def test_typicality_weights_wildcard_support(self):
        """Profile typicality weights support wildcard matching."""
        manager = ProfileManager()
        modal = manager.get_profile("modal")

        assert modal is not None
        # Modal.* patterns should have high weight in modal profile
        dorian_weight = modal.get_typicality_weight("modal.dorian_vamp")
        assert dorian_weight >= 0.85  # Should be high for modal profile

    def test_loads_from_custom_path(self):
        """ProfileManager can load from custom path."""
        # Create temporary profiles file
        profiles_data = {
            "profiles": [
                {
                    "name": "custom",
                    "display_name": "Custom Profile",
                    "enabled": True,
                    "substitutions": {},
                    "typicality_weights": {},
                }
            ]
        }

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(profiles_data, f)
            temp_path = Path(f.name)

        try:
            manager = ProfileManager(profiles_path=temp_path)
            profiles = manager.get_enabled_profiles()

            assert len(profiles) == 1
            assert profiles[0].name == "custom"
        finally:
            temp_path.unlink()

    def test_missing_file_raises_error(self):
        """ProfileManager raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            ProfileManager(profiles_path=Path("/nonexistent/path.json"))

    def test_invalid_json_raises_error(self):
        """ProfileManager raises ValueError for invalid JSON."""
        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                ProfileManager(profiles_path=temp_path)
        finally:
            temp_path.unlink()

    def test_missing_profiles_array_raises_error(self):
        """ProfileManager raises ValueError if 'profiles' array missing."""
        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"wrong_key": []}, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="'profiles' array"):
                ProfileManager(profiles_path=temp_path)
        finally:
            temp_path.unlink()

    def test_missing_required_field_raises_error(self):
        """ProfileManager raises ValueError if profile missing required field."""
        profiles_data = {
            "profiles": [
                {
                    "display_name": "Missing Name",  # Missing 'name' field
                    "enabled": True,
                }
            ]
        }

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(profiles_data, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="missing required field: name"):
                ProfileManager(profiles_path=temp_path)
        finally:
            temp_path.unlink()

    def test_invalid_field_type_raises_error(self):
        """ProfileManager raises ValueError for invalid field types."""
        profiles_data = {
            "profiles": [
                {
                    "name": 123,  # Should be string
                    "display_name": "Test",
                }
            ]
        }

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(profiles_data, f)
            temp_path = Path(f.name)

        try:
            # ValueError wraps the TypeError from validation
            with pytest.raises(ValueError, match="Invalid profile"):
                ProfileManager(profiles_path=temp_path)
        finally:
            temp_path.unlink()

    def test_invalid_typicality_weight_range_raises_error(self):
        """ProfileManager raises ValueError for weights outside [0, 1]."""
        profiles_data = {
            "profiles": [
                {
                    "name": "test",
                    "display_name": "Test",
                    "typicality_weights": {"pattern.id": 1.5},  # Invalid: > 1.0
                }
            ]
        }

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(profiles_data, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="between 0.0 and 1.0"):
                ProfileManager(profiles_path=temp_path)
        finally:
            temp_path.unlink()

    def test_invalid_substitutions_type_raises_error(self):
        """ProfileManager raises ValueError for invalid substitutions structure."""
        profiles_data = {
            "profiles": [
                {
                    "name": "test",
                    "display_name": "Test",
                    "substitutions": {"V": "not_a_list"},  # Should be array
                }
            ]
        }

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(profiles_data, f)
            temp_path = Path(f.name)

        try:
            # ValueError wraps the TypeError from validation
            with pytest.raises(ValueError, match="Invalid profile"):
                ProfileManager(profiles_path=temp_path)
        finally:
            temp_path.unlink()


class TestProfileManagerIntegration:
    """Integration tests with real profiles.json."""

    def test_all_profiles_have_required_fields(self):
        """All loaded profiles have required fields."""
        manager = ProfileManager()

        for profile in manager.get_enabled_profiles():
            assert profile.name
            assert profile.display_name
            assert isinstance(profile.enabled, bool)
            assert isinstance(profile.substitutions, dict)
            assert isinstance(profile.typicality_weights, dict)

    def test_substitutions_are_valid_roman_numerals(self):
        """All substitutions use valid roman numeral format."""
        manager = ProfileManager()

        for profile in manager.get_enabled_profiles():
            for key, substitutes in profile.substitutions.items():
                # Key should be a roman numeral pattern (starts with roman or accidental)
                assert any(key.startswith(p) for p in ["I", "i", "V", "v", "♭", "b"])

                # All substitutes should be valid
                for sub in substitutes:
                    # Just check they're strings - full validation would be complex
                    assert isinstance(sub, str)
                    assert len(sub) > 0

    def test_typicality_weights_in_valid_range(self):
        """All typicality weights are in [0.0, 1.0] range."""
        manager = ProfileManager()

        for profile in manager.get_enabled_profiles():
            for pattern_id, weight in profile.typicality_weights.items():
                assert 0.0 <= weight <= 1.0, (
                    f"Profile {profile.name}, pattern {pattern_id}: "
                    f"weight {weight} out of range"
                )
