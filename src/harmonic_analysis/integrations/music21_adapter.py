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
            # Analysis failed, continue to fallback (intentional)
            pass  # nosec B110

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

    def detect_tempo_from_score(self, score: Any) -> float:
        """
        Detect tempo from score, either from tempo marking or estimated
        from note density.

        Opening move: Look for explicit tempo markings in the score
        metadata. If none found, estimate tempo based on note density in
        the opening measures. This heuristic helps set appropriate analysis
        windows even when tempo isn't marked.

        Args:
            score: music21 Score object

        Returns:
            Tempo in BPM (beats per minute). Defaults to 100 if not found.

        Example:
            >>> adapter = Music21Adapter()
            >>> score = adapter._music21.converter.parse(
            ...     'tests/data/test_files/simple_progression.xml'
            ... )
            >>> tempo = adapter.detect_tempo_from_score(score)
            >>> print(f"Detected tempo: {tempo} BPM")
            Detected tempo: 120.0 BPM
        """
        try:
            # First, look for explicit tempo markings
            tempo_marks = score.flatten().getElementsByClass(
                self._music21.tempo.MetronomeMark
            )
            if tempo_marks:
                bpm = tempo_marks[0].number
                # Check if bpm is valid (not None)
                if bpm is not None and bpm > 0:
                    print(f"DEBUG: Found tempo marking: {bpm} BPM")
                    return float(bpm)
                else:
                    print(f"DEBUG: Found tempo marking but value is " f"invalid: {bpm}")

            # If no tempo marking, estimate from note density
            # This is a rough heuristic: count notes in first 4 measures
            total_notes = 0
            total_duration = 0.0

            for part in score.parts[:1]:  # Just check first part
                measures = part.getElementsByClass("Measure")
                for measure in measures[:4]:  # First 4 measures
                    notes = measure.flatten().notesAndRests
                    total_notes += len([n for n in notes if n.isNote or n.isChord])
                    total_duration += measure.quarterLength

            if total_duration > 0:
                # Notes per quarter note
                density = total_notes / total_duration
                # Rough estimate: higher density often means faster tempo
                # This is very approximate but better than nothing
                if density > 4:  # Very dense (lots of 16ths)
                    estimated_bpm = 140
                elif density > 2:  # Moderate (8ths, some 16ths)
                    estimated_bpm = 110
                else:  # Sparse (quarters, halves)
                    estimated_bpm = 80

                print(
                    f"DEBUG: Estimated tempo from note density: "
                    f"{estimated_bpm} BPM (density={density:.2f} notes/QL)"
                )
                return float(estimated_bpm)

        except Exception as e:
            print(f"DEBUG: Could not detect tempo: {e}")

        # Default fallback
        print("DEBUG: Using default tempo: 100 BPM")
        return 100.0

    def chordify_score(
        self,
        score: Any,
        analysis_window: float = 2.0,
        sample_interval: float = 0.25,
        process_full_file: bool = True,
        max_measures: int = 20,
    ) -> Any:
        """
        Create chord reduction staff from multi-part score using
        adaptive windowing.

        Opening move: Set up chord staff with proper clef and key
        signature. This staff will contain the harmonic reduction of
        the entire score.

        Main play: Use sliding window analysis to detect chord changes
        intelligently. We sample at fine intervals (16th notes) but merge
        regions where harmony is stable, then split at measure boundaries
        to match notation conventions.

        Victory lap: Return the original score with chordified staff added
        at bottom.

        Args:
            score: music21 Score object to chordify
            analysis_window: Window size in quarter lengths for chord
                detection (default 2.0 = half note)
            sample_interval: Sampling interval in quarter lengths
                (default 0.25 = 16th note)
            process_full_file: Whether to process entire file (vs first N
                measures)
            max_measures: Maximum measures to process if
                process_full_file=False

        Returns:
            New music21 Score with chord staff added (original parts +
            chord staff at bottom)

        Example:
            >>> adapter = Music21Adapter()
            >>> score = adapter._music21.converter.parse('chopin.xml')
            >>> # Auto-detect tempo and calculate window
            >>> tempo = adapter.detect_tempo_from_score(score)
            >>> from harmonic_analysis.core.utils import (
            ...     calculate_initial_window
            ... )
            >>> window = calculate_initial_window(tempo)
            >>> # Chordify with adaptive windowing
            >>> chordified_score = adapter.chordify_score(
            ...     score, analysis_window=window
            ... )
            >>> chordified_score.write(
            ...     'musicxml', fp='chopin_with_chords.xml'
            ... )
        """
        import copy

        # Create chord staff with adaptive windowing
        chordified = self._music21.stream.Part()
        chordified.partName = "Chord Analysis"

        # Set bass clef for chord analysis staff (chord symbols
        # typically in bass register)
        bass_clef = self._music21.clef.BassClef()
        chordified.insert(0, bass_clef)
        print("DEBUG: Set bass clef for chord analysis staff")

        # Copy key signature from original score (important: chord staff
        # should match original key)
        try:
            original_key = score.flatten().getElementsByClass("KeySignature")[0]
            print(
                f"DEBUG: Found original key signature: " f"{original_key.sharps} sharps"
            )
            # Create a NEW KeySignature object to avoid reference issues
            key_copy = self._music21.key.KeySignature(original_key.sharps)
            print(
                f"DEBUG: Created new key signature copy: " f"{key_copy.sharps} sharps"
            )
            chordified.insert(0, key_copy)
            print("DEBUG: ✓ Inserted key signature into chord staff at offset 0")
        except (IndexError, AttributeError) as e:
            print(f"DEBUG: No key signature found in original score: {e}")

        # CRITICAL: Copy time signature from original score (prevents
        # Dorico signpost issues)
        try:
            original_time = score.flatten().getElementsByClass("TimeSignature")[0]
            # Create a new TimeSignature object to avoid reference issues
            time_sig_copy = self._music21.meter.TimeSignature(
                f"{original_time.numerator}/{original_time.denominator}"
            )
            chordified.insert(0, time_sig_copy)
            print(
                f"DEBUG: Copied time signature to chord staff: "
                f"{original_time.numerator}/{original_time.denominator}"
            )
        except (IndexError, AttributeError) as e:
            print(f"DEBUG: No time signature found in original score: {e}")

        # Get the total duration of the piece
        full_duration = score.flatten().highestTime

        # Performance optimization: For large files, only chordify first portion
        # UNLESS user explicitly requested full file processing for download
        measure_count = (
            max(len(part.getElementsByClass("Measure")) for part in score.parts)
            if score.parts
            else 0
        )
        if measure_count > max_measures and not process_full_file:
            # Calculate duration of first N measures
            try:
                time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
                quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
            except (IndexError, AttributeError):
                quarters_per_measure = 4.0

            total_duration = max_measures * quarters_per_measure
            print(
                f"DEBUG: Large file detected - limiting chordify to first "
                f"{max_measures} measures ({total_duration} QL instead of "
                f"{full_duration} QL)"
            )
            print(
                "       💡 Tip: Enable 'Process Full File' option to "
                "include all measures in download"
            )
        else:
            total_duration = full_duration
            if measure_count > max_measures:
                print(
                    f"DEBUG: Processing full file ({measure_count} measures, "
                    f"{full_duration} QL) - this will take 1-2 minutes"
                )

        print(
            f"DEBUG: Using adaptive windowing (sample={sample_interval}QL, "
            f"window={analysis_window}QL)"
        )

        # First pass: collect pitch sets at each sample point
        samples = []

        # Generate list of offsets to iterate over
        offsets = []
        temp_offset = 0.0
        while temp_offset < total_duration:
            offsets.append(temp_offset)
            temp_offset += sample_interval

        # Use progress tracking with periodic updates
        for idx, current_offset in enumerate(offsets):
            # Collect all notes sounding at this moment
            pitches_at_moment = []

            for part in score.parts:
                for element in part.flatten().notesAndRests:
                    if element.isNote:
                        note_start = element.offset
                        note_end = element.offset + element.duration.quarterLength

                        # Note is sounding if current_offset is within its duration
                        if note_start <= current_offset < note_end:
                            pitches_at_moment.append(element.pitch)
                    elif element.isChord:
                        chord_start = element.offset
                        chord_end = element.offset + element.duration.quarterLength

                        # Chord is sounding at this moment
                        if chord_start <= current_offset < chord_end:
                            pitches_at_moment.extend(element.pitches)

            # Store pitch class set (not MIDI notes) for comparison
            pitch_classes = frozenset(p.pitchClass for p in pitches_at_moment)

            if pitch_classes:  # Only add if there are notes
                samples.append(
                    {
                        "offset": current_offset,
                        "pitch_classes": pitch_classes,
                        "pitches": pitches_at_moment,
                    }
                )

        print(f"DEBUG: Collected {len(samples)} sample points")

        # Second pass: use sliding window to detect chord changes
        # Look ahead to accumulate notes before deciding on boundaries
        merged_regions: List[Dict[str, Any]] = []

        if samples:
            i = 0

            while i < len(samples):
                # Look ahead: collect all notes within the next analysis_window
                window_start = samples[i]["offset"]  # type: ignore[index]
                window_end = window_start + analysis_window  # type: ignore[operator]

                # Accumulate all pitch classes in this window
                window_pitch_classes: set[Any] = set()
                window_pitches: List[Any] = []

                # Collect samples within this window
                j = i
                sample_offset = samples[j]["offset"]  # type: ignore[index]
                while j < len(samples) and sample_offset < window_end:  # type: ignore[operator]  # noqa: E501
                    pcs = samples[j]["pitch_classes"]  # type: ignore[index]
                    window_pitch_classes |= pcs  # type: ignore[arg-type]
                    pitches = samples[j]["pitches"]  # type: ignore[index]
                    window_pitches.extend(pitches)  # type: ignore[arg-type]
                    j += 1
                    if j < len(samples):
                        sample_offset = samples[j]["offset"]  # type: ignore[index]

                if window_pitch_classes:
                    # Import chord detection here to avoid circular import
                    from harmonic_analysis.core.utils.chord_detection import (
                        detect_chord_from_pitches,
                    )

                    # Detect chord from accumulated window
                    window_chord = detect_chord_from_pitches(
                        [pc for pc in window_pitch_classes]
                    )

                    # Check if this chord is different from previous region
                    if merged_regions:
                        prev_chord = detect_chord_from_pitches(
                            [pc for pc in merged_regions[-1]["pitch_classes"]]
                        )

                        # Compare chord roots (ignore inversions)
                        prev_root = (
                            prev_chord.split("/")[0]
                            if "/" in prev_chord
                            else prev_chord
                        )
                        curr_root = (
                            window_chord.split("/")[0]
                            if "/" in window_chord
                            else window_chord
                        )

                        # If same chord, extend previous region
                        if prev_root == curr_root and curr_root != "Unknown":
                            # Merge with previous region
                            merged_regions[-1]["pitch_classes"] |= window_pitch_classes
                            merged_regions[-1]["pitches"].extend(window_pitches)
                            merged_regions[-1]["end"] = window_end
                            merged_regions[-1]["duration"] = (
                                merged_regions[-1]["end"] - merged_regions[-1]["start"]
                            )
                        else:
                            # Different chord - create new region
                            merged_regions.append(
                                {
                                    "start": window_start,
                                    "end": window_end,
                                    "duration": analysis_window,
                                    "pitch_classes": window_pitch_classes,
                                    "pitches": window_pitches,
                                }
                            )
                    else:
                        # First region
                        merged_regions.append(
                            {
                                "start": window_start,
                                "end": window_end,
                                "duration": analysis_window,
                                "pitch_classes": window_pitch_classes,
                                "pitches": window_pitches,
                            }
                        )

                # Move to next window (advance by full window size - non-overlapping)
                i = j

        print(
            f"DEBUG: Merged into {len(merged_regions)} harmonic regions "
            f"via sliding windows"
        )

        # CRITICAL: Split regions at measure boundaries
        # Musical convention: each measure should get its own chord instance,
        # even if the harmony continues from the previous measure
        try:
            time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
            quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
        except (IndexError, AttributeError):
            quarters_per_measure = 4.0  # Default to 4/4 time

        measure_aware_regions = []
        for region in merged_regions:
            # Calculate which measures this region spans
            start_measure = int(region["start"] / quarters_per_measure)
            end_measure = int(
                (region["end"] - 0.001) / quarters_per_measure
            )  # Subtract small amount to handle exact boundaries

            if start_measure == end_measure:
                # Region fits within a single measure - keep as is
                measure_aware_regions.append(region)
            else:
                # Region crosses measure boundary - split it
                for measure_num in range(start_measure, end_measure + 1):
                    measure_start_offset = measure_num * quarters_per_measure
                    measure_end_offset = (measure_num + 1) * quarters_per_measure

                    # Calculate intersection with this measure
                    split_start = max(region["start"], measure_start_offset)
                    split_end = min(region["end"], measure_end_offset)

                    if split_end > split_start:  # Valid intersection
                        measure_aware_regions.append(
                            {
                                "start": split_start,
                                "end": split_end,
                                "duration": split_end - split_start,
                                "pitch_classes": region["pitch_classes"],
                                "pitches": region["pitches"],
                            }
                        )

        print(
            f"DEBUG: Split into {len(measure_aware_regions)} "
            f"measure-aware regions (respecting barlines)"
        )

        # DEBUG: Show how many chords per measure
        chords_per_measure: Dict[int, int] = {}
        for region in measure_aware_regions:
            measure_num = int(region["start"] / quarters_per_measure) + 1  # 1-indexed
            chords_per_measure[measure_num] = chords_per_measure.get(measure_num, 0) + 1

        # Show first 10 measures
        first_10_measures = sorted([m for m in chords_per_measure.keys() if m <= 10])
        if first_10_measures:
            measure_stats = ", ".join(
                [f"M{m}:{chords_per_measure[m]}" for m in first_10_measures]
            )
            print(f"DEBUG: Chords per measure (first 10): {measure_stats}")

        # Third pass: create chords from measure-aware regions
        for region in measure_aware_regions:
            if region["pitches"]:
                # Remove duplicate pitches (same MIDI note)
                unique_pitches = []
                seen_midi = set()
                for p in region["pitches"]:
                    if p.midi not in seen_midi:
                        unique_pitches.append(p)
                        seen_midi.add(p.midi)

                # Create chord for this region
                window_chord = self._music21.chord.Chord(unique_pitches)
                duration = region["duration"]
                window_chord.quarterLength = duration  # type: ignore[attr-defined]
                # CRITICAL: Set voice to 1 to prevent MusicXML export warnings
                # Missing voice tags cause Dorico to misinterpret the entire score
                window_chord.voice = 1  # type: ignore[attr-defined]
                start_offset = region["start"]
                chordified.insert(start_offset, window_chord)  # type: ignore[arg-type]

        print(
            f"DEBUG: Created {len(chordified.flatten().notesAndRests)} adaptive chords"
        )

        # Note: We intentionally do NOT call makeMeasures() here
        # music21 will auto-generate measures during MusicXML export
        # Calling makeMeasures() can corrupt the measure structure of the
        # entire score

        # Critical fix: Rebuild score with proper part order
        # Chord staff should appear at BOTTOM (traditional lead sheet
        # style)

        # Save original parts
        original_parts = list(score.parts)

        # Create new score with metadata preserved
        new_score = self._music21.stream.Score()
        if score.metadata:
            new_score.metadata = score.metadata

        # Add original parts FIRST (top staves)
        # CRITICAL: Deep copy parts to avoid music21 export modifying them in place
        copied_parts = []
        for part in original_parts:
            new_part = copy.deepcopy(part)
            new_score.append(new_part)
            copied_parts.append(new_part)

        # Create a staff group for the original parts (to keep them
        # visually separate from chord analysis)
        if len(copied_parts) > 0:
            # StaffGroup keeps original parts together with bracket
            original_group = self._music21.layout.StaffGroup(
                copied_parts, name="Original", symbol="bracket"
            )
            new_score.insert(0, original_group)

        # CRITICAL: Set explicit instrument to prevent auto-grouping with
        # piano parts. Use a generic instrument to mark this as completely
        # separate
        chord_instrument = self._music21.instrument.Instrument()
        chord_instrument.instrumentName = "Chord Analysis"
        chord_instrument.instrumentAbbreviation = "Ch."
        chordified.insert(0, chord_instrument)
        print(
            "DEBUG: Set explicit instrument for chord staff to prevent " "auto-grouping"
        )

        # Add chordified LAST as a completely separate part (no staff
        # group, separate instrument)
        new_score.append(chordified)

        print(
            f"DEBUG: Score rebuilt with {len(new_score.parts)} parts "
            f"(chord staff as separate instrument at bottom)"
        )

        return new_score

    def label_chords(self, score: Any) -> List[Dict[str, Any]]:
        """
        Label chords in the score's chord analysis staff with chord
        symbols.

        Opening move: Find the chord analysis staff (last part in score).
        Main play: For each chord in the staff, detect the chord symbol
        using the library's chord detection, add it as a lyric below the
        staff, and track measure numbers.
        Victory lap: Return list of chord symbols with measure information.

        CRITICAL: This method uses ONLY the library's
        detect_chord_from_pitches. No music21 comparison code is included.

        Args:
            score: music21 Score object with chord analysis staff (last part)

        Returns:
            List of dictionaries containing:
                - measure (int): Measure number (1-indexed)
                - chord (str): Detected chord symbol
                - offset (float): Offset in quarter lengths

        Example:
            >>> adapter = Music21Adapter()
            >>> score = adapter._music21.converter.parse('chopin.xml')
            >>> tempo = adapter.detect_tempo_from_score(score)
            >>> from harmonic_analysis.core.utils import (
            ...     calculate_initial_window
            ... )
            >>> window = calculate_initial_window(tempo)
            >>> chordified_score = adapter.chordify_score(
            ...     score, analysis_window=window
            ... )
            >>> chord_data = adapter.label_chords(chordified_score)
            >>> print(chord_data[0])
            {'measure': 1, 'chord': 'C', 'offset': 0.0}
        """
        from harmonic_analysis.core.utils.chord_detection import (
            detect_chord_from_pitches,
        )

        chordified_symbols_with_measures = []

        # For each chord in chordified staff, detect and label
        # Need to iterate through the actual chordified part in the score
        chord_part = score.parts[-1]  # Last part is chord analysis
        labeled_count = 0

        # Get time signature to calculate measure numbers from offsets
        # Assume 4/4 time if not specified (4 quarter notes per measure)
        try:
            time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
            quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
        except (IndexError, AttributeError):
            quarters_per_measure = 4.0  # Default to 4/4 time

        print(
            f"DEBUG: Calculating measures with {quarters_per_measure} "
            f"quarters per measure"
        )

        for element in chord_part.flatten().notesAndRests:
            if element.isChord:
                # Detect chord using library's chord detection
                try:
                    # Get MIDI pitch numbers from the chord
                    pitches = [p.midi for p in element.pitches]
                    chord_symbol = detect_chord_from_pitches(pitches)
                except (AttributeError, Exception) as e:
                    print(f"DEBUG: chord detection failed: {e}")
                    chord_symbol = "Unknown"

                # Add chord labels to the score as lyrics (below staff)
                element.addLyric(chord_symbol)
                labeled_count += 1

                # Calculate measure number from offset
                # Measure numbers start at 1
                measure_num = int(element.offset / quarters_per_measure) + 1

                # Store chord symbol with measure for analysis
                chordified_symbols_with_measures.append(
                    {
                        "measure": measure_num,
                        "chord": chord_symbol,
                        "offset": element.offset,
                    }
                )

        print(f"DEBUG: Added labels to {labeled_count} chords")
        print(
            f"DEBUG: Collected {len(chordified_symbols_with_measures)} "
            f"chords with measures for analysis"
        )

        return chordified_symbols_with_measures
