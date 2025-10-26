"""Integration tests for music21 file upload workflow - SIMPLIFIED FOR ASYNC MIGRATION"""

import asyncio
from pathlib import Path

import pytest

# Test data directory
TEST_FILES_DIR = Path(__file__).parent.parent / "data" / "test_files"


@pytest.fixture
def simple_musicxml():
    """Path to simple MusicXML test file."""
    return str(TEST_FILES_DIR / "simple_folk_song.mxl")


class TestAnalysisIntegration:
    """Test harmonic analysis integration with file upload."""

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_analyze_file_with_analysis_returns_populated_results(
        self, simple_musicxml
    ):
        """Test that run_analysis=True returns fully populated analysis results."""
        from demo.lib.music_file_processing import analyze_uploaded_file

        # Main play: run file analysis with harmonic analysis enabled
        result = asyncio.run(
            analyze_uploaded_file(
                file_path=simple_musicxml,
                run_analysis=True,
                profile="classical",
            )
        )

        # Victory lap: verify analysis result is populated
        assert (
            result["analysis_result"] is not None
        ), "Analysis result should not be null"
        assert isinstance(
            result["analysis_result"], dict
        ), "Analysis result should be a dict"

        # Verify primary interpretation exists and has required fields
        assert (
            "primary" in result["analysis_result"]
        ), "Should have primary interpretation"
        primary = result["analysis_result"]["primary"]

        # Big play: verify all required fields are present and populated
        assert "key_signature" in primary, "Primary should have key_signature field"
        assert (
            primary["key_signature"] is not None
        ), "Primary key_signature should not be null"

        assert "roman_numerals" in primary, "Primary should have roman_numerals field"
        assert len(primary["roman_numerals"]) > 0, "Primary should have roman numerals"

        assert "confidence" in primary, "Primary should have confidence field"
        assert primary["confidence"] > 0, "Primary confidence should be > 0"

        # Verify analysis type is present
        assert "type" in primary, "Primary should have type field"

        # Victory lap: verify patterns and cadences structure
        assert "patterns" in primary, "Primary should have patterns field"
        assert isinstance(primary["patterns"], list), "Patterns should be a list"

        # Verify terminal cadences if present
        if "terminal_cadences" in primary:
            assert isinstance(primary["terminal_cadences"], list)
