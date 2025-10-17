"""
Integration tests for music21 file upload workflow.

Tests the complete file upload and chordify workflow including:
- File parsing (MusicXML and MIDI)
- Chordify chord reduction
- Chord labeling and detection comparison
- PNG notation generation
- MusicXML export
- Optional harmonic analysis integration
"""

import os
from pathlib import Path

import pytest

# Test data directory
TEST_FILES_DIR = Path(__file__).parent.parent / "data" / "test_files"

# Test files available
MUSICXML_FILES = [
    "chopin_etude_op10_no1.mxl",
    "simple_folk_song.mxl",
    "chopin_nocturne_op9_no2.mxl",
]

MIDI_FILES = [
    "beethoven_moonlight_sonata.mid",
]


@pytest.fixture
def simple_musicxml():
    """Path to simple MusicXML test file."""
    return str(TEST_FILES_DIR / "simple_folk_song.mxl")


@pytest.fixture
def complex_musicxml():
    """Path to complex MusicXML test file."""
    return str(TEST_FILES_DIR / "chopin_etude_op10_no1.mxl")


@pytest.fixture
def midi_file():
    """Path to MIDI test file."""
    return str(TEST_FILES_DIR / "beethoven_moonlight_sonata.mid")


@pytest.fixture
def nocturne_musicxml():
    """Path to Chopin nocturne test file."""
    return str(TEST_FILES_DIR / "chopin_nocturne_op9_no2.mxl")


class TestFileUploadBasics:
    """Test basic file upload and parsing functionality."""

    def test_analyze_uploaded_file_function_exists(self):
        """Backend function should be importable."""
        # Opening move: verify the function exists in demo
        from demo.full_library_demo import analyze_uploaded_file

        assert callable(analyze_uploaded_file)

    def test_file_upload_validates_file_existence(self):
        """Should raise FileNotFoundError for missing files."""
        from demo.full_library_demo import analyze_uploaded_file

        with pytest.raises(FileNotFoundError, match="File not found"):
            analyze_uploaded_file("/nonexistent/file.xml")

    def test_file_upload_validates_file_extension(self):
        """Should raise ValueError for unsupported file formats."""
        import tempfile

        from demo.full_library_demo import analyze_uploaded_file

        # Create a temp file with wrong extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                analyze_uploaded_file(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.skipif(
        not all((TEST_FILES_DIR / f).exists() for f in MUSICXML_FILES),
        reason="Test MusicXML files not available",
    )
    def test_can_parse_simple_musicxml(self, simple_musicxml):
        """Should successfully parse simple MusicXML file."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=False,
            label_chords=False,
            run_analysis=False,
        )

        # Victory lap: verify basic structure
        assert "chord_symbols" in result
        assert "key_hint" in result
        assert "metadata" in result
        assert isinstance(result["chord_symbols"], list)
        assert result["metadata"] is not None

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / MIDI_FILES[0]).exists(),
        reason="Test MIDI file not available",
    )
    def test_can_parse_midi_file(self, midi_file):
        """Should successfully parse MIDI file with warning."""
        from demo.full_library_demo import analyze_uploaded_file

        # MIDI parsing should issue warning about inferred chords
        with pytest.warns(
            UserWarning, match="MIDI files may not contain chord symbols"
        ):
            result = analyze_uploaded_file(
                file_path=midi_file,
                add_chordify=False,
                label_chords=False,
                run_analysis=False,
            )

        # Basic validation
        assert "chord_symbols" in result
        assert "metadata" in result


class TestChordifyFunctionality:
    """Test music21 chordify chord reduction functionality."""

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_chordify_generates_chord_reduction(self, simple_musicxml):
        """Chordify should create chord reduction staff."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=True,
            label_chords=False,
            run_analysis=False,
        )

        # Chordify adds comparison tracking
        assert "comparison" in result
        assert isinstance(result["comparison"], list)

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_chord_labeling_adds_symbols(self, simple_musicxml):
        """Chord labeling should add chord symbols to notation."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=True,
            label_chords=True,
            run_analysis=False,
        )

        # Main play: verify comparison data structure
        assert "comparison" in result
        assert len(result["comparison"]) > 0

        # Each comparison entry should have required fields
        for entry in result["comparison"]:
            assert "measure" in entry
            assert "music21" in entry
            assert "chord_logic" in entry
            assert "match" in entry
            assert isinstance(entry["match"], bool)

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_agreement_rate_calculated(self, simple_musicxml):
        """Should calculate agreement rate between detection methods."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=True,
            label_chords=True,
            run_analysis=False,
        )

        # Agreement rate should be calculated
        assert "agreement_rate" in result
        assert isinstance(result["agreement_rate"], float)
        assert 0.0 <= result["agreement_rate"] <= 1.0


class TestOutputGeneration:
    """Test PNG and MusicXML output generation."""

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_musicxml_export_created(self, simple_musicxml):
        """Should export annotated MusicXML file."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=True,
            label_chords=True,
            run_analysis=False,
        )

        # MusicXML export should be created
        assert "download_url" in result
        assert result["download_url"] is not None

        # File should exist
        download_path = result["download_url"]
        assert os.path.exists(download_path)
        assert download_path.endswith(".xml")

        # Clean up temp file
        if os.path.exists(download_path):
            os.unlink(download_path)

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_png_generation_requires_lilypond(self, simple_musicxml):
        """PNG generation requires Lilypond to be installed."""
        import shutil

        from demo.full_library_demo import analyze_uploaded_file

        # Check if Lilypond is installed
        lilypond_installed = shutil.which("lilypond") is not None

        if not lilypond_installed:
            # Should raise RuntimeError if Lilypond not installed
            with pytest.raises(RuntimeError, match="Lilypond is required"):
                analyze_uploaded_file(
                    file_path=simple_musicxml,
                    add_chordify=True,
                    label_chords=True,
                    run_analysis=False,
                )
        else:
            # If Lilypond is installed, PNG should be generated successfully
            result = analyze_uploaded_file(
                file_path=simple_musicxml,
                add_chordify=True,
                label_chords=True,
                run_analysis=False,
            )

            # PNG should be created
            assert "png_path" in result
            assert result["png_path"] is not None
            assert os.path.exists(result["png_path"])
            assert result["png_path"].endswith(".png")

            # Clean up temp files
            os.unlink(result["png_path"])
            if result["download_url"] and os.path.exists(result["download_url"]):
                os.unlink(result["download_url"])


class TestAnalysisIntegration:
    """Test optional harmonic analysis integration."""

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_optional_analysis_runs(self, simple_musicxml):
        """Should run harmonic analysis when requested."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=False,
            label_chords=False,
            run_analysis=True,
            profile="classical",
        )

        # Analysis result should be present
        assert "analysis_result" in result

        # If chords were extracted, analysis should have run
        if result["chord_symbols"]:
            assert result["analysis_result"] is not None
            assert isinstance(result["analysis_result"], dict)

            # Should have primary interpretation
            if "primary" in result["analysis_result"]:
                primary = result["analysis_result"]["primary"]
                assert "type" in primary
                assert "confidence" in primary

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_analysis_profile_respected(self, simple_musicxml):
        """Analysis should respect the provided profile."""
        from demo.full_library_demo import analyze_uploaded_file

        # Test with different profiles
        for profile in ["classical", "jazz", "pop"]:
            result = analyze_uploaded_file(
                file_path=simple_musicxml,
                add_chordify=False,
                label_chords=False,
                run_analysis=True,
                profile=profile,
            )

            # Should complete without error
            assert "analysis_result" in result


class TestComplexFiles:
    """Test with more complex musical files."""

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "chopin_etude_op10_no1.mxl").exists(),
        reason="Complex test file not available",
    )
    def test_complex_musicxml_handling(self, complex_musicxml):
        """Should handle complex polyphonic MusicXML files."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=complex_musicxml,
            add_chordify=True,
            label_chords=True,
            run_analysis=False,
        )

        # Big play: complex file should still be processed
        assert "chord_symbols" in result
        assert "comparison" in result
        assert "download_url" in result

        # Clean up temp files
        if result["download_url"] and os.path.exists(result["download_url"]):
            os.unlink(result["download_url"])
        if result.get("png_path") and os.path.exists(result["png_path"]):
            os.unlink(result["png_path"])

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "chopin_nocturne_op9_no2.mxl").exists(),
        reason="Nocturne test file not available",
    )
    def test_nocturne_with_full_workflow(self, nocturne_musicxml):
        """Test complete workflow with Chopin nocturne."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=nocturne_musicxml,
            add_chordify=True,
            label_chords=True,
            run_analysis=True,
            profile="classical",
        )

        # Victory lap: full workflow should complete
        assert "chord_symbols" in result
        assert "key_hint" in result
        assert "comparison" in result
        assert "agreement_rate" in result
        assert "download_url" in result

        # Clean up temp files
        if result["download_url"] and os.path.exists(result["download_url"]):
            os.unlink(result["download_url"])
        if result.get("png_path") and os.path.exists(result["png_path"]):
            os.unlink(result["png_path"])


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_corrupted_file_handling(self):
        """Should handle corrupted files gracefully."""
        import tempfile

        from demo.full_library_demo import analyze_uploaded_file

        # Create a corrupted XML file
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode="w") as f:
            f.write("This is not valid XML content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to parse"):
                analyze_uploaded_file(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_chordify_without_labeling(self, simple_musicxml):
        """Should handle chordify without chord labeling."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=True,
            label_chords=False,  # Chordify but don't label
            run_analysis=False,
        )

        # Should complete without comparison data
        assert "comparison" in result
        assert len(result["comparison"]) == 0

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_no_chordify_no_labeling(self, simple_musicxml):
        """Should handle no chordify and no labeling (extraction only)."""
        from demo.full_library_demo import analyze_uploaded_file

        result = analyze_uploaded_file(
            file_path=simple_musicxml,
            add_chordify=False,
            label_chords=False,
            run_analysis=False,
        )

        # Basic extraction should work
        assert "chord_symbols" in result
        assert "comparison" in result
        assert len(result["comparison"]) == 0  # No comparison without chordify


class TestRegressionPrevention:
    """Regression tests to ensure existing functionality unchanged."""

    @pytest.mark.skipif(
        not (TEST_FILES_DIR / "simple_folk_song.mxl").exists(),
        reason="Test MusicXML file not available",
    )
    def test_music21_adapter_still_works(self, simple_musicxml):
        """Music21Adapter should still work independently."""
        from harmonic_analysis.integrations.music21_adapter import Music21Adapter

        adapter = Music21Adapter()
        data = adapter.from_musicxml(simple_musicxml)

        # Basic adapter functionality unchanged
        assert "chord_symbols" in data
        assert "key_hint" in data
        assert "metadata" in data
        assert "structure" in data
        assert "score_object" in data

    def test_existing_demo_still_works(self):
        """Existing demo functionality should be unchanged."""
        from demo.full_library_demo import analyze_progression

        # Basic chord analysis should still work
        context = analyze_progression(
            key="C major",
            profile="classical",
            chords_text="C,Am,F,G",
            romans_text=None,
            melody_text=None,
            scales_input=None,
        )

        assert context.key == "C major"
        assert len(context.chords) == 4
        assert context.metadata["profile"] == "classical"
