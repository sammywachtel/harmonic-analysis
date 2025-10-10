"""
Music21Adapter: Convert music21 objects to harmonic-analysis internal format.

This adapter enables parsing MusicXML and MIDI files while maintaining
the library's lightweight string-based internal representation.
"""

import warnings
from typing import Any, Dict, List, Optional


class Music21ImportError(ImportError):
    """Raised when music21 is not installed but required."""

    pass


class Music21Adapter:
    """
    Adapter to convert music21 Score objects to internal format.

    Handles parsing of MusicXML and MIDI files, extracting:
    - Chord symbols (as strings: 'C', 'Am', 'F7', etc.)
    - Key information (for key_hint parameter)
    - Structural metadata (title, composer, time signature)
    - Measure grouping and sectioning

    Usage:
        adapter = Music21Adapter()

        # From MusicXML
        data = adapter.from_musicxml('chopin_prelude.xml')

        # From MIDI
        data = adapter.from_midi('progression.mid')

        # Pass to analysis service
        result = await service.analyze_with_patterns_async(
            data['chord_symbols'],
            key_hint=data['key_hint'],
            profile=data.get('style', 'classical')
        )
    """

    def __init__(self) -> None:
        """Initialize adapter and verify music21 availability."""
        self._music21: Any = None
        self._check_music21_available()

    def _check_music21_available(self) -> None:
        """Verify music21 is installed and importable."""
        try:
            import music21  # type: ignore[import-not-found]

            self._music21 = music21
        except ImportError as e:
            raise Music21ImportError(
                "music21 is required for file I/O integration. "
                "Install with: pip install harmonic-analysis[music21]"
            ) from e

    def from_musicxml(self, file_path: str) -> Dict[str, Any]:
        """
        Parse MusicXML file and extract harmonic information.

        Args:
            file_path: Path to MusicXML file (.xml or .mxl)

        Returns:
            Dictionary containing:
                - chord_symbols (List[str]): Chord symbols as strings
                - key_hint (str): Detected key (e.g., 'C major', 'A minor')
                - metadata (Dict): Title, composer, tempo, time signature
                - structure (Dict): Measures, sections, repeats
                - score_object: Original music21 Score (for later annotation)

        Raises:
            Music21ImportError: If music21 not installed
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed

        Example:
            >>> adapter = Music21Adapter()
            >>> data = adapter.from_musicxml('chopin.xml')
            >>> print(data['chord_symbols'])
            ['Am', 'F', 'C', 'G']
            >>> print(data['key_hint'])
            'A minor'
        """
        # Opening move: validate file path
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"MusicXML file not found: {file_path}")

        # Main play: parse the score using music21
        try:
            score = self._music21.converter.parse(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse MusicXML file: {e}") from e

        # Extract all the goodies from the score
        return self._extract_from_score(score, file_path)

    def from_midi(self, file_path: str) -> Dict[str, Any]:
        """
        Parse MIDI file and extract harmonic information.

        Note: MIDI files don't contain chord symbols, so this method
        attempts to infer chords from simultaneous notes. Results may
        vary depending on the MIDI file complexity.

        Args:
            file_path: Path to MIDI file (.mid or .midi)

        Returns:
            Same structure as from_musicxml(), but:
                - chord_symbols may be inferred from notes
                - metadata may be limited (MIDI has less info)

        Raises:
            Music21ImportError: If music21 not installed
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed

        Example:
            >>> adapter = Music21Adapter()
            >>> data = adapter.from_midi('progression.mid')
            >>> print(data['chord_symbols'])
            ['C', 'Am', 'F', 'G']
        """
        # Opening move: validate file path
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"MIDI file not found: {file_path}")

        # Main play: parse MIDI using music21
        try:
            score = self._music21.converter.parse(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse MIDI file: {e}") from e

        # MIDI-specific handling: warn if no chord symbols found
        warnings.warn(
            "MIDI files may not contain chord symbols. "
            "Chords will be inferred from simultaneous notes, "
            "which may not always be accurate.",
            UserWarning,
        )

        return self._extract_from_score(score, file_path)

    def _extract_from_score(self, score: Any, file_path: str) -> Dict[str, Any]:
        """
        Extract harmonic content from a music21 Score object.

        This is where the real work happens - pulling out all the
        information we need for analysis while converting to our
        lightweight internal format.

        Args:
            score: music21.stream.Score object
            file_path: Original file path (for metadata)

        Returns:
            Structured dictionary with all extracted information
        """
        # Big play: extract key information
        key_hint = self._extract_key(score)

        # Extract chord symbols (either from ChordSymbol objects or inferred)
        chord_symbols = self._extract_chord_symbols(score)

        # Extract metadata (title, composer, etc.)
        metadata = self._extract_metadata(score, file_path)

        # Extract structural information (measures, sections)
        structure = self._extract_structure(score)

        # Victory lap: package everything up
        return {
            "chord_symbols": chord_symbols,
            "key_hint": key_hint,
            "metadata": metadata,
            "structure": structure,
            "score_object": score,  # Keep for later annotation
        }

    def _extract_key(self, score: Any) -> str:
        """
        Extract key from score using music21 analysis.

        Tries multiple methods:
        1. Explicit key signatures in the score
        2. music21's key analysis (Krumhansl-Schmuckler)
        3. Fallback to 'C major' if nothing found

        Args:
            score: music21 Score object

        Returns:
            Key as string (e.g., 'C major', 'A minor')
        """
        # First try: look for explicit key signatures
        key_sigs = score.flatten().getElementsByClass(self._music21.key.KeySignature)
        if key_sigs:
            # Get the first key signature
            key_obj = key_sigs[0]
            # Convert to Key object if it's just a KeySignature
            if isinstance(key_obj, self._music21.key.KeySignature):
                # Infer major/minor from key signature
                # This is a simplification - may need improvement
                tonic = key_obj.asKey("major")
                return f"{tonic.tonic.name} {tonic.mode}"

        # Second try: analyze the key using music21
        try:
            key_obj = score.analyze("key")
            if key_obj:
                return f"{key_obj.tonic.name} {key_obj.mode}"
        except Exception:
            # Analysis failed, continue to fallback
            pass

        # Final whistle: fallback to C major
        warnings.warn(
            "Could not determine key from score, defaulting to C major",
            UserWarning,
        )
        return "C major"

    def _extract_chord_symbols(self, score: Any) -> List[str]:
        """
        Extract chord symbols from score.

        Looks for ChordSymbol objects first. If none found,
        attempts to infer chords from simultaneous notes.

        Args:
            score: music21 Score object

        Returns:
            List of chord symbol strings (e.g., ['C', 'Am', 'F', 'G'])
        """
        chord_symbols = []

        # Opening move: look for explicit ChordSymbol objects
        flattened = score.flatten()
        harmony_symbols = flattened.getElementsByClass(
            self._music21.harmony.ChordSymbol
        )

        if harmony_symbols:
            # Victory: we have explicit chord symbols
            for chord_symbol in harmony_symbols:
                # Convert music21 ChordSymbol to string
                symbol_str = self._chord_to_symbol(chord_symbol)
                chord_symbols.append(symbol_str)
            return chord_symbols

        # Tricky bit: no chord symbols, try to infer from Chord objects
        chords = flattened.getElementsByClass(self._music21.chord.Chord)

        if chords:
            for chord in chords:
                symbol_str = self._chord_to_symbol(chord)
                chord_symbols.append(symbol_str)
            return chord_symbols

        # Final whistle: no chords found
        warnings.warn(
            "No chord symbols or chords found in score. "
            "You may need to add chord symbols manually.",
            UserWarning,
        )
        return []

    def _chord_to_symbol(self, chord_obj: Any) -> str:
        """
        Convert music21 Chord or ChordSymbol to string symbol.

        Args:
            chord_obj: music21.chord.Chord or harmony.ChordSymbol

        Returns:
            Chord symbol string (e.g., 'Cmaj7', 'Am', 'F7')
        """
        # Main play: use the figure attribute if available (ChordSymbol)
        if hasattr(chord_obj, "figure") and chord_obj.figure:
            return str(chord_obj.figure)

        # Backup plan: try to infer symbol from chord pitches
        try:
            # Get root and quality
            root = str(chord_obj.root().name)
            quality = self._infer_quality(chord_obj)
            return f"{root}{quality}"
        except Exception:
            # Last resort: just use the root note
            try:
                return str(chord_obj.root().name)
            except Exception:
                return "C"  # Ultimate fallback

    def _infer_quality(self, chord_obj: Any) -> str:
        """
        Infer chord quality from chord intervals.

        This is a simplified heuristic - music21's chord analysis
        can be more sophisticated, but this covers common cases.

        Args:
            chord_obj: music21.chord.Chord

        Returns:
            Quality string ('', 'm', '7', 'maj7', etc.)
        """
        # Check common chord types using music21's built-in methods
        if hasattr(chord_obj, "isMinorTriad") and chord_obj.isMinorTriad():
            return "m"
        elif hasattr(chord_obj, "isDominantSeventh") and chord_obj.isDominantSeventh():
            return "7"
        elif hasattr(chord_obj, "isMajorTriad") and chord_obj.isMajorTriad():
            return ""  # Major triad, no suffix
        elif hasattr(chord_obj, "isDiminishedTriad") and chord_obj.isDiminishedTriad():
            return "dim"

        # Fallback: return empty string for major
        return ""

    def _extract_metadata(self, score: Any, file_path: str) -> Dict[str, Optional[Any]]:
        """
        Extract metadata from score.

        Args:
            score: music21 Score object
            file_path: Original file path

        Returns:
            Dictionary with title, composer, tempo, time signature
        """
        metadata = {
            "title": None,
            "composer": None,
            "tempo": None,
            "time_signature": None,
            "file_path": file_path,
        }

        # Extract title
        if score.metadata and score.metadata.title:
            metadata["title"] = score.metadata.title

        # Extract composer
        if score.metadata and score.metadata.composer:
            metadata["composer"] = score.metadata.composer

        # Extract tempo
        tempos = score.flatten().getElementsByClass(self._music21.tempo.MetronomeMark)
        if tempos:
            metadata["tempo"] = tempos[0].number

        # Extract time signature
        time_sigs = score.flatten().getElementsByClass(
            self._music21.meter.TimeSignature
        )
        if time_sigs:
            metadata["time_signature"] = time_sigs[0].ratioString

        return metadata

    def _extract_structure(self, score: Any) -> Dict[str, Any]:
        """
        Extract structural information from score.

        Args:
            score: music21 Score object

        Returns:
            Dictionary with measure count, sections, parts
        """
        structure = {
            "measure_count": 0,
            "part_count": 0,
            "sections": [],
        }

        # Count measures
        measures = score.flatten().getElementsByClass(self._music21.stream.Measure)
        structure["measure_count"] = len(measures)

        # Count parts
        parts = score.getElementsByClass(self._music21.stream.Part)
        structure["part_count"] = len(parts)

        # Extract section markers (rehearsal marks, etc.)
        # This is a placeholder - could be enhanced
        structure["sections"] = []

        return structure
