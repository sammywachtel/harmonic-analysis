"""
Music file processing for MIDI and MusicXML files.

Handles file upload and processing workflow:
- Parse MIDI/MusicXML files using music21
- Detect tempo and calculate analysis window size
- Chordify (extract chord reduction from multi-part scores)
- Label chords with symbols
- Track measures and offsets
- Export to MusicXML and PNG notation
- Integrate with harmonic analysis engine

This module provides the core file processing functions for the demo's
music file upload feature.
"""

from __future__ import annotations

import asyncio
import copy
import io
import os
import shutil
import tempfile
import uuid
import warnings
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from demo.lib.analysis_orchestration import get_service
from demo.lib.chord_detection import (
    detect_chord_from_pitches,
    detect_chord_with_music21,
)
from demo.lib.key_conversion import (
    convert_key_signature_to_mode,
    parse_key_signature_from_hint,
)

# Maximum number of measures to include in notation viewer for large files
# (MIDI files can create massive MusicXML that browsers can't handle)
# Reduced to 20 for better OSMD performance with dense piano music
MAX_MEASURES_FOR_DISPLAY = 20


# ============================================================================
# Tempo Detection
# ============================================================================


def detect_tempo_from_score(score) -> float:
    """
    Detect tempo from score, either from tempo marking or estimated from note density.

    Opening move: Look for explicit tempo markings in the score metadata.
    If none found, estimate tempo based on note density in the opening measures.
    This heuristic helps set appropriate analysis windows even when tempo isn't marked.

    Args:
        score: music21 Score object

    Returns:
        Tempo in BPM (beats per minute). Defaults to 100 if not found.

    Example:
        >>> from music21 import converter
        >>> score = converter.parse('tests/data/test_files/simple_progression.xml')
        >>> tempo = detect_tempo_from_score(score)
        >>> print(f"Detected tempo: {tempo} BPM")
        Detected tempo: 120.0 BPM
    """
    try:
        # First, look for explicit tempo markings
        from music21 import tempo as m21_tempo

        tempo_marks = score.flatten().getElementsByClass(m21_tempo.MetronomeMark)
        if tempo_marks:
            bpm = tempo_marks[0].number
            # Check if bpm is valid (not None)
            if bpm is not None and bpm > 0:
                print(f"DEBUG: Found tempo marking: {bpm} BPM")
                return float(bpm)
            else:
                print(f"DEBUG: Found tempo marking but value is invalid: {bpm}")

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
                f"DEBUG: Estimated tempo from note density: {estimated_bpm} BPM (density={density:.2f} notes/QL)"
            )
            return float(estimated_bpm)

    except Exception as e:
        print(f"DEBUG: Could not detect tempo: {e}")

    # Default fallback
    print("DEBUG: Using default tempo: 100 BPM")
    return 100.0


# ============================================================================
# Window Size Calculation
# ============================================================================


def calculate_initial_window(tempo_bpm: float) -> float:
    """
    Calculate initial analysis window size based on tempo.

    CRITICAL: Returns only musically sensible note values:
        - 0.5 QL = eighth note
        - 1.0 QL = quarter note
        - 2.0 QL = half note
        - 4.0 QL = whole note

    This ensures chord detection windows align with musical phrasing.
    Faster tempos use smaller windows (more frequent changes), while
    slower tempos use larger windows (sustained harmonies).

    Args:
        tempo_bpm: Tempo in beats per minute

    Returns:
        Window size quantized to musical note values

    Tempo guidelines:
        - Very fast (>140 BPM): 1.0 QL (quarter note) - Fast jazz, rapid changes
        - Fast (100-140 BPM): 2.0 QL (half note) - Pop, upbeat classical
        - Moderate (60-100 BPM): 2.0 QL (half note) - Ballads, most classical
        - Slow (<60 BPM): 4.0 QL (whole note) - Slow choral, very sustained

    Example:
        >>> window = calculate_initial_window(120)  # Fast tempo
        >>> print(f"Window size: {window} QL")
        Window size: 2.0 QL
    """
    if tempo_bpm > 140:
        window = 1.0
        category = "Very fast"
        note_name = "quarter note"
    elif tempo_bpm > 100:
        window = 2.0
        category = "Fast"
        note_name = "half note"
    elif tempo_bpm > 60:
        window = 2.0
        category = "Moderate"
        note_name = "half note"
    else:
        window = 4.0
        category = "Slow"
        note_name = "whole note"

    print(
        f"DEBUG: Tempo-based window calculation: {tempo_bpm} BPM → {window} QL = {note_name} ({category})"
    )
    return window


# ============================================================================
# Main File Analysis Function
# ============================================================================


def analyze_uploaded_file(
    file_path: str,
    add_chordify: bool = True,
    label_chords: bool = True,
    run_analysis: bool = False,
    profile: str = "classical",
    process_full_file: bool = False,
    auto_window: bool = True,
    manual_window_size: float = 1.0,
    key_mode_preference: str = "Major",
) -> Dict[str, Any]:
    """
    Process uploaded MusicXML/MIDI file with optional chordify and analysis.

    This function tests the music21 integration by:
    1. Parsing uploaded files (MusicXML or MIDI)
    2. Optionally using music21's chordify to extract chord reduction
    3. Detecting chords and comparing music21 vs chord_logic
    4. Generating PNG notation and MusicXML download
    5. Optionally running harmonic analysis on extracted chords

    Opening move: Validate file and set up parsing with warning capture.
    The file parsing can generate lots of warnings about MIDI import quirks,
    so we filter and present only musically relevant warnings to users.

    Main play: Chordify the score if requested. This is the big one - we use
    adaptive windowing to detect chord changes, then split at measure boundaries
    to match musical notation conventions. Each chord gets labeled with symbols.

    Victory lap: Export the annotated score to MusicXML and optionally run
    harmonic analysis on the extracted chord progression.

    Args:
        file_path: Path to uploaded file (.xml, .mxl, .mid, .midi)
        add_chordify: Whether to add chordify staff to score
        label_chords: Whether to add chord symbol labels
        run_analysis: Whether to run harmonic analysis on chords
        profile: Analysis profile (classical, jazz, pop, etc.)
        process_full_file: Whether to process entire file (vs first 20 measures)
        auto_window: Whether to auto-calculate window size from tempo
        manual_window_size: Manual window size in quarter lengths (if auto_window=False)
        key_mode_preference: "Major" or "Minor" for key signature interpretation

    Returns:
        Dictionary containing:
            - chord_symbols: List of detected chord symbols
            - chordified_symbols_with_measures: Chords with measure numbers
            - key_hint: Detected key signature
            - metadata: File metadata (title, composer, etc.)
            - comparison: List of chord detection comparisons
            - agreement_rate: Percentage agreement between detections
            - notation_url: Path to generated PNG notation
            - download_url: Path to annotated MusicXML file
            - analysis_result: Optional analysis results
            - measure_count: Total measures in score
            - truncated_for_display: Whether notation was truncated
            - is_midi: Flag for MIDI warning display
            - parsing_logs: Parsing logs and warnings
            - window_size_used: Window size used for chord detection

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format unsupported or parsing fails
        RuntimeError: If Lilypond is not installed (required for PNG generation)

    Example:
        >>> result = analyze_uploaded_file(
        ...     'tests/data/test_files/simple_progression.xml',
        ...     add_chordify=True,
        ...     label_chords=True,
        ...     run_analysis=True
        ... )
        >>> print(result['chord_symbols'])
        ['C', 'Am', 'F', 'G']
        >>> print(result['agreement_rate'])
        0.95
    """
    # Opening move: import music21 integration and check file exists
    # Capture warnings during file parsing
    from harmonic_analysis.integrations.music21_adapter import Music21Adapter

    parsing_logs = []
    is_midi = False

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in [".xml", ".mxl", ".mid", ".midi"]:
        raise ValueError(
            f"Unsupported file format: {file_ext}. "
            "Expected .xml, .mxl, .mid, or .midi"
        )

    # Track if this is a MIDI file
    is_midi = file_ext in [".mid", ".midi"]

    # Main play: parse the file using Music21Adapter with warning capture
    adapter = Music21Adapter()

    # Capture Python warnings and music21 output during parsing
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")

        if file_ext in [".xml", ".mxl"]:
            parsing_logs.append(
                f"📄 Parsing MusicXML file: {os.path.basename(file_path)}"
            )
            data = adapter.from_musicxml(file_path)
            parsing_logs.append("✅ MusicXML file parsed successfully")
        else:  # .mid or .midi
            parsing_logs.append(f"🎹 Parsing MIDI file: {os.path.basename(file_path)}")
            parsing_logs.append("⚠️  Note: MIDI → notation conversion is approximate")
            data = adapter.from_midi(file_path)
            parsing_logs.append("✅ MIDI file parsed")

        # Collect any warnings that occurred (filter out irrelevant ones)
        if caught_warnings:
            # Filter warnings - only show music21 and file-parsing related warnings
            irrelevant_categories = {"ResourceWarning", "DeprecationWarning"}
            irrelevant_keywords = {"unclosed event loop", "coroutine", "asyncio"}

            relevant_warnings = []
            for w in caught_warnings:
                warning_msg = str(w.message)
                # Skip if warning category is irrelevant
                if w.category.__name__ in irrelevant_categories:
                    # Check if message contains music-related content
                    if not any(
                        keyword in warning_msg.lower()
                        for keyword in [
                            "music",
                            "note",
                            "chord",
                            "measure",
                            "staff",
                            "voice",
                        ]
                    ):
                        continue
                # Skip if message contains irrelevant keywords
                if any(
                    keyword in warning_msg.lower() for keyword in irrelevant_keywords
                ):
                    continue

                # Truncate very long warnings
                if len(warning_msg) > 200:
                    warning_msg = warning_msg[:200] + "..."
                relevant_warnings.append(f"  • {w.category.__name__}: {warning_msg}")

            # Only add warning section if we have relevant warnings
            if relevant_warnings:
                parsing_logs.append(
                    f"\n⚠️  {len(relevant_warnings)} warning(s) during parsing:"
                )
                parsing_logs.extend(relevant_warnings)

    score = data["score_object"]
    chord_symbols = data["chord_symbols"]
    key_hint = data["key_hint"]
    metadata = data["metadata"]

    # Convert key signature to major or minor based on user preference
    # This ensures analysis uses the correct tonal center (e.g., B minor vs D major for 2 sharps)
    if key_hint and run_analysis:
        sharps_flats = parse_key_signature_from_hint(key_hint)
        prefer_minor = key_mode_preference == "Minor"
        converted_key = convert_key_signature_to_mode(sharps_flats, prefer_minor)
        print(
            f"DEBUG: Key conversion - Original: {key_hint}, Preference: {key_mode_preference}, Converted: {converted_key}"
        )
        key_hint_for_analysis = converted_key
    else:
        key_hint_for_analysis = key_hint

    # Initialize comparison tracking and window info
    comparison: List[Dict[str, Any]] = []
    final_window_size = None  # Will be set if chordify is enabled
    chordified_symbols_with_measures = (
        []
    )  # Will be populated during labeling if chordify+label enabled

    # Big play: chordify and label if requested
    if add_chordify:
        # Adaptive windowing based on harmonic change detection
        # Use fine-grained sampling + intelligent merging when harmony is stable
        from music21 import chord as m21_chord
        from music21 import clef, key
        from music21 import note as m21_note
        from music21 import stream

        # Create chord staff with adaptive windowing
        chordified = stream.Part()
        chordified.partName = "Chord Analysis"

        # Set bass clef for chord analysis staff (chord symbols typically in bass register)
        bass_clef = clef.BassClef()
        chordified.insert(0, bass_clef)
        print("DEBUG: Set bass clef for chord analysis staff")

        # Copy key signature from original score (important: chord staff should match original key)
        try:
            original_key = score.flatten().getElementsByClass("KeySignature")[0]
            print(f"DEBUG: Found original key signature: {original_key.sharps} sharps")
            # Create a NEW KeySignature object to avoid reference issues
            key_copy = key.KeySignature(original_key.sharps)
            print(f"DEBUG: Created new key signature copy: {key_copy.sharps} sharps")
            chordified.insert(0, key_copy)
            print(f"DEBUG: ✓ Inserted key signature into chord staff at offset 0")
        except (IndexError, AttributeError) as e:
            print(f"DEBUG: No key signature found in original score: {e}")

        # CRITICAL: Copy time signature from original score (prevents Dorico signpost issues)
        try:
            from music21 import meter

            original_time = score.flatten().getElementsByClass("TimeSignature")[0]
            # Create a new TimeSignature object to avoid reference issues
            time_sig_copy = meter.TimeSignature(
                f"{original_time.numerator}/{original_time.denominator}"
            )
            chordified.insert(0, time_sig_copy)
            print(
                f"DEBUG: Copied time signature to chord staff: {original_time.numerator}/{original_time.denominator}"
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
        if measure_count > MAX_MEASURES_FOR_DISPLAY and not process_full_file:
            # Calculate duration of first N measures
            try:
                time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
                quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
            except (IndexError, AttributeError):
                quarters_per_measure = 4.0

            total_duration = MAX_MEASURES_FOR_DISPLAY * quarters_per_measure
            print(
                f"DEBUG: Large file detected - limiting chordify to first {MAX_MEASURES_FOR_DISPLAY} measures ({total_duration} QL instead of {full_duration} QL)"
            )
            print(
                f"       💡 Tip: Enable 'Process Full File' option to include all measures in download"
            )
        else:
            total_duration = full_duration
            if measure_count > MAX_MEASURES_FOR_DISPLAY:
                print(
                    f"DEBUG: Processing full file ({measure_count} measures, {full_duration} QL) - this will take 1-2 minutes"
                )

        # Sample at fine intervals (16th notes) to detect all changes
        sample_interval = 0.25  # Quarter note / 4 = 16th note

        # Determine analysis window size
        if auto_window:
            # Auto mode: calculate based on tempo
            tempo_bpm = detect_tempo_from_score(score)
            initial_window = calculate_initial_window(tempo_bpm)
            analysis_window = initial_window
            print(
                f"DEBUG: AUTO WINDOW MODE - Tempo: {tempo_bpm} BPM → Window: {analysis_window} QL"
            )
        else:
            # Manual mode: use user's setting
            analysis_window = manual_window_size
            print(f"DEBUG: MANUAL WINDOW MODE - User selected: {analysis_window} QL")

        # Store for return value
        final_window_size = analysis_window

        print(
            f"DEBUG: Using adaptive windowing (sample={sample_interval}QL, window={analysis_window}QL)"
        )

        # First pass: collect pitch sets at each sample point
        samples = []
        current_offset = 0.0
        total_samples = int(total_duration / sample_interval)

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
        merged_regions = []

        if samples:
            i = 0
            total_windows = len(samples)
            windows_processed = 0

            while i < len(samples):
                # Look ahead: collect all notes within the next analysis_window
                window_start = samples[i]["offset"]
                window_end = window_start + analysis_window

                # Accumulate all pitch classes in this window
                window_pitch_classes = set()
                window_pitches = []
                window_samples = 0

                # Collect samples within this window
                j = i
                while j < len(samples) and samples[j]["offset"] < window_end:
                    window_pitch_classes |= samples[j]["pitch_classes"]
                    window_pitches.extend(samples[j]["pitches"])
                    window_samples += 1
                    j += 1

                windows_processed += 1

                if window_pitch_classes:
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
            f"DEBUG: Merged into {len(merged_regions)} harmonic regions via sliding windows"
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
            f"DEBUG: Split into {len(measure_aware_regions)} measure-aware regions (respecting barlines)"
        )

        # DEBUG: Show how many chords per measure
        chords_per_measure = {}
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
                window_chord = m21_chord.Chord(unique_pitches)
                window_chord.quarterLength = region["duration"]
                # CRITICAL: Set voice to 1 to prevent MusicXML export warnings
                # Missing voice tags cause Dorico to misinterpret the entire score
                window_chord.voice = 1
                chordified.insert(region["start"], window_chord)

        print(
            f"DEBUG: Created {len(chordified.flatten().notesAndRests)} adaptive chords"
        )

        # Note: We intentionally do NOT call makeMeasures() here
        # music21 will auto-generate measures during MusicXML export
        # Calling makeMeasures() can corrupt the measure structure of the entire score

        # Critical fix: Rebuild score with proper part order
        # Chord staff should appear at BOTTOM (traditional lead sheet style)
        from music21 import instrument, layout, stream

        # Save original parts
        original_parts = list(score.parts)

        # Create new score with metadata preserved
        new_score = stream.Score()
        if score.metadata:
            new_score.metadata = score.metadata

        # Add original parts FIRST (top staves)
        # CRITICAL: Deep copy parts to avoid music21 export modifying them in place
        copied_parts = []
        for part in original_parts:
            new_part = copy.deepcopy(part)
            new_score.append(new_part)
            copied_parts.append(new_part)

        # Create a staff group for the original parts (to keep them visually separate from chord analysis)
        if len(copied_parts) > 0:
            # StaffGroup keeps original parts together with bracket
            original_group = layout.StaffGroup(
                copied_parts, name="Original", symbol="bracket"
            )
            new_score.insert(0, original_group)

        # CRITICAL: Set explicit instrument to prevent auto-grouping with piano parts
        # Use a generic instrument to mark this as completely separate
        chord_instrument = instrument.Instrument()
        chord_instrument.instrumentName = "Chord Analysis"
        chord_instrument.instrumentAbbreviation = "Ch."
        chordified.insert(0, chord_instrument)
        print("DEBUG: Set explicit instrument for chord staff to prevent auto-grouping")

        # Add chordified LAST as a completely separate part (no staff group, separate instrument)
        new_score.append(chordified)

        # Replace score
        score = new_score

        print(
            f"DEBUG: Score rebuilt with {len(score.parts)} parts (chord staff as separate instrument at bottom)"
        )

        if label_chords:
            # For each chord in chordified staff, detect and label
            # Need to iterate through the actual chordified part in the score
            chord_part = new_score.parts[-1]  # Last part is chord analysis
            labeled_count = 0

            # Get time signature to calculate measure numbers from offsets
            # Assume 4/4 time if not specified (4 quarter notes per measure)
            try:
                time_sig = score.flatten().getElementsByClass("TimeSignature")[0]
                quarters_per_measure = time_sig.numerator * (4.0 / time_sig.denominator)
            except (IndexError, AttributeError):
                quarters_per_measure = 4.0  # Default to 4/4 time

            print(
                f"DEBUG: Calculating measures with {quarters_per_measure} quarters per measure"
            )

            for element in chord_part.flatten().notesAndRests:
                if element.isChord:
                    # music21's enhanced chord detection with sus4/add4 support
                    try:
                        m21_symbol = detect_chord_with_music21(element)
                    except (AttributeError, Exception) as e:
                        print(f"DEBUG: music21 detection failed: {e}")
                        m21_symbol = "Unknown"

                    # Our detection: extract pitches and detect chord using legacy chord_parser logic
                    try:
                        # Get MIDI pitch numbers from the chord
                        pitches = [p.midi for p in element.pitches]
                        our_symbol = detect_chord_from_pitches(pitches)
                    except (AttributeError, Exception) as e:
                        print(f"DEBUG: chord_logic detection failed: {e}")
                        our_symbol = "Unknown"

                    # Add our labels to the score as lyrics (below staff)
                    element.addLyric(our_symbol)
                    labeled_count += 1

                    # Calculate measure number from offset
                    # Measure numbers start at 1
                    measure_num = int(element.offset / quarters_per_measure) + 1

                    # Store chord symbol with measure for analysis
                    chordified_symbols_with_measures.append(
                        {
                            "measure": measure_num,
                            "chord": our_symbol,
                            "offset": element.offset,
                        }
                    )

                    comparison.append(
                        {
                            "measure": measure_num,
                            "music21": m21_symbol,
                            "chord_logic": our_symbol,
                            "match": "✓" if m21_symbol == our_symbol else "✗",
                        }
                    )

            print(f"DEBUG: Added labels to {labeled_count} chords")
            print(
                f"DEBUG: Collected {len(chordified_symbols_with_measures)} chords with measures for analysis"
            )

    # Generate output files
    # We need TWO files:
    # 1. notation_xml - for OSMD viewer (always truncated to 20 measures)
    # 2. download_xml - for download (full file if requested, preview otherwise)
    temp_dir = tempfile.gettempdir()
    file_uuid = str(uuid.uuid4())

    notation_xml_path = os.path.join(
        temp_dir, f"notation_{file_uuid}.xml"
    )  # For viewer
    download_xml_path = os.path.join(
        temp_dir, f"download_{file_uuid}.xml"
    )  # For download

    # Strip tempo markings to avoid OSMD parsing errors
    # OSMD 1.8.6 has bugs with TempoExpressions
    from music21 import tempo

    removed_count = 0

    # Iterate through all parts and recursively remove tempo elements
    for part in score.parts:
        # Collect tempo elements to remove (can't remove while iterating)
        tempo_elements = []
        for element in part.recurse():
            if isinstance(
                element,
                (tempo.TempoIndication, tempo.MetronomeMark, tempo.MetricModulation),
            ):
                tempo_elements.append(element)

        # Remove collected tempo elements
        for tempo_elem in tempo_elements:
            try:
                # Get the container (measure or part)
                container = tempo_elem.activeSite
                if container:
                    container.remove(tempo_elem)
                    removed_count += 1
            except Exception as e:
                print(f"DEBUG: Could not remove tempo element: {e}")

    if removed_count > 0:
        print(f"DEBUG: Removed {removed_count} tempo markings for OSMD compatibility")
    else:
        print("DEBUG: No tempo markings found to remove")

    # Debug: Check score structure before export
    part_count = len(score.parts) if hasattr(score, "parts") else 0

    # Count measures correctly - check the parts, not flattened score
    # (flattened scores lose measure structure in music21)
    measure_count = 0
    if part_count > 0:
        # Get max measure count from any part
        measure_count = max(
            len(part.getElementsByClass("Measure")) for part in score.parts
        )

    print(
        f"DEBUG: Score structure - {part_count} parts, {measure_count} measures (max in any part)"
    )

    if part_count == 0:
        print("WARNING: Score has no parts! This may cause export issues.")

    # For large MIDI files, create a separate preview for notation viewer
    # while keeping full score for download when requested
    # (MIDI files often generate huge MusicXML that OSMD can't handle)
    notation_score = score  # Default: use full score

    if measure_count > MAX_MEASURES_FOR_DISPLAY:
        print(
            f"DEBUG: Large score detected ({measure_count} measures). Creating preview with first {MAX_MEASURES_FOR_DISPLAY} measures for notation viewer."
        )

        # Create a truncated copy using music21's measure extraction
        # This preserves more context than manual copying
        from music21 import stream

        try:
            # Manual measure extraction is more reliable than score.measures()
            # because it avoids broken activeSite references
            notation_score = stream.Score()
            if score.metadata:
                # CRITICAL: Create a COPY of metadata to avoid modifying original score's metadata
                notation_score.metadata = copy.deepcopy(score.metadata)

            # Set a better title if not present (music21 defaults to "Music21 Fragment")
            if (
                not notation_score.metadata
                or not notation_score.metadata.title
                or notation_score.metadata.title == "Music21 Fragment"
            ):
                filename = os.path.basename(file_path)
                notation_score.metadata.title = (
                    f"{filename} (First {MAX_MEASURES_FOR_DISPLAY} Measures)"
                )

            truncated_parts = 0
            for original_part in score.parts:
                measures = original_part.getElementsByClass("Measure")

                if measures and len(measures) > 0:
                    # Part has explicit measures (normal case)
                    new_part = stream.Part()

                    # Copy part attributes
                    if hasattr(original_part, "partName"):
                        new_part.partName = original_part.partName
                    if hasattr(original_part, "id"):
                        new_part.id = original_part.id

                    # Copy first N measures (creates fresh copies, avoiding activeSite issues)
                    for measure in measures[:MAX_MEASURES_FOR_DISPLAY]:
                        # Deep copy the measure to break old references
                        new_measure = copy.deepcopy(measure)
                        new_part.append(new_measure)

                    notation_score.append(new_part)
                    truncated_parts += 1
                else:
                    # Part has no measures (e.g., chordified staff) - use offset-based slicing
                    # Calculate end offset for first N measures based on time signature
                    try:
                        time_sig = score.flatten().getElementsByClass("TimeSignature")[
                            0
                        ]
                        quarters_per_measure = time_sig.numerator * (
                            4.0 / time_sig.denominator
                        )
                    except (IndexError, AttributeError):
                        quarters_per_measure = 4.0  # Default to 4/4

                    max_offset = MAX_MEASURES_FOR_DISPLAY * quarters_per_measure

                    # Extract elements within offset range
                    new_part = stream.Part()
                    if hasattr(original_part, "partName"):
                        new_part.partName = original_part.partName
                    if hasattr(original_part, "id"):
                        new_part.id = original_part.id

                    # CRITICAL: Copy key signature, time signature, clef from original part
                    # These are at offset 0 and must be preserved
                    for element in original_part.getElementsByOffset(0):
                        # Check if element has isNote attribute (not all elements do, e.g., Instrument)
                        if not hasattr(element, "isNote") or (
                            not element.isNote and not element.isRest
                        ):
                            # Copy non-note elements at offset 0 (clef, key sig, time sig, etc.)
                            new_part.insert(0, copy.deepcopy(element))

                    # Copy notes and rests within the excerpt range
                    for element in original_part.flatten().notesAndRests:
                        if element.offset < max_offset:
                            new_element = copy.deepcopy(element)
                            new_part.insert(element.offset, new_element)

                    if len(new_part.flatten().notesAndRests) > 0:
                        notation_score.append(new_part)
                        truncated_parts += 1
                        print(
                            f"DEBUG: Included offset-based part '{new_part.partName}' with {len(new_part.flatten().notesAndRests)} elements"
                        )

            if truncated_parts > 0:
                print(
                    f"DEBUG: ✓ Created excerpt with {truncated_parts} parts, first {MAX_MEASURES_FOR_DISPLAY} measures each"
                )
            else:
                print(f"DEBUG: Truncation failed, using full score as fallback")
                notation_score = score

        except Exception as e:
            print(f"WARNING: Could not create excerpt: {e}. Using full score.")
            import traceback

            traceback.print_exc()
            notation_score = score

    # Decision: Which score to export for download?
    # - If process_full_file=True: Export full score (all measures with chords)
    # - Otherwise: Export truncated score (first 20 measures for quick preview)
    if process_full_file:
        download_score = score  # Full score with all processing
        print(
            f"DEBUG: Full file processing enabled - download will contain all {measure_count} measures"
        )

        # Set a better title for full download file
        # CRITICAL: Ensure we have metadata object, and fix title if it's missing or wrong
        if not download_score.metadata:
            from music21 import metadata as m21_metadata

            download_score.metadata = m21_metadata.Metadata()

        filename = os.path.basename(file_path)

        # Always set proper title for full file (it may have "First 20 Measures" from earlier operations)
        if (
            not download_score.metadata.title
            or download_score.metadata.title == "Music21 Fragment"
            or "First" in str(download_score.metadata.title)
        ):
            download_score.metadata.title = (
                f"{filename} (Full - {measure_count} Measures)"
            )
            print(f"DEBUG: Set download title to: {download_score.metadata.title}")
    else:
        download_score = notation_score  # Truncated preview
        print(
            f"DEBUG: Preview mode - download will contain first {MAX_MEASURES_FOR_DISPLAY} measures"
        )

    # Export TWO MusicXML files:
    # 1. Notation file (for OSMD viewer) - always truncated for browser performance
    # 2. Download file (for user) - full or preview depending on checkbox

    # Export notation file (for OSMD viewer)
    try:
        # CRITICAL: Skip makeNotation() and deepcopy to preserve original notation
        # makeNotation() recalculates durations and corrupts the piano parts
        print(
            "DEBUG: Exporting notation file without makeNotation() to preserve MIDI notation"
        )
        notation_score.write("musicxml", fp=notation_xml_path)

        if os.path.exists(notation_xml_path):
            file_size = os.path.getsize(notation_xml_path)
            print(
                f"DEBUG: ✓ Exported notation MusicXML for viewer: {notation_xml_path} ({file_size:,} bytes)"
            )
        else:
            print(
                f"ERROR: Notation MusicXML file was not created at {notation_xml_path}"
            )

    except Exception as e:
        print(f"ERROR: Failed to export notation MusicXML: {e}")
        import traceback

        traceback.print_exc()

    # Export download file (full or preview based on checkbox)
    try:
        # CRITICAL: Skip makeNotation() to preserve original notation
        # makeNotation() recalculates durations and corrupts the piano parts
        # The original MIDI-imported notation is already correct
        print("DEBUG: Skipping makeNotation() to preserve original MIDI notation")
        download_export_score = download_score

        # Try to write MusicXML (export chosen score - full or preview)
        download_export_score.write("musicxml", fp=download_xml_path)

        # Verify export was successful
        if os.path.exists(download_xml_path):
            file_size = os.path.getsize(download_xml_path)
            print(
                f"DEBUG: ✓ Exported download MusicXML: {download_xml_path} ({file_size:,} bytes)"
            )

            # Validate the MusicXML file
            try:
                print("DEBUG: Validating MusicXML file...")
                from music21 import converter

                # Try to parse it back - if it's valid, this should work
                validation_score = converter.parse(download_xml_path)
                part_count = (
                    len(validation_score.parts)
                    if hasattr(validation_score, "parts")
                    else 0
                )
                print(
                    f"DEBUG: ✓ MusicXML validation passed - {part_count} parts parsed successfully"
                )

            except Exception as e:
                print(f"WARNING: MusicXML validation failed: {e}")
                print(
                    f"         The file may not import correctly into some notation software"
                )
                import traceback

                traceback.print_exc()

            if file_size == 0:
                print(
                    f"ERROR: Download MusicXML file is empty! Score may have no content."
                )
            elif file_size > 10_000_000:  # 10MB
                print(
                    f"WARNING: Download MusicXML file is very large ({file_size:,} bytes)."
                )
        else:
            print(
                f"ERROR: Download MusicXML file was not created at {download_xml_path}"
            )

    except Exception as e:
        print(f"ERROR: Failed to export MusicXML: {e}")
        print(f"ERROR: Score type: {type(score)}, Has parts: {hasattr(score, 'parts')}")
        import traceback

        traceback.print_exc()

        # Create a minimal error placeholder file
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Error</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>whole</type></note>
    </measure>
  </part>
</score-partwise>"""
        with open(download_xml_path, "w") as f:
            f.write(error_xml)
        print(f"DEBUG: Created placeholder MusicXML file due to export error")

    # Calculate agreement rate
    agreement_rate = 0.0
    if comparison:
        matches = sum(1 for c in comparison if c["match"] == "✓")
        agreement_rate = matches / len(comparison)

    # Optional: run harmonic analysis
    # CRITICAL: Use chordified symbols if available, otherwise fall back to original
    analysis_result = None
    analysis_chord_data = None  # Will contain chord symbols with measure numbers

    if run_analysis:
        # Use chordified symbols if we created them, otherwise use original
        if chordified_symbols_with_measures:
            analysis_chords = [
                item["chord"] for item in chordified_symbols_with_measures
            ]
            analysis_chord_data = chordified_symbols_with_measures
        elif chord_symbols:
            analysis_chords = chord_symbols
            analysis_chord_data = [
                {"measure": i + 1, "chord": c, "offset": None}
                for i, c in enumerate(chord_symbols)
            ]
        else:
            analysis_chords = []

        if analysis_chords:
            service = get_service()
            try:
                analysis_result = asyncio.run(
                    service.analyze_with_patterns_async(
                        chord_symbols=analysis_chords,
                        key_hint=key_hint_for_analysis,  # Use converted key based on user preference
                        profile=profile,
                    )
                )
            except Exception as e:
                warnings.warn(f"Analysis failed: {e}", UserWarning)

    # Victory lap: return comprehensive results
    return {
        "chord_symbols": chord_symbols,
        "chordified_symbols_with_measures": chordified_symbols_with_measures,  # NEW: chords with measure info
        "key_hint": key_hint,
        "metadata": metadata,
        "comparison": comparison,
        "agreement_rate": agreement_rate,
        "notation_url": notation_xml_path,  # MusicXML file for OSMD viewer (always 20 measures)
        "download_url": download_xml_path,  # MusicXML file for download (full or preview)
        "analysis_result": asdict(analysis_result) if analysis_result else None,
        "measure_count": measure_count,  # Total measures in score
        "truncated_for_display": measure_count
        > MAX_MEASURES_FOR_DISPLAY,  # Whether notation was truncated
        "is_midi": is_midi,  # Flag for MIDI warning display
        "parsing_logs": (
            "\n".join(parsing_logs) if parsing_logs else None
        ),  # Parsing logs and warnings
        "window_size_used": final_window_size,  # Window size used for chord detection (None if no chordify)
    }
