"""Public audio adapter — entry points for analyzing audio files.

This is the user-facing surface of the audio pipeline:

* ``AudioAdapter`` — orchestrates ``audio/_io.py`` (chroma extraction) and
  the WU1 audio core (``_key_estimation``, ``_cadence``, ``_region``).
* ``AudioAnalysisResult`` — frozen dataclass returned to callers.
* ``ChordEvent`` — placeholder type for WU3's chord transcription. The
  ``chords`` field on ``AudioAnalysisResult`` is always ``[]`` until WU3
  ships; the docstring says so explicitly so nobody panics.
* ``analyze_audio`` / ``analyze_audio_async`` — module-level convenience
  wrappers. The async variant uses ``asyncio.to_thread`` to keep the
  blocking librosa work off the event loop.

Lazy import semantics
---------------------
Importing this module only fails if librosa or soundfile are missing AND
you actually try to instantiate ``AudioAdapter`` or call ``analyze_audio``.
The module itself is import-safe; the audio deps are checked inside
``AudioAdapter.__init__``. This is the same pattern as ``music21_adapter``
but without the print-to-stderr debug calls (those are pre-existing
anti-patterns in that module — we use ``logging`` instead).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Type alias for filepath args.
PathLike = Union[str, Path]


class AudioImportError(ImportError):
    """Raised when ``librosa`` or ``soundfile`` are not installed.

    The message includes the literal strings ``"audio"`` and ``"pip install"``
    so downstream callers can grep for them when surfacing actionable
    install guidance to users. Subclass of ``ImportError`` so existing
    ``except ImportError:`` blocks still catch it.
    """

    pass


@dataclass(frozen=True)
class ChordEvent:
    """Placeholder for a single chord event in time.

    WU3 will populate this field with real chord transcription data
    (root, quality, onset, duration, confidence). Until then, the
    ``AudioAnalysisResult.chords`` field is intentionally an empty list,
    and this dataclass exists only to give mypy something concrete to
    check against ``list[ChordEvent]``.

    A bare ``Any`` would silently pass the type checker and hide the WU3
    handoff seam from grep — explicit stub is better than implicit hole.
    """

    symbol: str


@dataclass(frozen=True)
class AudioAnalysisResult:
    """Result of an end-to-end audio analysis pass.

    Attributes:
        global_key: Krumhansl-Schmuckler key estimate over the whole file.
        local_key: Krumhansl-Schmuckler key estimate over the analyzed
            segment. Equal to ``global_key`` semantics-wise when no
            segment is specified, but computed from a different chroma
            slice.
        cadences: V-I cadence detection result for the segment.
        region: Region classification (stable / modulation / modal_shift)
            comparing the local segment against the global key.
        chords: WU3 will populate this; until then this is intentionally
            empty. ``chords_as_symbols()`` returns ``[]`` to match.
        segment_start: Start of the analyzed segment in seconds. ``0.0``
            when no segment was specified.
        segment_end: End of the analyzed segment in seconds. Equal to
            file duration when no segment was specified.

    The ``key_hint`` derived property formats ``"<tonic> <mode>"`` from
    the local key, in a form compatible with
    ``PatternAnalysisService.analyze_with_patterns_async(key_hint=...)``.
    """

    global_key: object  # KeyInfo — quoting to keep this module import-safe
    local_key: object  # KeyInfo
    cadences: object  # CadenceInfo
    region: object  # RegionInfo
    segment_start: float
    segment_end: float
    chords: list[ChordEvent] = field(default_factory=list)

    @property
    def key_hint(self) -> str:
        """Service-ready key hint string of the form ``"<tonic> <mode>"``.

        The mode comes from K-S as ``"Ionian"`` / ``"Aeolian"`` /
        ``"N/A"``; we map the K-S labels to the standard mode names that
        ``PatternAnalysisService`` accepts (``"major"`` / ``"minor"`` /
        ``"dorian"`` / etc.). Anything unrecognized falls through to
        ``"major"`` rather than raising — a key hint is informational, not
        a hard contract, and a wrong-but-plausible label beats a crash.

        Returns:
            String matching the regex
            ``^[A-G][#b]? (major|minor|dorian|phrygian|lydian|mixolydian|``
            ``aeolian|locrian)$``.
            Never empty for a well-formed local key; ``"C major"`` for a
            zero-energy ``"N/A"`` sentinel.
        """
        # Avoid importing KeyInfo at module-eval time — work at runtime.
        tonic = getattr(self.local_key, "tonic", "C")
        mode = getattr(self.local_key, "mode", "Ionian")

        # K-S returns Ionian/Aeolian; the service expects major/minor/etc.
        # Map the labels we know; pass through anything that's already a
        # standard mode name; default to "major" for the N/A sentinel.
        mode_lower = str(mode).lower()
        mode_map = {
            "ionian": "major",
            "aeolian": "minor",
            "major": "major",
            "minor": "minor",
            "dorian": "dorian",
            "phrygian": "phrygian",
            "lydian": "lydian",
            "mixolydian": "mixolydian",
            "locrian": "locrian",
        }
        mapped_mode = mode_map.get(mode_lower, "major")

        # N/A sentinel — emit a defensible default rather than the
        # literal "N/A" which wouldn't match the regex.
        if tonic == "N/A":
            return "C major"
        return f"{tonic} {mapped_mode}"

    def chords_as_symbols(self) -> list[str]:
        """Return ``self.chords`` as a list of plain symbol strings.

        WU3 will populate ``self.chords``; until then this returns ``[]``.
        Keeping the method here (rather than inlining
        ``[c.symbol for c in result.chords]`` at every call site) gives
        WU3 a single migration point when the real data lands.

        Returns:
            ``list[str]`` of chord symbols. Always ``[]`` in WU2.
        """
        return [c.symbol for c in self.chords]


class AudioAdapter:
    """Orchestrates audio I/O + WU1 audio core into a single analysis call.

    Construction is the lazy-import boundary: librosa and soundfile are
    imported inside ``__init__``; if either is missing,
    ``AudioImportError`` is raised with actionable install guidance.
    Construction also runs an ffmpeg presence check and emits a single
    WARNING log if ffmpeg isn't on PATH (because then MP3/AAC/OGG decoding
    will fail at use-time, but WAV still works fine).

    Use the module-level ``analyze_audio`` / ``analyze_audio_async``
    helpers if you don't need to keep the adapter instance around.

    Attributes:
        ffmpeg_available: ``True`` if ``ffmpeg`` was found on PATH at
            construction time.

    Raises:
        AudioImportError: If librosa or soundfile is missing.
    """

    def __init__(self, *, quiet: bool = False) -> None:
        """Initialize the adapter.

        Args:
            quiet: When ``True``, suppresses the ffmpeg-missing WARNING
                log. Useful for test fixtures that want to avoid log-leak
                noise. Defaults to ``False``.

        Raises:
            AudioImportError: If ``librosa`` or ``soundfile`` cannot be
                imported. Message contains ``"audio"`` and
                ``"pip install"`` for grep-friendly install guidance.
        """
        # Lazy import — keeps `import harmonic_analysis` lean. We don't
        # store the modules on self because _io.py imports them directly;
        # we only need to confirm they're present.
        try:
            import librosa  # noqa: F401  # presence check only
            import soundfile  # noqa: F401  # presence check only
        except ImportError as exc:
            raise AudioImportError(
                "The audio extra is required for AudioAdapter. "
                "Install with: pip install harmonic-analysis[audio]"
            ) from exc

        # Now that deps are known-good, the lazy `audio/_io.py` import is
        # safe — it imports librosa/soundfile at module top.
        from harmonic_analysis.audio._io import check_ffmpeg_available

        self.ffmpeg_available: bool = check_ffmpeg_available()

        if not quiet and not self.ffmpeg_available:
            # Single WARNING — informational, not a fail. WAV still works.
            # Message contains "ffmpeg" + a format hint per AC9.
            logger.warning(
                "ffmpeg not found on PATH. WAV files will analyze fine, but "
                "MP3, AAC, and OGG decoding will fail at use-time. Install "
                "ffmpeg via your package manager (Homebrew: `brew install "
                "ffmpeg`; apt: `apt install ffmpeg`)."
            )

    def from_audio(
        self,
        filepath: PathLike,
        *,
        segment: Optional[Tuple[float, Optional[float]]] = None,
    ) -> AudioAnalysisResult:
        """Run the full audio analysis pipeline on a file.

        Pipeline:
            1. Extract global chroma (1D ``(12,)``) → estimate global key.
            2. Resolve segment bounds (default: whole file).
            3. Extract local chroma (2D ``(12, T)``) for the segment.
            4. Estimate local key from the time-averaged local chroma.
            5. Detect cadences from the raw 2D local chroma.
            6. Classify region against the global key.

        Args:
            filepath: Path to an audio file (WAV directly; MP3/AAC/OGG
                via ffmpeg).
            segment: Optional ``(start_sec, end_sec)`` window. ``end_sec``
                may be ``None`` to mean "to end of file." When omitted,
                the analyzed segment is the whole file.

        Returns:
            ``AudioAnalysisResult`` with global + local keys, cadences,
            region, segment bounds, and an empty ``chords`` list (WU3
            populates that).

        Raises:
            ValueError: Surfaced from ``audio/_io.py`` for empty / too-short
                segments.
            RuntimeError: Surfaced from soundfile/librosa for unreadable
                files.
        """
        # Imports are inside the method on purpose — keeps the module
        # import-safe even when audio deps are absent at module load time.
        # By the time we reach this method, __init__ has already verified
        # librosa + soundfile are importable.
        from harmonic_analysis.audio._cadence import detect_cadences
        from harmonic_analysis.audio._io import (
            extract_global_chroma,
            extract_local_chroma,
        )
        from harmonic_analysis.audio._key_estimation import find_best_key
        from harmonic_analysis.audio._region import classify_region_type

        # Step 1 — global chroma + global key. Already 1D (12,) per the
        # _io.py contract; pass directly to find_best_key.
        global_chroma = extract_global_chroma(filepath)
        global_key = find_best_key(global_chroma)

        # Step 2 — resolve segment bounds. Default: whole file. We need
        # to know file duration up front to fill in segment_end when no
        # segment is supplied.
        import soundfile as sf

        with sf.SoundFile(str(filepath), "r") as f:
            file_duration_sec = len(f) / float(f.samplerate)

        if segment is None:
            resolved_start = 0.0
            resolved_end = file_duration_sec
        else:
            resolved_start = float(segment[0])
            requested_end = segment[1]
            if requested_end is None or requested_end > file_duration_sec:
                resolved_end = file_duration_sec
            else:
                resolved_end = float(requested_end)

        # Step 3 — local chroma. 2D (12, T) per _io.py contract.
        local_chroma = extract_local_chroma(
            filepath, start_time=resolved_start, end_time=resolved_end
        )

        # Step 4 — local key. find_best_key expects 1D 12-bin;
        # detect_cadences expects 2D (12,T) raw — see WU2 prepare doc.
        # (12,T) → (12,) required by find_best_key; averaging done here,
        # not in the estimator.
        local_chroma_1d = local_chroma.mean(axis=1)
        local_key = find_best_key(local_chroma_1d)

        # Step 5 — cadences. Pass the full 2D matrix; detect_cadences
        # does its own .mean(axis=1) internally.
        cadences = detect_cadences(local_chroma, local_key)

        # Step 6 — region classification. Threshold tuning lives in
        # _region.py and is not our concern here.
        region = classify_region_type(
            global_key=global_key,
            local_key=local_key,
            local_key_confidence=local_key.confidence,
            local_cadence=cadences,
        )

        return AudioAnalysisResult(
            global_key=global_key,
            local_key=local_key,
            cadences=cadences,
            region=region,
            segment_start=resolved_start,
            segment_end=resolved_end,
            chords=[],
        )


def analyze_audio(
    filepath: PathLike,
    *,
    segment: Optional[Tuple[float, Optional[float]]] = None,
    quiet: bool = False,
) -> AudioAnalysisResult:
    """Synchronous convenience wrapper around ``AudioAdapter.from_audio``.

    Use this when you don't need the adapter instance (most callers).
    Constructs a fresh ``AudioAdapter`` per call — cheap, the only real
    work in ``__init__`` is the ffmpeg-on-PATH check.

    Args:
        filepath: Path to an audio file.
        segment: Optional ``(start_sec, end_sec)`` window;
            ``end_sec`` may be ``None``.
        quiet: Suppresses the ffmpeg-missing WARNING when ``True``.

    Returns:
        ``AudioAnalysisResult``.

    Raises:
        AudioImportError: If librosa/soundfile are missing.
        ValueError: For empty segments / too-short audio.
    """
    adapter = AudioAdapter(quiet=quiet)
    return adapter.from_audio(filepath, segment=segment)


async def analyze_audio_async(
    filepath: PathLike,
    *,
    segment: Optional[Tuple[float, Optional[float]]] = None,
    quiet: bool = False,
) -> AudioAnalysisResult:
    """Async convenience wrapper. Offloads librosa work to a worker thread.

    Args:
        filepath: Path to an audio file.
        segment: Optional ``(start_sec, end_sec)`` window;
            ``end_sec`` may be ``None``.
        quiet: Suppresses the ffmpeg-missing WARNING when ``True``.

    Returns:
        ``AudioAnalysisResult``.

    Raises:
        AudioImportError: If librosa/soundfile are missing.
        ValueError: For empty segments / too-short audio.
    """
    # to_thread instead of run_in_executor — DD1, avoids 3.10+
    # get_event_loop DeprecationWarning when called outside a running loop.
    return await asyncio.to_thread(
        analyze_audio, filepath, segment=segment, quiet=quiet
    )
