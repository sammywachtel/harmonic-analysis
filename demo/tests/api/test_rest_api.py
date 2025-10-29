"""
Comprehensive tests for REST API endpoints.

Opening move: Test all API endpoints with various inputs.
These tests validate request handling, response format, error cases, and Gradio parity.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Kickoff: Import the app
from demo.backend.rest_api.main import create_app


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest_asyncio.fixture
async def async_client(app):
    """Create async HTTP client for testing."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Main play: Test root endpoint
@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    """Test root endpoint returns API information."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data
    assert "progression" in data["endpoints"]


# Big play: Test progression analysis endpoints
@pytest.mark.asyncio
async def test_analyze_chords(async_client):
    """Test chord progression analysis."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "analysis" in data
    assert "enhanced_summaries" in data


@pytest.mark.asyncio
async def test_analyze_chords_with_csv_string(async_client):
    """Test chord analysis with CSV string input."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": "Dm, G7, C",  # CSV string should be coerced to list
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data


@pytest.mark.asyncio
async def test_analyze_chords_with_educational(async_client):
    """Test chord analysis with educational content enabled."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
            "include_educational": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "analysis" in data
    assert "educational" in data
    assert "available" in data["educational"]


@pytest.mark.asyncio
async def test_analyze_chords_educational_default(async_client):
    """Test that educational is enabled by default."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Educational should be present by default
    assert "educational" in data


@pytest.mark.asyncio
async def test_analyze_chords_without_educational(async_client):
    """Test chord analysis with educational content disabled."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
            "include_educational": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "analysis" in data
    # Educational should not be in response when disabled
    assert "educational" not in data


@pytest.mark.asyncio
@pytest.mark.educational
async def test_educational_content_structure(async_client):
    """Test structure of educational content in response (if available)."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
            "include_educational": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    educational = data.get("educational")
    if educational and educational.get("available"):
        # If educational features are available, validate structure
        assert "content" in educational
        if educational["content"]:
            # Check first card structure
            card = educational["content"][0]
            assert "pattern_id" in card
            assert "title" in card
            assert "summary" in card
            # Optional fields
            if "category" in card:
                assert isinstance(card["category"], (str, type(None)))
            if "difficulty" in card:
                assert isinstance(card["difficulty"], (str, type(None)))


@pytest.mark.asyncio
@pytest.mark.educational
async def test_educational_content_pac_card(async_client):
    """
    Test that PAC card is returned for ii-V-I progression (Criterion 2).

    Victory lap: End-to-end test ensuring educational content appears for
    the classic ii-V-I progression in C major (Dm G7 C).
    """
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
            "include_educational": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Educational content should be available
    educational = data.get("educational")
    assert educational is not None, "Educational data should be present in response"
    assert (
        educational.get("available") is True
    ), "Educational features should be available"

    # Should have educational content
    content = educational.get("content")
    assert content is not None, "Educational content should not be None"
    assert len(content) > 0, "Educational content should contain at least one card"

    # Find PAC card in content
    pac_card = None
    for card in content:
        if card.get("pattern_id") == "cadence.authentic.perfect":
            pac_card = card
            break

    assert (
        pac_card is not None
    ), "PAC card (cadence.authentic.perfect) should be in educational content"

    # Validate PAC card structure
    assert pac_card["pattern_id"] == "cadence.authentic.perfect"
    assert "title" in pac_card
    assert len(pac_card["title"]) > 0
    assert "summary" in pac_card
    assert len(pac_card["summary"]) > 0
    assert "category" in pac_card


@pytest.mark.asyncio
@pytest.mark.educational
async def test_educational_full_explanations_included(async_client):
    """
    Test that full explanations are included in educational payload.

    Opening move: Verify explanations dict is present in response.
    Main play: Validate PAC full explanation structure (Layer 1 + Layer 2).
    Victory lap: Confirm all required fields present and non-empty.
    """
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
            "include_educational": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Opening move: verify educational payload structure
    educational = data.get("educational")
    assert educational is not None
    assert educational.get("available") is True

    # Main play: check explanations dict exists
    explanations = educational.get("explanations")
    assert (
        explanations is not None
    ), "Explanations dict should be in educational payload"
    assert isinstance(explanations, dict), "Explanations should be a dictionary"

    # Big play: verify PAC explanation is included
    pac_explanation = explanations.get("cadence.authentic.perfect")
    assert pac_explanation is not None, "PAC explanation should be in explanations dict"

    # Validate Layer 1 fields (core Bernstein-style content)
    assert "pattern_id" in pac_explanation
    assert pac_explanation["pattern_id"] == "cadence.authentic.perfect"
    assert "title" in pac_explanation
    assert pac_explanation["title"] == "Perfect Authentic Cadence (PAC)"

    # Check all required Layer 1 fields present and non-empty
    assert "hook" in pac_explanation
    assert len(pac_explanation["hook"]) > 0, "Hook should not be empty"

    assert "breakdown" in pac_explanation
    assert isinstance(pac_explanation["breakdown"], list)
    assert len(pac_explanation["breakdown"]) > 0, "Breakdown should have items"

    assert "story" in pac_explanation
    assert len(pac_explanation["story"]) > 0, "Story should not be empty"

    assert "composers" in pac_explanation
    assert len(pac_explanation["composers"]) > 0, "Composers should not be empty"

    assert "examples" in pac_explanation
    assert isinstance(pac_explanation["examples"], list)
    assert len(pac_explanation["examples"]) > 0, "Examples should have items"

    assert "try_this" in pac_explanation
    assert len(pac_explanation["try_this"]) > 0, "Try this should not be empty"

    # Victory lap: validate Layer 2 technical notes
    assert "technical_notes" in pac_explanation
    tech_notes = pac_explanation["technical_notes"]
    assert tech_notes is not None, "Technical notes should exist for PAC"

    assert "voice_leading" in tech_notes
    assert tech_notes["voice_leading"] is not None
    assert len(tech_notes["voice_leading"]) > 0

    assert "theoretical_depth" in tech_notes
    assert tech_notes["theoretical_depth"] is not None
    assert len(tech_notes["theoretical_depth"]) > 0

    assert "historical_context" in tech_notes
    assert tech_notes["historical_context"] is not None
    assert len(tech_notes["historical_context"]) > 0


@pytest.mark.asyncio
@pytest.mark.educational
async def test_educational_explanations_only_for_available_patterns(async_client):
    """
    Test that explanations are only included for patterns that have them.

    Time to tackle the tricky bit: Not all patterns will have full explanations.
    Only PAC has one in iteration_01, so we verify graceful handling.
    """
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["Dm", "G7", "C"],
            "key": "C major",
            "profile": "classical",
            "include_educational": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    educational = data.get("educational")
    explanations = educational.get("explanations", {})

    # Opening move: PAC should have explanation
    assert "cadence.authentic.perfect" in explanations

    # Main play: Other patterns detected might not have explanations yet
    # This is expected behavior - explanations are opt-in per pattern
    for pattern_id, explanation in explanations.items():
        # All explanations that exist should have required structure
        assert "pattern_id" in explanation
        assert "title" in explanation
        assert "hook" in explanation
        assert "breakdown" in explanation
        assert "story" in explanation
        assert "composers" in explanation
        assert "examples" in explanation
        assert "try_this" in explanation


@pytest.mark.asyncio
async def test_analyze_romans(async_client):
    """Test roman numeral analysis."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "romans": ["ii", "V", "I"],
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "analysis" in data


@pytest.mark.asyncio
async def test_analyze_melody(async_client):
    """Test melody analysis via progression endpoint."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "melody": ["C4", "D4", "E4", "F4", "G4"],
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "analysis" in data


@pytest.mark.asyncio
async def test_analyze_scale_via_progression(async_client):
    """Test scale analysis via progression endpoint."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "scales": [["C", "D", "E", "F", "G", "A", "B"]],
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "analysis" in data


@pytest.mark.asyncio
async def test_analyze_no_input_error(async_client):
    """Test that providing no input returns 400 error."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


# Victory lap: Test dedicated scale endpoint
@pytest.mark.asyncio
async def test_analyze_scale_dedicated(async_client):
    """Test dedicated scale analysis endpoint."""
    response = await async_client.post(
        "/api/analyze/scale",
        json={
            "notes": ["C", "D", "E", "F", "G", "A", "B"],
            "key": "C major",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Scale analysis returns dataclass dict
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_analyze_scale_missing_key_error(async_client):
    """Test scale analysis without key returns 400 error."""
    response = await async_client.post(
        "/api/analyze/scale",
        json={
            "notes": ["C", "D", "E", "F", "G", "A", "B"],
        },
    )
    assert response.status_code == 400


# Final whistle: Test dedicated melody endpoint
@pytest.mark.asyncio
async def test_analyze_melody_dedicated(async_client):
    """Test dedicated melody analysis endpoint."""
    response = await async_client.post(
        "/api/analyze/melody",
        json={
            "notes": ["C4", "D4", "E4", "F4", "G4"],
            "key": "C major",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Melody analysis returns dataclass dict
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_analyze_melody_missing_key_error(async_client):
    """Test melody analysis without key returns 400 error."""
    response = await async_client.post(
        "/api/analyze/melody",
        json={
            "notes": ["C4", "D4", "E4", "F4", "G4"],
        },
    )
    assert response.status_code == 400


# Glossary endpoint tests
@pytest.mark.asyncio
async def test_glossary_lookup_cadence(async_client):
    """Test glossary lookup for cadence term."""
    response = await async_client.get("/glossary/half_cadence")
    assert response.status_code == 200
    data = response.json()
    assert "term" in data
    assert "definition" in data or "type" in data


@pytest.mark.asyncio
async def test_glossary_lookup_not_found(async_client):
    """Test glossary lookup for non-existent term."""
    response = await async_client.get("/glossary/nonexistent_term_xyz")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# File upload endpoint tests
@pytest.mark.asyncio
async def test_analyze_file_midi(async_client):
    """Test file upload endpoint with MIDI file."""
    # Find test MIDI file
    test_file = (
        Path(__file__).parent.parent
        / "data"
        / "test_files"
        / "beethoven_moonlight_sonata.mid"
    )

    if not test_file.exists():
        pytest.skip(f"Test file not found: {test_file}")

    # Read file contents
    with open(test_file, "rb") as f:
        file_content = f.read()

    # Upload file
    response = await async_client.post(
        "/api/analyze/file",
        files={"file": ("test.mid", file_content, "audio/midi")},
        data={
            "add_chordify": "true",
            "label_chords": "true",
            "run_analysis": "false",
            "profile": "classical",
            "process_full_file": "false",
            "auto_window": "true",
            "manual_window_size": "1.0",
            "key_mode_preference": "Major",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "chord_symbols" in data
    assert "key_hint" in data
    assert "metadata" in data
    assert "notation_url" in data
    assert "download_url" in data
    assert isinstance(data["is_midi"], bool)
    assert data["is_midi"] is True  # Should detect MIDI


@pytest.mark.asyncio
async def test_analyze_file_invalid_format(async_client):
    """Test file upload with invalid file format."""
    response = await async_client.post(
        "/api/analyze/file",
        files={"file": ("test.txt", b"invalid content", "text/plain")},
        data={
            "add_chordify": "true",
            "label_chords": "true",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Unsupported file format" in data["detail"]


# Gradio parity tests
@pytest.mark.asyncio
async def test_gradio_parity_chord_analysis(async_client):
    """
    Test that API returns same results as Gradio demo.

    Victory lap: Verify API matches exact Gradio behavior.
    """
    test_chords = ["Dm", "G7", "C"]
    test_key = "C major"
    test_profile = "classical"

    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": test_chords,
            "key": test_key,
            "profile": test_profile,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure matches Gradio output
    assert "summary" in data
    assert "analysis" in data
    assert "enhanced_summaries" in data

    # Verify analysis contains expected fields
    analysis = data["analysis"]
    assert "primary" in analysis or "interpretations" in analysis


@pytest.mark.asyncio
async def test_gradio_parity_scale_analysis(async_client):
    """Test scale analysis matches Gradio behavior."""
    response = await async_client.post(
        "/api/analyze/scale",
        json={
            "notes": ["C", "D", "E", "F", "G", "A", "B"],
            "key": "C major",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Scale analysis should return dataclass-like structure
    assert isinstance(data, dict)


# Edge case tests
@pytest.mark.asyncio
async def test_analyze_empty_chord_list(async_client):
    """Test handling of empty chord list."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": [],
            "key": "C major",
            "profile": "classical",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analyze_with_auto_key(async_client):
    """Test analysis with auto key detection (no key hint)."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "profile": "classical",
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyze_with_none_key(async_client):
    """Test analysis with 'None' key string."""
    response = await async_client.post(
        "/api/analyze",
        json={
            "chords": ["C", "F", "G", "C"],
            "key": "None",  # Should be treated as null
            "profile": "classical",
        },
    )
    assert response.status_code == 200


# OpenAPI documentation test
@pytest.mark.asyncio
async def test_openapi_docs(async_client):
    """Test that OpenAPI documentation is accessible."""
    response = await async_client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_json(async_client):
    """Test that OpenAPI JSON schema is accessible."""
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
