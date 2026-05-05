"""Public audio adapter — entry points for analyzing audio files.

This is the user-facing surface of the audio pipeline:

* ``AudioAdapter`` — orchestrates ``audio/_io.py`` (chroma extraction) and
  the WU1 audio core (``_key_estimation``, ``_cadence``, ``_region``).
* ``AudioAnalysisResult`` — frozen dataclass returned to callers.
* ``ChordEvent`` — frozen dataclass for timestamped chord events produced
  by the chord estimation layer (``audio/_chord_estimation.py``).
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
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Default ensemble preset — used when callers don't pass key_detection.
# "default" enables the four iteration_01 approaches; ks_only mirrors the
# pre-ensemble code path for backward compat.
_DEFAULT_KEY_DETECTION = "default"

# Type alias for the key_detection parameter shape. Three input shapes:
# preset string ("default" | "ks_only" | "full"), explicit list of approach
# names, or dict mapping approach name → weight.
KeyDetectionSpec = Union[str, List[str], Dict[str, float]]

# Rubato presets: (window_size_s, hop_size_s, median_kernel).
# Named after the musical term because that's literally what this controls —
# how tightly the analysis window tracks the beat grid. "strict" is a
# metronome; "free" is Rubinstein playing Chopin.
_RUBATO_PRESETS: dict[str, Tuple[float, float, int]] = {
    "strict": (0.25, 0.1, 3),
    "moderate": (0.5, 0.25, 3),
    "loose": (0.75, 0.4, 5),
    "free": (1.0, 0.5, 7),
}


def _resolve_rubato(rubato: Union[str, float]) -> Tuple[float, float, int]:
    """Map a rubato preset name or float to (window_size, hop_size, median_kernel).

    String values look up ``_RUBATO_PRESETS``. Float values in [0.0, 1.0]
    interpolate linearly between "strict" and "free", with the median kernel
    rounded to the nearest odd integer (because even-sized medians are an
    abomination unto the signal processing gods).

    Args:
        rubato: Preset name (``"strict"``, ``"moderate"``, ``"loose"``,
            ``"free"``) or a float 0.0–1.0 for continuous control.

    Returns:
        Tuple of ``(window_size_s, hop_size_s, median_kernel)``.

    Raises:
        ValueError: If ``rubato`` is a string not in the preset table.
    """
    if isinstance(rubato, str):
        if rubato in _RUBATO_PRESETS:
            return _RUBATO_PRESETS[rubato]
        raise ValueError(
            f"Unknown rubato preset {rubato!r}. "
            f"Valid presets: {', '.join(sorted(_RUBATO_PRESETS))}."
        )

    # Float path: lerp between strict and free. Clamp silently — if someone
    # passes 1.5 they probably meant "free" and we're not their parent.
    t = float(rubato)
    strict = _RUBATO_PRESETS["strict"]
    free = _RUBATO_PRESETS["free"]

    window = strict[0] + t * (free[0] - strict[0])
    hop = strict[1] + t * (free[1] - strict[1])
    raw_kernel = strict[2] + t * (free[2] - strict[2])

    # Round to nearest odd. The bit-twiddling is the classic "round to odd"
    # trick: round normally, then force the LSB. Equivalent to
    # 2 * round((raw_kernel + 1) / 2) - 1 but clearer about intent.
    kernel = 2 * ((int(raw_kernel) + 1) // 2) - 1
    kernel = max(1, kernel)  # paranoia: kernel must be at least 1

    return (window, hop, kernel)


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
    """A single chord event with time bounds and confidence.

    Produced by the chord estimation layer. Each event represents
    a contiguous time region where the algorithm detected the same chord
    label. Confidence is the cosine similarity (post-tonal-bias) of the
    best-matching template, averaged over the constituent windows.
    """

    start_time: float
    end_time: float
    chord_label: str
    confidence: float
    is_diatonic: bool


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
        chords: Populated by the chord estimation layer. Each entry is a
            ``ChordEvent`` with time bounds and confidence.
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
    # Diagnostic-panel payload populated only when callers ask for it. None
    # by default to keep production payloads light. Schema documented in
    # docs/reference/audio-api.md and at AC-05.
    key_analysis_details: Optional[Dict[str, Any]] = None

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
        """Return chord labels as a flat list of strings.

        Extracts ``chord_label`` from each ``ChordEvent`` in ``self.chords``.
        The resulting list is directly compatible with
        ``PatternAnalysisService.analyze_with_patterns_async(chord_symbols=...)``.

        Returns:
            ``list[str]`` of chord label strings (e.g. ``["C", "G", "Am", "F"]``).
        """
        return [c.chord_label for c in self.chords]


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

    def __init__(
        self,
        *,
        quiet: bool = False,
        include_chords: bool = True,
        chord_window_size_s: Optional[float] = None,
        chord_hop_size_s: Optional[float] = None,
        tonal_bias: float = 0.15,
        use_bass_chroma: bool = False,
        bass_bonus: float = 0.3,
        rubato: Union[str, float] = "moderate",
        min_chroma_norm: float = 0.05,
        key_detection: KeyDetectionSpec = _DEFAULT_KEY_DETECTION,
        show_analysis_details: bool = False,
        key_ensemble_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            quiet: When ``True``, suppresses the ffmpeg-missing WARNING
                log. Useful for test fixtures that want to avoid log-leak
                noise. Defaults to ``False``.
            include_chords: When ``True`` (default), the chord estimation
                layer runs during ``from_audio()``. Set to ``False`` to
                skip chord estimation entirely — useful when you only need
                key/cadence/region results and want to shave a few ms.
            chord_window_size_s: Chord estimation analysis window in seconds.
                When ``None`` (default), uses the value from rubato resolution.
                Explicit values override rubato.
            chord_hop_size_s: Chord estimation hop size in seconds.
                When ``None`` (default), uses the value from rubato resolution.
                Explicit values override rubato.
            tonal_bias: Bonus added to cosine similarity for diatonic chord
                templates. Set to 0.0 to disable tonal weighting.
            use_bass_chroma: When ``True``, extract a parallel bass-register
                chroma and use it to disambiguate relative-pair confusions
                (e.g. Am vs C). Costs a second chroma pass. Default ``False``.
            bass_bonus: Maximum bonus for bass-root matching. Scaled by
                per-window bass confidence. 0.3 is moderate; 0.5 is aggressive.
            rubato: Controls the temporal resolution of chord estimation.
                Named presets: ``"strict"`` (tight grid), ``"moderate"``
                (default, balanced), ``"loose"`` (forgiving), ``"free"``
                (very wide windows). Float 0.0–1.0 interpolates between
                strict and free. Affects window size, hop size, and median
                kernel. Explicit ``chord_window_size_s`` / ``chord_hop_size_s``
                override the rubato-derived values.
            min_chroma_norm: L2 norm threshold below which a chroma window
                is treated as silence and skipped. Prevents hallucinated
                chords during dead air. Default 0.05.
            key_detection: Ensemble preset, list of approach names, or
                dict of approach-name → weight. Defaults to ``"default"``
                which enables ``template_correlation``, ``boundary_chords``,
                ``bass_dominance``, and ``cadential``. ``"ks_only"`` runs
                only the K-S template correlation (matches pre-ensemble
                behavior). ``"full"`` includes the iteration_02 opt-ins
                ``pattern_engine`` and ``hmm`` (which fall back to no-op
                in iteration_01).
            show_analysis_details: When ``True``, populates
                ``AudioAnalysisResult.key_analysis_details`` with a
                per-approach breakdown for debugging. Off by default to
                keep payloads light for production callers.
            key_ensemble_weights: Optional override for the per-approach
                weights. Replaces the default weights for any approach
                listed; unlisted approaches retain their default weight.

        Raises:
            AudioImportError: If ``librosa`` or ``soundfile`` cannot be
                imported. Message contains ``"audio"`` and
                ``"pip install"`` for grep-friendly install guidance.
            ValueError: If ``key_detection`` is an unknown preset string,
                an empty list, or an empty dict.
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

        # Resolve rubato first — it provides defaults for window/hop/kernel.
        # Explicit chord_window_size_s / chord_hop_size_s override the
        # rubato-derived values, so callers with specific timing needs
        # aren't locked into presets.
        rubato_window, rubato_hop, rubato_kernel = _resolve_rubato(rubato)

        self._include_chords = include_chords
        self._chord_window_size_s = (
            chord_window_size_s if chord_window_size_s is not None else rubato_window
        )
        self._chord_hop_size_s = (
            chord_hop_size_s if chord_hop_size_s is not None else rubato_hop
        )
        self._tonal_bias = tonal_bias
        self._use_bass_chroma = use_bass_chroma
        self._bass_bonus = bass_bonus
        self._median_kernel = rubato_kernel
        self._min_chroma_norm = min_chroma_norm

        # Resolve key_detection up front. resolve_preset() validates the
        # spec and raises ValueError for bad input — we want the failure
        # at construction time, not deep inside from_audio().
        from harmonic_analysis.audio._key_ensemble import resolve_preset

        approach_names, resolved_weights = resolve_preset(key_detection)
        # Apply user weight overrides on top of the resolved defaults.
        if key_ensemble_weights:
            for k, v in key_ensemble_weights.items():
                resolved_weights[k] = float(v)
        self._key_detection_spec: KeyDetectionSpec = key_detection
        self._approach_names: List[str] = approach_names
        self._approach_weights: Dict[str, float] = resolved_weights
        self._show_analysis_details = show_analysis_details

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
            7. Chord estimation via template matching on local chroma.

        Args:
            filepath: Path to an audio file (WAV directly; MP3/AAC/OGG
                via ffmpeg).
            segment: Optional ``(start_sec, end_sec)`` window. ``end_sec``
                may be ``None`` to mean "to end of file." When omitted,
                the analyzed segment is the whole file.

        Returns:
            ``AudioAnalysisResult`` with global + local keys, cadences,
            region, segment bounds, and chord events (when
            ``include_chords`` is enabled).

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
        from harmonic_analysis.audio._key_approaches import DEFAULT_APPROACH_REGISTRY
        from harmonic_analysis.audio._key_approaches.template_correlation import (
            TemplateCorrelationApproach,
        )
        from harmonic_analysis.audio._key_ensemble import (
            KeyDetectionContext,
            KeyEnsembleSynthesizer,
        )
        from harmonic_analysis.audio._region import classify_region_type

        # Step 1 — global chroma + STAGE 1 key (template_correlation only).
        # The K-S result feeds chord estimation's tonal_bias. Even if the
        # ensemble eventually picks a different key, tonal_bias only
        # affects diatonic-chord weighting and relative pairs share the
        # same diatonic set — so stage-1 K-S is good enough here.
        global_chroma = extract_global_chroma(filepath)
        ks_verdict = TemplateCorrelationApproach().detect(
            KeyDetectionContext(chroma_1d=global_chroma)
        )
        ks_key = ks_verdict.ranked[0][0]

        # Step 2 — resolve segment bounds. Default: whole file. We need
        # to know file duration up front to fill in segment_end when no
        # segment is supplied.
        import soundfile as sf

        with sf.SoundFile(str(filepath), "r") as f:
            sr = f.samplerate
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
        local_chroma_1d = local_chroma.mean(axis=1)

        # Step 4 — STAGE 2: chord estimation, biased by the K-S key.
        # Always extract bass chroma when we'll need it for the ensemble
        # (or when use_bass_chroma is on). We compute it once and reuse
        # for both chord-estimation bonus and bass_dominance approach.
        bass_chroma = None
        bass_chroma_1d = None
        need_bass_for_ensemble = "bass_dominance" in self._approach_names
        if self._use_bass_chroma or need_bass_for_ensemble:
            from harmonic_analysis.audio._io import extract_local_bass_chroma

            bass_chroma = extract_local_bass_chroma(
                filepath, start_time=resolved_start, end_time=resolved_end
            )
            bass_chroma_1d = bass_chroma.mean(axis=1)

        chords: list[ChordEvent] = []
        if self._include_chords:
            from harmonic_analysis.audio._chord_estimation import (
                estimate_chord_progression,
            )

            chords = estimate_chord_progression(
                local_chroma,
                ks_key,  # tonal_bias driven by K-S — stage-1 result
                sr=sr,
                hop_length=512,
                window_size_s=self._chord_window_size_s,
                hop_size_s=self._chord_hop_size_s,
                tonal_bias=self._tonal_bias,
                bass_chroma_frames=bass_chroma if self._use_bass_chroma else None,
                bass_bonus=self._bass_bonus,
                min_chroma_norm=self._min_chroma_norm,
                median_kernel=self._median_kernel,
            )

        # Step 5 — STAGE 3: full ensemble. Run every enabled approach
        # against a context that now includes chord events from stage 2.
        ensemble_ctx = KeyDetectionContext(
            chroma_1d=global_chroma,
            bass_chroma_1d=bass_chroma_1d,
            chord_events=list(chords) if chords else None,
            audio_path=str(filepath),
        )

        verdicts = []
        for name in self._approach_names:
            cls = DEFAULT_APPROACH_REGISTRY.get(name)
            if cls is None:
                # Iteration_02 opt-ins (pattern_engine, hmm) aren't
                # registered yet. Skip silently — including their names
                # in "full" preset is forward-compat scaffolding.
                continue
            verdicts.append(cls().detect(ensemble_ctx))

        # If only template_correlation ran (ks_only path), we're done —
        # the synthesizer will return a SynthesisResult whose winner is
        # the K-S key. No special-case needed.
        synthesizer = KeyEnsembleSynthesizer()
        synthesis_result = synthesizer.synthesize(
            verdicts, weights=self._approach_weights
        )
        ensemble_key = synthesis_result.winner

        # Step 6 — local key. With segments, the local chroma differs
        # from the global; recompute via ensemble using the local chroma.
        # When no segment is set, local == global by construction so we
        # reuse the ensemble winner to avoid redundant work.
        if segment is None:
            local_key = ensemble_key
            # Cadences and region still want their inputs; reuse local_chroma.
        else:
            # Run a smaller ensemble on the local chroma. We use
            # template_correlation only here for performance — the
            # boundary/bass/cadential signals are global concepts and
            # don't need re-running per segment.
            local_ks = TemplateCorrelationApproach().detect(
                KeyDetectionContext(chroma_1d=local_chroma_1d)
            )
            local_key = local_ks.ranked[0][0]

        # Step 7 — cadences and region classification. detect_cadences
        # does its own .mean(axis=1) internally on the 2D matrix.
        cadences = detect_cadences(local_chroma, local_key)
        region = classify_region_type(
            global_key=ensemble_key,
            local_key=local_key,
            local_key_confidence=local_key.confidence,
            local_cadence=cadences,
        )

        # Step 8 — diagnostic panel (only when requested).
        key_analysis_details: Optional[Dict[str, Any]] = None
        if self._show_analysis_details:
            key_analysis_details = self._build_analysis_details(
                verdicts=verdicts, synthesis=synthesis_result
            )

        return AudioAnalysisResult(
            global_key=ensemble_key,
            local_key=local_key,
            cadences=cadences,
            region=region,
            segment_start=resolved_start,
            segment_end=resolved_end,
            chords=chords,
            key_analysis_details=key_analysis_details,
        )

    def _build_analysis_details(
        self,
        *,
        verdicts: list,
        synthesis: object,
    ) -> Dict[str, Any]:
        """Construct the show_analysis_details payload.

        Schema is locked by AC-05:
            {
                "approaches": [{"name", "weight", "top_3": [{...}]}, ...],
                "synthesis": {
                    "method", "winner": {...}, "runner_up": {...} | None,
                    "margin", "key_score_table"
                },
                "modulations": None,  # iteration_02 owns the HMM segments
            }

        KeyInfo objects get manually serialized — the frozenset
        ``diatonic_pitch_classes`` would explode any naive ``asdict``.
        """

        def _key_to_dict(ki: object) -> Dict[str, Any]:
            return {
                "tonic": getattr(ki, "tonic", None),
                "mode": getattr(ki, "mode", None),
                "key_signature": getattr(ki, "key_signature", None),
                "confidence": getattr(ki, "confidence", None),
            }

        approaches_payload = []
        for v in verdicts:
            top_3 = [
                {"key": _key_to_dict(k), "score": float(s)} for k, s in v.ranked[:3]
            ]
            approaches_payload.append(
                {
                    "name": v.name,
                    "weight": float(self._approach_weights.get(v.name, 0.0)),
                    "top_3": top_3,
                }
            )

        synth_payload = {
            "method": getattr(synthesis, "method", "weighted_sum"),
            "winner": _key_to_dict(getattr(synthesis, "winner", None)),
            "runner_up": (
                _key_to_dict(getattr(synthesis, "runner_up"))
                if getattr(synthesis, "runner_up", None) is not None
                else None
            ),
            "margin": float(getattr(synthesis, "margin", 0.0)),
            "key_score_table": dict(getattr(synthesis, "key_score_table", {})),
        }

        return {
            "approaches": approaches_payload,
            "synthesis": synth_payload,
            "modulations": None,  # iteration_02
        }


def analyze_audio(
    filepath: PathLike,
    *,
    segment: Optional[Tuple[float, Optional[float]]] = None,
    quiet: bool = False,
    include_chords: bool = True,
    chord_window_size_s: Optional[float] = None,
    chord_hop_size_s: Optional[float] = None,
    tonal_bias: float = 0.15,
    use_bass_chroma: bool = False,
    bass_bonus: float = 0.3,
    rubato: Union[str, float] = "moderate",
    min_chroma_norm: float = 0.05,
    key_detection: KeyDetectionSpec = _DEFAULT_KEY_DETECTION,
    show_analysis_details: bool = False,
    key_ensemble_weights: Optional[Dict[str, float]] = None,
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
        include_chords: Enable chord estimation (default ``True``).
        chord_window_size_s: Chord estimation window size in seconds.
            ``None`` uses the rubato-derived default.
        chord_hop_size_s: Chord estimation hop size in seconds.
            ``None`` uses the rubato-derived default.
        tonal_bias: Diatonic similarity bonus for chord estimation.
        use_bass_chroma: Extract bass-register chroma for root
            disambiguation. Default ``False``.
        bass_bonus: Bass-root matching bonus magnitude.
        rubato: Temporal resolution preset or float 0.0–1.0.
            See ``AudioAdapter.__init__`` for details.
        min_chroma_norm: Silence detection threshold for chroma windows.

    Returns:
        ``AudioAnalysisResult``.

    Raises:
        AudioImportError: If librosa/soundfile are missing.
        ValueError: For empty segments / too-short audio.
    """
    adapter = AudioAdapter(
        quiet=quiet,
        include_chords=include_chords,
        chord_window_size_s=chord_window_size_s,
        chord_hop_size_s=chord_hop_size_s,
        tonal_bias=tonal_bias,
        use_bass_chroma=use_bass_chroma,
        bass_bonus=bass_bonus,
        rubato=rubato,
        min_chroma_norm=min_chroma_norm,
        key_detection=key_detection,
        show_analysis_details=show_analysis_details,
        key_ensemble_weights=key_ensemble_weights,
    )
    return adapter.from_audio(filepath, segment=segment)


async def analyze_audio_async(
    filepath: PathLike,
    *,
    segment: Optional[Tuple[float, Optional[float]]] = None,
    quiet: bool = False,
    include_chords: bool = True,
    chord_window_size_s: Optional[float] = None,
    chord_hop_size_s: Optional[float] = None,
    tonal_bias: float = 0.15,
    use_bass_chroma: bool = False,
    bass_bonus: float = 0.3,
    rubato: Union[str, float] = "moderate",
    min_chroma_norm: float = 0.05,
    key_detection: KeyDetectionSpec = _DEFAULT_KEY_DETECTION,
    show_analysis_details: bool = False,
    key_ensemble_weights: Optional[Dict[str, float]] = None,
) -> AudioAnalysisResult:
    """Async convenience wrapper. Offloads librosa work to a worker thread.

    Args:
        filepath: Path to an audio file.
        segment: Optional ``(start_sec, end_sec)`` window;
            ``end_sec`` may be ``None``.
        quiet: Suppresses the ffmpeg-missing WARNING when ``True``.
        include_chords: Enable chord estimation (default ``True``).
        chord_window_size_s: Chord estimation window size in seconds.
            ``None`` uses the rubato-derived default.
        chord_hop_size_s: Chord estimation hop size in seconds.
            ``None`` uses the rubato-derived default.
        tonal_bias: Diatonic similarity bonus for chord estimation.
        use_bass_chroma: Extract bass-register chroma for root
            disambiguation. Default ``False``.
        bass_bonus: Bass-root matching bonus magnitude.
        rubato: Temporal resolution preset or float 0.0–1.0.
            See ``AudioAdapter.__init__`` for details.
        min_chroma_norm: Silence detection threshold for chroma windows.

    Returns:
        ``AudioAnalysisResult``.

    Raises:
        AudioImportError: If librosa/soundfile are missing.
        ValueError: For empty segments / too-short audio.
    """
    # to_thread instead of run_in_executor — DD1, avoids 3.10+
    # get_event_loop DeprecationWarning when called outside a running loop.
    return await asyncio.to_thread(
        analyze_audio,
        filepath,
        segment=segment,
        quiet=quiet,
        include_chords=include_chords,
        chord_window_size_s=chord_window_size_s,
        chord_hop_size_s=chord_hop_size_s,
        tonal_bias=tonal_bias,
        use_bass_chroma=use_bass_chroma,
        bass_bonus=bass_bonus,
        rubato=rubato,
        min_chroma_norm=min_chroma_norm,
        key_detection=key_detection,
        show_analysis_details=show_analysis_details,
        key_ensemble_weights=key_ensemble_weights,
    )
