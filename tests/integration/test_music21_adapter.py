"""
Unit tests for Music21Adapter.

These tests mock music21 to avoid requiring it as a dependency
for running the core test suite. Integration tests with real
music21 objects are in test_music21_integration.py.
"""

import importlib.util
from unittest.mock import MagicMock, patch

import pytest


# Import adapter module directly without triggering main package import
def import_adapter_module():
    """Import music21_adapter module directly from file."""
    spec = importlib.util.spec_from_file_location(
        "music21_adapter",
        "src/harmonic_analysis/integrations/music21_adapter.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def adapter_module():
    """Load adapter module once per test session."""
    mock_music21 = MagicMock()
    # Setup all the nested modules and classes that adapter uses
    mock_music21.converter = MagicMock()
    mock_music21.key.KeySignature = type("KeySignature", (), {})
    mock_music21.harmony.ChordSymbol = type("ChordSymbol", (), {})
    mock_music21.chord.Chord = type("Chord", (), {})
    mock_music21.tempo.MetronomeMark = type("MetronomeMark", (), {})
    mock_music21.meter.TimeSignature = type("TimeSignature", (), {})
    mock_music21.stream.Measure = type("Measure", (), {})
    mock_music21.stream.Part = type("Part", (), {})

    with patch.dict("sys.modules", {"music21": mock_music21}):
        module = import_adapter_module()
        yield module


@pytest.fixture
def mock_music21_module():
    """Provide mock music21 for tests that need it."""
    mock_music21 = MagicMock()
    mock_music21.converter = MagicMock()
    mock_music21.key.KeySignature = type("KeySignature", (), {})
    mock_music21.harmony.ChordSymbol = type("ChordSymbol", (), {})
    mock_music21.chord.Chord = type("Chord", (), {})
    mock_music21.tempo.MetronomeMark = type("MetronomeMark", (), {})
    mock_music21.meter.TimeSignature = type("TimeSignature", (), {})
    mock_music21.stream.Measure = type("Measure", (), {})
    mock_music21.stream.Part = type("Part", (), {})
    return mock_music21


class TestMusic21AdapterInitialization:
    """Test adapter initialization and music21 availability checks."""

    def test_init_without_music21_raises_error(self, adapter_module):
        """Should raise Music21ImportError when music21 not installed."""

        # Simulate ImportError by patching the check method
        def mock_check(self):
            raise adapter_module.Music21ImportError(
                "music21 is required for file I/O integration"
            )

        with patch.object(
            adapter_module.Music21Adapter,
            "_check_music21_available",
            mock_check,
        ):
            with pytest.raises(adapter_module.Music21ImportError) as exc_info:
                adapter_module.Music21Adapter()

            assert "music21 is required" in str(exc_info.value)

    def test_init_with_music21_succeeds(self, adapter_module):
        """Should initialize successfully when music21 is available."""
        adapter = adapter_module.Music21Adapter()
        assert adapter._music21 is not None


class TestMusic21AdapterMusicXMLParsing:
    """Test MusicXML file parsing functionality."""

    @pytest.fixture
    def adapter(self, adapter_module, mock_music21_module):
        """Create adapter with mocked music21."""
        adapter = adapter_module.Music21Adapter()
        adapter._music21 = mock_music21_module
        return adapter

    def test_from_musicxml_file_not_found(self, adapter):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError) as exc_info:
            adapter.from_musicxml("/nonexistent/file.xml")

        assert "not found" in str(exc_info.value)

    def test_from_musicxml_parse_error(self, adapter, tmp_path):
        """Should raise ValueError when file cannot be parsed."""
        # Create a temporary file
        test_file = tmp_path / "invalid.xml"
        test_file.write_text("invalid xml content")

        # Mock parse to raise exception
        adapter._music21.converter.parse.side_effect = Exception("Parse failed")

        with pytest.raises(ValueError) as exc_info:
            adapter.from_musicxml(str(test_file))

        assert "Failed to parse MusicXML" in str(exc_info.value)

    def test_from_musicxml_success(self, adapter, tmp_path):
        """Should successfully parse valid MusicXML file."""
        # Opening move: create test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<score></score>")

        # Set up mock score with chord symbols
        mock_score = MagicMock()
        mock_flattened = MagicMock()

        # Mock key analysis
        mock_key = MagicMock()
        mock_key.tonic.name = "C"
        mock_key.mode = "major"
        mock_score.analyze.return_value = mock_key

        # Mock chord symbols
        mock_chord_symbol = MagicMock()
        mock_chord_symbol.figure = "Cmaj7"
        mock_flattened.getElementsByClass.return_value = [mock_chord_symbol]

        mock_score.flatten.return_value = mock_flattened

        # Mock metadata
        mock_score.metadata = MagicMock()
        mock_score.metadata.title = "Test Piece"
        mock_score.metadata.composer = "Test Composer"

        adapter._music21.converter.parse.return_value = mock_score

        # Main play: parse the file
        result = adapter.from_musicxml(str(test_file))

        # Victory lap: verify all extracted data
        assert result["chord_symbols"] == ["Cmaj7"]
        assert result["key_hint"] == "C major"
        assert result["metadata"]["title"] == "Test Piece"
        assert result["metadata"]["composer"] == "Test Composer"
        assert result["score_object"] is mock_score


class TestMusic21AdapterMIDIParsing:
    """Test MIDI file parsing functionality."""

    @pytest.fixture
    def adapter(self, adapter_module, mock_music21_module):
        """Create adapter with mocked music21."""
        adapter = adapter_module.Music21Adapter()
        adapter._music21 = mock_music21_module
        return adapter

    def test_from_midi_file_not_found(self, adapter):
        """Should raise FileNotFoundError for missing MIDI files."""
        with pytest.raises(FileNotFoundError) as exc_info:
            adapter.from_midi("/nonexistent/file.mid")

        assert "MIDI file not found" in str(exc_info.value)

    def test_from_midi_parse_error(self, adapter, tmp_path):
        """Should raise ValueError when MIDI cannot be parsed."""
        test_file = tmp_path / "invalid.mid"
        test_file.write_bytes(b"invalid midi")

        adapter._music21.converter.parse.side_effect = Exception("MIDI parse failed")

        with pytest.raises(ValueError) as exc_info:
            adapter.from_midi(str(test_file))

        assert "Failed to parse MIDI" in str(exc_info.value)

    def test_from_midi_warns_about_chord_inference(self, adapter, tmp_path):
        """Should warn user about chord inference from MIDI."""
        test_file = tmp_path / "test.mid"
        test_file.write_bytes(b"MThd")  # MIDI header

        mock_score = MagicMock()
        mock_score.flatten.return_value = MagicMock()
        mock_score.analyze.return_value = MagicMock(
            tonic=MagicMock(name="C"), mode="major"
        )
        adapter._music21.converter.parse.return_value = mock_score

        with pytest.warns(UserWarning, match="MIDI files may not contain"):
            adapter.from_midi(str(test_file))


class TestMusic21AdapterKeyExtraction:
    """Test key extraction from scores."""

    @pytest.fixture
    def adapter(self, adapter_module, mock_music21_module):
        """Create adapter with mocked music21."""
        adapter = adapter_module.Music21Adapter()
        adapter._music21 = mock_music21_module
        return adapter

    def test_extract_key_from_analysis(self, adapter):
        """Should extract key using music21 analysis."""
        mock_score = MagicMock()
        mock_score.flatten.return_value.getElementsByClass.return_value = []

        mock_key = MagicMock()
        mock_key.tonic.name = "A"
        mock_key.mode = "minor"
        mock_score.analyze.return_value = mock_key

        result = adapter._extract_key(mock_score)
        assert result == "A minor"

    def test_extract_key_fallback_to_c_major(self, adapter):
        """Should fallback to C major when key cannot be determined."""
        mock_score = MagicMock()
        mock_score.flatten.return_value.getElementsByClass.return_value = []
        mock_score.analyze.side_effect = Exception("Analysis failed")

        with pytest.warns(UserWarning, match="Could not determine key from score"):
            result = adapter._extract_key(mock_score)

        assert result == "C major"


class TestMusic21AdapterChordExtraction:
    """Test chord symbol extraction from scores."""

    @pytest.fixture
    def adapter(self, adapter_module, mock_music21_module):
        """Create adapter with mocked music21."""
        adapter = adapter_module.Music21Adapter()
        adapter._music21 = mock_music21_module
        return adapter

    def test_extract_chord_symbols_from_harmony_objects(self, adapter):
        """Should extract chord symbols from ChordSymbol objects."""
        mock_score = MagicMock()
        mock_flattened = MagicMock()

        # Mock ChordSymbol objects
        chord1 = MagicMock()
        chord1.figure = "Cmaj7"
        chord2 = MagicMock()
        chord2.figure = "Am"

        # Return ChordSymbols on first call, empty on second
        mock_flattened.getElementsByClass.side_effect = [
            [chord1, chord2],  # ChordSymbol query
            [],  # Chord query (won't be called)
        ]

        mock_score.flatten.return_value = mock_flattened

        result = adapter._extract_chord_symbols(mock_score)
        assert result == ["Cmaj7", "Am"]

    def test_extract_chord_symbols_inferred_from_chords(self, adapter):
        """Should infer chord symbols from Chord objects when no symbols."""
        mock_score = MagicMock()
        mock_flattened = MagicMock()

        # Mock Chord objects
        chord1 = MagicMock()
        chord1.figure = None
        chord1.root.return_value.name = "C"
        # Explicitly set chord1 to be major (not minor, not dominant, not diminished)
        chord1.isMinorTriad.return_value = False
        chord1.isDominantSeventh.return_value = False
        chord1.isMajorTriad.return_value = True
        chord1.isDiminishedTriad.return_value = False

        chord2 = MagicMock()
        chord2.figure = None
        chord2.root.return_value.name = "A"
        # Explicitly set chord2 to be minor
        chord2.isMinorTriad.return_value = True
        chord2.isDominantSeventh.return_value = False
        chord2.isMajorTriad.return_value = False
        chord2.isDiminishedTriad.return_value = False

        mock_flattened.getElementsByClass.side_effect = [
            [],  # No ChordSymbols
            [chord1, chord2],  # Chord objects
        ]

        mock_score.flatten.return_value = mock_flattened

        result = adapter._extract_chord_symbols(mock_score)
        assert result == ["C", "Am"]

    def test_extract_chord_symbols_empty_warns(self, adapter):
        """Should warn when no chords found in score."""
        mock_score = MagicMock()
        mock_flattened = MagicMock()
        mock_flattened.getElementsByClass.return_value = []
        mock_score.flatten.return_value = mock_flattened

        with pytest.warns(UserWarning, match="No chord symbols or chords"):
            result = adapter._extract_chord_symbols(mock_score)

        assert result == []


class TestMusic21AdapterChordConversion:
    """Test conversion of music21 chords to symbol strings."""

    @pytest.fixture
    def adapter(self, adapter_module, mock_music21_module):
        """Create adapter with mocked music21."""
        adapter = adapter_module.Music21Adapter()
        adapter._music21 = mock_music21_module
        return adapter

    def test_chord_to_symbol_with_figure(self, adapter):
        """Should use figure attribute when available."""
        mock_chord = MagicMock()
        mock_chord.figure = "Dm7"

        result = adapter._chord_to_symbol(mock_chord)
        assert result == "Dm7"

    def test_chord_to_symbol_infer_minor(self, adapter):
        """Should infer minor quality from chord intervals."""
        mock_chord = MagicMock()
        mock_chord.figure = None
        mock_chord.root.return_value.name = "D"
        mock_chord.isMinorTriad.return_value = True

        result = adapter._chord_to_symbol(mock_chord)
        assert result == "Dm"

    def test_chord_to_symbol_infer_dominant_seventh(self, adapter):
        """Should infer dominant seventh quality."""
        mock_chord = MagicMock()
        mock_chord.figure = None
        mock_chord.root.return_value.name = "G"
        mock_chord.isMinorTriad.return_value = False
        mock_chord.isDominantSeventh.return_value = True

        result = adapter._chord_to_symbol(mock_chord)
        assert result == "G7"

    def test_chord_to_symbol_fallback(self, adapter):
        """Should fallback to root when inference fails."""
        mock_chord = MagicMock()
        mock_chord.figure = None
        mock_chord.root.return_value.name = "C"
        mock_chord.isMinorTriad.return_value = False
        mock_chord.isDominantSeventh.return_value = False
        mock_chord.isMajorTriad.return_value = False
        mock_chord.isDiminishedTriad.return_value = False

        result = adapter._chord_to_symbol(mock_chord)
        assert result == "C"


class TestMusic21AdapterMetadataExtraction:
    """Test metadata extraction from scores."""

    @pytest.fixture
    def adapter(self, adapter_module, mock_music21_module):
        """Create adapter with mocked music21."""
        adapter = adapter_module.Music21Adapter()
        adapter._music21 = mock_music21_module
        return adapter

    def test_extract_metadata_complete(self, adapter):
        """Should extract all available metadata."""
        mock_score = MagicMock()
        mock_score.metadata.title = "Prelude in C"
        mock_score.metadata.composer = "J.S. Bach"

        mock_tempo = MagicMock()
        mock_tempo.number = 120

        mock_time_sig = MagicMock()
        mock_time_sig.ratioString = "4/4"

        mock_flattened = MagicMock()
        mock_flattened.getElementsByClass.side_effect = [
            [mock_tempo],
            [mock_time_sig],
        ]
        mock_score.flatten.return_value = mock_flattened

        result = adapter._extract_metadata(mock_score, "test.xml")

        assert result["title"] == "Prelude in C"
        assert result["composer"] == "J.S. Bach"
        assert result["tempo"] == 120
        assert result["time_signature"] == "4/4"
        assert result["file_path"] == "test.xml"

    def test_extract_metadata_minimal(self, adapter):
        """Should handle missing metadata gracefully."""
        mock_score = MagicMock()
        mock_score.metadata = None
        mock_flattened = MagicMock()
        mock_flattened.getElementsByClass.return_value = []
        mock_score.flatten.return_value = mock_flattened

        result = adapter._extract_metadata(mock_score, "test.xml")

        assert result["title"] is None
        assert result["composer"] is None
        assert result["tempo"] is None
        assert result["time_signature"] is None
        assert result["file_path"] == "test.xml"


class TestMusic21AdapterStructureExtraction:
    """Test structure extraction from scores."""

    @pytest.fixture
    def adapter(self, adapter_module, mock_music21_module):
        """Create adapter with mocked music21."""
        adapter = adapter_module.Music21Adapter()
        adapter._music21 = mock_music21_module
        return adapter

    def test_extract_structure(self, adapter):
        """Should extract measure and part counts."""
        mock_score = MagicMock()

        # Mock measures
        mock_measures = [MagicMock() for _ in range(16)]
        # Mock parts
        mock_parts = [MagicMock() for _ in range(2)]

        mock_flattened = MagicMock()
        mock_flattened.getElementsByClass.return_value = mock_measures
        mock_score.flatten.return_value = mock_flattened
        mock_score.getElementsByClass.return_value = mock_parts

        result = adapter._extract_structure(mock_score)

        assert result["measure_count"] == 16
        assert result["part_count"] == 2
        assert result["sections"] == []
