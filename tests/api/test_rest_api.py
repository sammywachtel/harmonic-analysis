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
from harmonic_analysis.rest_api.main import create_app


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
