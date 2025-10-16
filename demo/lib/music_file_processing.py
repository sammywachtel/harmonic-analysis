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
from harmonic_analysis.core.utils.chord_detection import detect_chord_from_pitches
from harmonic_analysis.core.utils.key_signature import (
    convert_key_signature_to_mode,
    parse_key_signature_from_hint,
)

# Maximum number of measures to include in notation viewer for large files
# (MIDI files can create massive MusicXML that browsers can't handle)
# Reduced to 20 for better OSMD performance with dense piano music
MAX_MEASURES_FOR_DISPLAY = 20


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

    This function provides music21 integration by:
    1. Parsing uploaded files (MusicXML or MIDI)
    2. Optionally using music21's chordify to extract chord reduction
    3. Detecting chords using the library's chord detection
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
        >>> print(result['analysis_result']['primary']['interpretation'])
        'I - vi - IV - V (Functional cadence in C major)'
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

    # Initialize window info
    final_window_size = None  # Will be set if chordify is enabled
    chordified_symbols_with_measures = (
        []
    )  # Will be populated during labeling if chordify+label enabled

    # Big play: chordify and label if requested using library utilities
    if add_chordify:
        from harmonic_analysis.core.utils.analysis_params import (
            calculate_initial_window,
        )

        # Determine analysis window size
        if auto_window:
            # Auto mode: calculate based on tempo
            tempo_bpm = adapter.detect_tempo_from_score(score)
            analysis_window = calculate_initial_window(tempo_bpm)
            print(
                f"DEBUG: AUTO WINDOW MODE - Tempo: {tempo_bpm} BPM → Window: {analysis_window} QL"
            )
        else:
            # Manual mode: use user's setting
            analysis_window = manual_window_size
            print(f"DEBUG: MANUAL WINDOW MODE - User selected: {analysis_window} QL")

        # Store for return value
        final_window_size = analysis_window

        # Use library's chordify_score method
        score = adapter.chordify_score(
            score,
            analysis_window=analysis_window,
            sample_interval=0.25,
            process_full_file=process_full_file,
            max_measures=MAX_MEASURES_FOR_DISPLAY,
        )

        # Use library's label_chords method if requested
        if label_chords:
            chordified_symbols_with_measures = adapter.label_chords(score)

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
        "chordified_symbols_with_measures": chordified_symbols_with_measures,  # Chords with measure info
        "key_hint": key_hint,
        "metadata": metadata,
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
