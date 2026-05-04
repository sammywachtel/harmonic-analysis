#!/usr/bin/env python3
"""
Multi-Profile API Integration Tests

Validates that the REST API correctly handles multi-profile harmonic analysis:
- Profile parameter validation (classical/jazz/pop/modal)
- Style-aware response fields (dominant_style, style_confidence, style_analysis)
- Profile discovery endpoint
- Backward compatibility (no profile parameter)

Tests the full request/response flow through the API layer.
"""

import pytest

# Try to import FastAPI dependencies - skip tests if not available
try:
    from fastapi.testclient import TestClient

    from demo.backend.rest_api.main import app
    from demo.backend.rest_api.models import ProfileResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    pytest.skip("FastAPI not installed (demo dependency)", allow_module_level=True)


# Setup: Create test client
@pytest.fixture
def client():
    """Create FastAPI test client for API integration tests."""
    return TestClient(app)


# -----------------------------
# Profile Discovery Tests (AC-4)
# -----------------------------


def test_get_profiles_endpoint_exists(client):
    """
    Opening move: Verify profile discovery endpoint returns 200.

    AC-4: GET /api/constants/profiles endpoint returns 4 available profiles
    """
    response = client.get("/api/constants/profiles")
    assert response.status_code == 200, f"Profile endpoint failed: {response.text}"


def test_get_profiles_returns_correct_structure(client):
    """
    Main play: Verify profile response has correct structure and content.

    AC-4: GET /api/constants/profiles endpoint returns 4 available profiles
    """
    response = client.get("/api/constants/profiles")
    data = response.json()

    # Verify top-level structure
    assert "profiles" in data, "Response missing 'profiles' field"
    assert isinstance(data["profiles"], list), "profiles should be a list"

    # Verify we have exactly 4 profiles
    profiles = data["profiles"]
    assert len(profiles) == 4, f"Expected 4 profiles, got {len(profiles)}"

    # Verify each profile has required fields
    profile_names = set()
    for profile in profiles:
        assert "name" in profile, "Profile missing 'name' field"
        assert "display_name" in profile, "Profile missing 'display_name' field"
        assert "description" in profile, "Profile missing 'description' field"
        assert "enabled" in profile, "Profile missing 'enabled' field"
        profile_names.add(profile["name"])

    # Verify all expected profiles are present
    expected_profiles = {"classical", "jazz", "pop", "modal"}
    assert (
        profile_names == expected_profiles
    ), f"Profile names mismatch. Expected {expected_profiles}, got {profile_names}"


def test_get_profiles_validates_against_pydantic_model(client):
    """
    Victory lap: Verify response can be deserialized into ProfileResponse model.

    AC-4: GET /api/constants/profiles endpoint returns 4 available profiles
    """
    response = client.get("/api/constants/profiles")
    data = response.json()

    # Pydantic validation should pass
    try:
        profile_response = ProfileResponse(**data)
        assert len(profile_response.profiles) == 4
    except Exception as e:
        pytest.fail(f"ProfileResponse validation failed: {e}")


# -----------------------------
# Profile Parameter Tests (AC-1, AC-5)
# -----------------------------


@pytest.mark.parametrize(
    "profile",
    ["classical", "jazz", "pop", "modal"],
)
def test_analyze_accepts_valid_profile(client, profile):
    """
    Big play: Verify API accepts all valid profile values.

    AC-1: API accepts optional profile parameter with validation
    AC-5: Integration test validates multi-profile API request/response flow
    """
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "profile": profile,
            "include_educational": False,
        },
    )

    assert response.status_code == 200, f"Profile '{profile}' rejected: {response.text}"

    # Verify response is valid JSON with expected structure
    data = response.json()
    assert "analysis" in data, "Response missing 'analysis' field"
    assert "summary" in data, "Response missing 'summary' field"


def test_analyze_rejects_invalid_profile(client):
    """
    Defensive check: Verify API rejects invalid profile values.

    AC-1: API accepts optional profile parameter with validation
    """
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "profile": "invalid_profile",
            "include_educational": False,
        },
    )

    # Should return 422 Unprocessable Entity for validation error
    assert (
        response.status_code == 422
    ), f"Invalid profile should fail validation, got {response.status_code}"


def test_analyze_profile_defaults_to_classical(client):
    """
    Verify profile defaults to 'classical' when not provided.

    AC-1: API accepts optional profile parameter with validation
    AC-7: Backward compatibility test verifies old API requests work unchanged
    """
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "include_educational": False,
        },
    )

    assert (
        response.status_code == 200
    ), f"Request without profile failed: {response.text}"

    # The analysis should succeed (implicitly using classical profile)
    data = response.json()
    assert "analysis" in data, "Response missing 'analysis' field"


# -----------------------------
# Style-Aware Response Tests (AC-2, AC-3)
# -----------------------------


def test_analyze_response_structure(client):
    """
    Check baseline: Verify response has expected top-level structure.

    AC-2: Response includes style-aware fields
    """
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "profile": "classical",
            "include_educational": False,
        },
    )

    data = response.json()

    # Core response fields
    assert "summary" in data, "Response missing 'summary' field"
    assert "analysis" in data, "Response missing 'analysis' field"

    # Analysis envelope structure
    analysis = data["analysis"]
    assert "primary" in analysis, "Analysis missing 'primary' field"
    assert "alternatives" in analysis, "Analysis missing 'alternatives' field"
    assert "chord_symbols" in analysis, "Analysis missing 'chord_symbols' field"


def test_analyze_response_includes_style_fields(client):
    """
    Main validation: Verify response includes style-aware fields.

    AC-2: Response includes style-aware fields (dominant_style, style_confidence, style_analysis)

    NOTE: Until Epic 1 Fix completes, these fields may be null/None.
    We're validating the API contract exists, not that values are populated.
    """
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["Dm7", "G7", "Cmaj7", "Cmaj7"],
            "profile": "jazz",
            "include_educational": False,
        },
    )

    data = response.json()
    analysis = data["analysis"]
    primary = analysis["primary"]

    # Verify style-aware fields exist in response structure
    # These fields are defined as Optional in DTO, so they may be null
    assert (
        "dominant_style" in primary
    ), "Primary analysis missing 'dominant_style' field"
    assert (
        "style_confidence" in primary
    ), "Primary analysis missing 'style_confidence' field"
    assert (
        "style_analysis" in primary
    ), "Primary analysis missing 'style_analysis' field"

    # Type validation when values are present
    if primary["dominant_style"] is not None:
        assert isinstance(
            primary["dominant_style"], str
        ), "dominant_style should be string"

    if primary["style_confidence"] is not None:
        assert isinstance(
            primary["style_confidence"], dict
        ), "style_confidence should be dict"
        # Validate it's Dict[str, float]
        for key, value in primary["style_confidence"].items():
            assert isinstance(
                key, str
            ), f"style_confidence key '{key}' should be string"
            assert isinstance(
                value, (int, float)
            ), f"style_confidence value for '{key}' should be numeric"

    if primary["style_analysis"] is not None:
        assert isinstance(
            primary["style_analysis"], dict
        ), "style_analysis should be dict"


def test_analyze_style_analysis_nested_structure(client):
    """
    Deep dive: Verify style_analysis dict contains valid StyleAnalysisDetail objects.

    AC-3: Dict[str, StyleAnalysisDetail] serializes correctly to nested JSON

    NOTE: Until Epic 1 Fix completes, style_analysis may be null.
    This test validates serialization structure when present.
    """
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G7", "C"],
            "profile": "jazz",
            "include_educational": False,
        },
    )

    data = response.json()
    primary = data["analysis"]["primary"]

    # If style_analysis is populated, validate its nested structure
    if primary["style_analysis"] is not None:
        style_analysis = primary["style_analysis"]

        # Should be a dictionary with profile names as keys
        assert isinstance(style_analysis, dict), "style_analysis should be a dictionary"

        # Validate each StyleAnalysisDetail object
        for profile_name, detail in style_analysis.items():
            assert isinstance(
                profile_name, str
            ), f"Profile key '{profile_name}' should be string"
            assert isinstance(
                detail, dict
            ), f"StyleAnalysisDetail for '{profile_name}' should be dict"

            # Validate StyleAnalysisDetail required fields
            assert (
                "style_name" in detail
            ), f"StyleAnalysisDetail missing 'style_name' for {profile_name}"
            assert (
                "confidence" in detail
            ), f"StyleAnalysisDetail missing 'confidence' for {profile_name}"
            assert (
                "patterns" in detail
            ), f"StyleAnalysisDetail missing 'patterns' for {profile_name}"
            assert (
                "roman_numerals" in detail
            ), f"StyleAnalysisDetail missing 'roman_numerals' for {profile_name}"

            # Type validation
            assert isinstance(detail["style_name"], str)
            assert isinstance(detail["confidence"], (int, float))
            assert isinstance(detail["patterns"], list)
            assert isinstance(detail["roman_numerals"], list)


# -----------------------------
# Backward Compatibility Tests (AC-7)
# -----------------------------


def test_backward_compatibility_no_profile_parameter(client):
    """
    Regression guard: Verify old API requests (without profile) still work.

    AC-7: Backward compatibility test verifies old API requests (no profile) work unchanged
    """
    # Old-style request without profile parameter
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "Am", "F", "G"],
            "include_educational": False,
        },
    )

    assert (
        response.status_code == 200
    ), f"Backward compatibility broken: {response.text}"

    # Verify response structure is unchanged
    data = response.json()
    assert "summary" in data
    assert "analysis" in data
    analysis = data["analysis"]
    assert "primary" in analysis
    assert "roman_numerals" in analysis["primary"]
    assert "confidence" in analysis["primary"]


def test_backward_compatibility_response_fields_optional(client):
    """
    Ensure new fields are optional and don't break old clients.

    AC-7: Backward compatibility test verifies old API requests (no profile) work unchanged
    """
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "include_educational": False,
        },
    )

    data = response.json()
    primary = data["analysis"]["primary"]

    # New fields should exist but may be null (backward compatible)
    assert "dominant_style" in primary
    assert "style_confidence" in primary
    assert "style_analysis" in primary

    # Old core fields must still be present
    assert "type" in primary
    assert "roman_numerals" in primary
    assert "confidence" in primary
    assert "key_signature" in primary


# -----------------------------
# Cross-Profile Validation (AC-5)
# -----------------------------


def test_different_profiles_may_yield_different_results(client):
    """
    Spot check: Verify different profiles can produce different analyses.

    AC-5: Integration test validates multi-profile API request/response flow

    NOTE: Until Epic 1 Fix completes, all profiles may return identical results.
    This is expected behavior during API contract validation phase.
    """
    progression = ["Dm7", "G7", "Cmaj7", "A7"]

    # Analyze with jazz profile
    jazz_response = client.post(
        "/api/analyze",
        json={"chords": progression, "profile": "jazz", "include_educational": False},
    )
    jazz_data = jazz_response.json()

    # Analyze with classical profile
    classical_response = client.post(
        "/api/analyze",
        json={
            "chords": progression,
            "profile": "classical",
            "include_educational": False,
        },
    )
    classical_data = classical_response.json()

    # Both should succeed
    assert jazz_response.status_code == 200
    assert classical_response.status_code == 200

    # Both should have valid analysis structures
    assert "analysis" in jazz_data
    assert "analysis" in classical_data

    # Note: We're NOT asserting different results here because Epic 1 Fix
    # hasn't completed yet. Just validate both profiles work.


def test_analyze_with_romans_input_and_profile(client):
    """
    Edge case: Verify profile parameter works with roman numeral input.

    AC-1: API accepts optional profile parameter with validation
    """
    response = client.post(
        "/api/analyze",
        json={
            "romans": ["I", "IV", "V", "I"],
            "key": "C major",
            "profile": "classical",
            "include_educational": False,
        },
    )

    assert (
        response.status_code == 200
    ), f"Roman numeral analysis with profile failed: {response.text}"

    data = response.json()
    assert "analysis" in data


def test_analyze_with_melody_input_and_profile(client):
    """
    Edge case: Verify profile parameter works with melody input.

    AC-1: API accepts optional profile parameter with validation
    """
    response = client.post(
        "/api/analyze",
        json={
            "melody": ["C", "D", "E", "F", "G"],
            "key": "C major",
            "profile": "modal",
            "include_educational": False,
        },
    )

    assert (
        response.status_code == 200
    ), f"Melody analysis with profile failed: {response.text}"

    data = response.json()
    assert "analysis" in data


# -----------------------------
# Error Handling Tests
# -----------------------------


def test_analyze_missing_input_returns_400(client):
    """
    Defensive check: Verify API returns 400 for requests with no input.
    """
    response = client.post(
        "/api/analyze",
        json={"profile": "classical", "include_educational": False},
    )

    assert (
        response.status_code == 400
    ), f"Expected 400 for missing input, got {response.status_code}"


# -----------------------------
# Performance Sanity Checks
# -----------------------------


def test_analyze_completes_in_reasonable_time(client):
    """
    Smoke test: Verify API responds within reasonable time.

    This is a sanity check, not a strict performance test.
    """
    import time

    start = time.time()
    response = client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "profile": "classical",
            "include_educational": False,
        },
    )
    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 5.0, f"API took {elapsed:.2f}s, expected < 5s"
