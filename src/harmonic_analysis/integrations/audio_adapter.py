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
        # "auto" is a deferred-resolution sentinel — the actual values
        # depend on detected tempo, which we don't have at __init__ time.
        # Caller handles tempo detection during analysis and overrides.
        # We return moderate as a safe stub so __init__ doesn't blow up.
        if rubato == "auto":
            return _RUBATO_PRESETS["moderate"]
        raise ValueError(
            f"Unknown rubato preset {rubato!r}. "
            f"Valid presets: {', '.join(sorted(_RUBATO_PRESETS))} or 'auto'."
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


def _respell_keyinfo_for_display(key_info: Any) -> Any:
    """Return a copy of ``key_info`` with canonical music-notation spelling.

    Audio's internal ``PITCH_CLASSES`` is sharps-only (so a song in B-flat
    minor surfaces internally as ``A# Aeolian``). This wraps the K-S
    output before it reaches the caller so the published ``tonic`` and
    ``key_signature`` follow the rest of the library's spelling
    convention (Bb minor, not A# minor; Db major, not C# major; etc.).

    See ``_profiles.canonical_key_spelling`` for the per-PC respell table
    and the music-notation rationale.
    """
    from harmonic_analysis.audio._profiles import canonical_key_spelling
    from harmonic_analysis.audio._types import KeyInfo

    display_tonic, display_key_sig = canonical_key_spelling(
        key_info.tonic, key_info.mode
    )
    if display_tonic == key_info.tonic and display_key_sig == key_info.key_signature:
        return key_info
    return KeyInfo(
        tonic=display_tonic,
        mode=key_info.mode,
        key_signature=display_key_sig,
        confidence=key_info.confidence,
    )


def _respell_analysis_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """Apply canonical key spelling to every key reference in the panel.

    The diagnostic panel embeds many KeyInfo-shaped dicts (each approach's
    top_3 / top_5, the synthesis winner / runner-up, the score table). We
    walk all of them and rewrite ``tonic`` + ``key_signature`` in-place
    using the same convention as the surface-level fields.
    """
    from harmonic_analysis.audio._profiles import canonical_key_spelling

    def _respell_key_dict(k: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not k:
            return k
        tonic = k.get("tonic")
        mode = k.get("mode")
        if not tonic or not mode:
            return k
        new_tonic, new_keysig = canonical_key_spelling(tonic, mode)
        if new_tonic == tonic:
            return k
        return {**k, "tonic": new_tonic, "key_signature": new_keysig}

    out = dict(details)

    # Per-approach top_3 / top_5 candidate lists.
    approaches = out.get("approaches") or []
    new_approaches = []
    for a in approaches:
        new_a = dict(a)
        for field_name in ("top_3", "top_5"):
            if field_name in new_a:
                new_a[field_name] = [
                    {**entry, "key": _respell_key_dict(entry.get("key"))}
                    for entry in new_a[field_name]
                ]
        new_approaches.append(new_a)
    out["approaches"] = new_approaches

    # Synthesis winner / runner_up.
    synth = out.get("synthesis")
    if synth:
        new_synth = dict(synth)
        new_synth["winner"] = _respell_key_dict(synth.get("winner"))
        if synth.get("runner_up"):
            new_synth["runner_up"] = _respell_key_dict(synth.get("runner_up"))
        # Score table keys are "<tonic> <mode>" strings — rewrite them.
        score_table = synth.get("key_score_table")
        if score_table:
            rebuilt = {}
            for label, score in score_table.items():
                parts = label.rsplit(" ", 1)
                if len(parts) == 2:
                    new_tonic, new_keysig = canonical_key_spelling(*parts)
                    rebuilt[new_keysig] = score
                else:
                    rebuilt[label] = score
            new_synth["key_score_table"] = rebuilt
        out["synthesis"] = new_synth

    return out


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
        tempo: Optional tempo information. Populated when ``rubato="auto"``
            triggers tempo detection, or always when callers want BPM
            metadata. ``None`` when tempo wasn't computed (saves the
            librosa cycles when no caller asked for it).

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
    # Tempo info — populated when rubato="auto" triggers detection, or
    # when callers explicitly request it. Carries BPM, confidence, and
    # (variable-tempo) tempo regions. See _tempo.TempoInfo for schema.
    tempo: Optional[object] = None  # TempoInfo, quoted to dodge import order

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
        bass_confidence_threshold: float = 0.25,
        rubato: Union[str, float] = "moderate",
        min_chroma_norm: float = 0.05,
        rms_silence_threshold: float = 0.005,
        trailing_silence_window_s: float = 3.0,
        trailing_silence_ratio: float = 0.10,
        key_detection: KeyDetectionSpec = _DEFAULT_KEY_DETECTION,
        show_analysis_details: bool = False,
        key_ensemble_weights: Optional[Dict[str, float]] = None,
        tempo_region_threshold: float = 0.20,
        merge_same_root: bool = True,
        max_merge_duration_s: float = 4.0,
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
        # aren't locked into presets. "auto" returns moderate values here
        # as a stub; the real numbers come from tempo detection at
        # analysis time (see ``from_audio``).
        rubato_window, rubato_hop, rubato_kernel = _resolve_rubato(rubato)

        # Stash the original choice so from_audio can detect "auto" and
        # reach for tempo detection. We deliberately don't normalize
        # this — "auto", a preset name, or a float all flow through and
        # the analysis method dispatches.
        self._rubato_setting = rubato
        # Track whether window/hop/kernel were explicitly pinned by the
        # caller — those override rubato (including "auto") so a caller
        # who wants exact control gets it.
        self._chord_window_explicit = chord_window_size_s is not None
        self._chord_hop_explicit = chord_hop_size_s is not None

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
        self._bass_confidence_threshold = bass_confidence_threshold
        self._median_kernel = rubato_kernel
        self._min_chroma_norm = min_chroma_norm
        self._rms_silence_threshold = rms_silence_threshold
        self._trailing_silence_window_s = trailing_silence_window_s
        self._trailing_silence_ratio = trailing_silence_ratio
        self._merge_same_root = merge_same_root
        self._max_merge_duration_s = max_merge_duration_s
        # Fractional BPM change that triggers a new tempo region during
        # auto-rubato detection. 20% is loose enough to ignore performance
        # micro-variation, tight enough to catch deliberate tempo changes
        # (accelerando, ritardando, sectional speed shifts).
        self._tempo_region_threshold = tempo_region_threshold

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

        # Step 3b — tempo detection. Always-on when rubato="auto" (we
        # need the BPM to size the chord window); skipped otherwise to
        # save the librosa call. Result is surfaced in the final payload
        # whenever it was computed, so callers who set rubato="auto"
        # also get BPM metadata for free.
        from harmonic_analysis.audio._tempo import (
            TempoInfo,
            bpm_to_rubato,
            detect_tempo,
        )

        tempo_info: Optional[TempoInfo] = None
        chord_window = self._chord_window_size_s
        chord_hop = self._chord_hop_size_s
        chord_kernel = self._median_kernel
        if self._rubato_setting == "auto" and self._include_chords:
            tempo_info = detect_tempo(
                filepath,
                start_time=resolved_start,
                end_time=resolved_end,
                # Variable-tempo support: ask for region segmentation so
                # each constant-tempo span can size its own chord window.
                # Stable-tempo material gets a single region (or none) and
                # we fall back to global-BPM sizing automatically.
                detect_regions=True,
                region_change_threshold=self._tempo_region_threshold,
            )
            # Explicit window/hop pins from the caller still win — auto
            # only fills in slots the caller left open.
            auto_window, auto_hop, auto_kernel = bpm_to_rubato(
                tempo_info.bpm, tempo_info.confidence
            )
            if not self._chord_window_explicit:
                chord_window = auto_window
            if not self._chord_hop_explicit:
                chord_hop = auto_hop
            chord_kernel = auto_kernel

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
            from harmonic_analysis.audio._io import extract_local_rms_envelope

            # Frame-aligned RMS envelope — the only way to recognize
            # actual silence in the audio (chroma_cqt's normalization
            # makes its own norm useless as a silence proxy).
            rms_envelope = extract_local_rms_envelope(
                filepath, start_time=resolved_start, end_time=resolved_end
            )

            # Variable-tempo path: when auto detected multiple tempo
            # regions AND those regions would actually get different
            # window sizes from bpm_to_rubato, run chord estimation
            # independently per region. When all regions would clamp
            # to the same window (because the cap or floor pins them),
            # per-region processing adds no benefit — it just slices
            # the chroma at region boundaries, which introduces
            # spurious chord events that confuse the cadential vote.
            # Stable-tempo material and "regions but same window"
            # material both fall through to the single-pass global path.
            #
            # Empirical note: per-region also helps on songs where the
            # windows are *technically* distinct but very close (e.g.,
            # dusty_wings with 0.992s vs 1.000s windows). The slicing
            # itself appears to give the chord matcher beneficial
            # boundary resets — without it, chord events bleed across
            # section transitions and confuse the cadential vote. Keep
            # the per-region path even when the spread looks tiny.
            from harmonic_analysis.audio._tempo import bpm_to_rubato

            use_per_region = (
                tempo_info is not None
                and len(tempo_info.regions) > 1
                and not self._chord_window_explicit
                and not self._chord_hop_explicit
            )
            if use_per_region:
                assert tempo_info is not None  # mypy hint
                # Compute per-region window tuples; if they're all
                # identical, fall through to the global path. (Tiny
                # numerical differences still count as distinct — see
                # the empirical note above.)
                region_windows = {
                    bpm_to_rubato(r.bpm, r.confidence) for r in tempo_info.regions
                }
                if len(region_windows) <= 1:
                    use_per_region = False

            if use_per_region:
                assert tempo_info is not None  # mypy hint
                chords = _estimate_chords_per_region(
                    local_chroma=local_chroma,
                    rms_envelope=rms_envelope,
                    bass_chroma=bass_chroma if self._use_bass_chroma else None,
                    regions=tempo_info.regions,
                    segment_start=resolved_start,
                    ks_key=ks_key,
                    sr=sr,
                    tonal_bias=self._tonal_bias,
                    bass_bonus=self._bass_bonus,
                    bass_confidence_threshold=self._bass_confidence_threshold,
                    min_chroma_norm=self._min_chroma_norm,
                    rms_silence_threshold=self._rms_silence_threshold,
                    trailing_silence_window_s=self._trailing_silence_window_s,
                    trailing_silence_ratio=self._trailing_silence_ratio,
                    merge_same_root=self._merge_same_root,
                    max_merge_duration_s=self._max_merge_duration_s,
                )
            else:
                chords = estimate_chord_progression(
                    local_chroma,
                    ks_key,  # tonal_bias driven by K-S — stage-1 result
                    sr=sr,
                    hop_length=512,
                    window_size_s=chord_window,
                    hop_size_s=chord_hop,
                    tonal_bias=self._tonal_bias,
                    bass_chroma_frames=(bass_chroma if self._use_bass_chroma else None),
                    bass_bonus=self._bass_bonus,
                    bass_confidence_threshold=self._bass_confidence_threshold,
                    min_chroma_norm=self._min_chroma_norm,
                    rms_frames=rms_envelope,
                    rms_silence_threshold=self._rms_silence_threshold,
                    trailing_silence_window_s=self._trailing_silence_window_s,
                    trailing_silence_ratio=self._trailing_silence_ratio,
                    median_kernel=chord_kernel,
                    merge_same_root=self._merge_same_root,
                    max_merge_duration_s=self._max_merge_duration_s,
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

        # Step 9 — canonical key spelling. Internal pipeline uses the
        # audio module's sharps-only PITCH_CLASSES for pitch-class
        # arithmetic ("A#", "G#", etc.); the rest of the library and
        # standard music notation expect flats for most black-key roots
        # (Bb minor, not A# minor). Apply at the API boundary so the
        # internal calculations stay consistent but every value the
        # caller sees follows the canonical convention.
        ensemble_key = _respell_keyinfo_for_display(ensemble_key)
        local_key = _respell_keyinfo_for_display(local_key)
        if key_analysis_details is not None:
            key_analysis_details = _respell_analysis_details(key_analysis_details)

        return AudioAnalysisResult(
            global_key=ensemble_key,
            local_key=local_key,
            cadences=cadences,
            region=region,
            segment_start=resolved_start,
            segment_end=resolved_end,
            chords=chords,
            key_analysis_details=key_analysis_details,
            tempo=tempo_info,
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
            # Build top_3 (the human-friendly summary) and top_5 (the
            # diagnostic-deep-dive view) in one pass. With extended chord
            # templates, more chord variants emerge per harmonic moment,
            # so the cadential rankings shift around. Three entries was
            # enough on the old triad-only matcher; five gives the
            # diagnostics enough room to expose the dual-credit pattern
            # even when other tonics climb above on raw count.
            ranked_dicts = [
                {"key": _key_to_dict(k), "score": float(s)} for k, s in v.ranked[:5]
            ]
            approaches_payload.append(
                {
                    "name": v.name,
                    "weight": float(self._approach_weights.get(v.name, 0.0)),
                    "top_3": ranked_dicts[:3],
                    "top_5": ranked_dicts,
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


def _estimate_chords_per_region(
    *,
    local_chroma: Any,  # np.ndarray, kept Any to avoid lazy-import dance
    rms_envelope: Optional[Any],
    bass_chroma: Optional[Any],
    regions: list,
    segment_start: float,
    ks_key: Any,  # KeyInfo
    sr: int,
    tonal_bias: float,
    bass_bonus: float,
    bass_confidence_threshold: float = 0.25,
    min_chroma_norm: float = 0.05,
    rms_silence_threshold: float = 0.005,
    trailing_silence_window_s: float = 3.0,
    trailing_silence_ratio: float = 0.10,
    merge_same_root: bool = True,
    max_merge_duration_s: float = 4.0,
    hop_length: int = 512,
) -> list:
    """Run chord estimation independently for each tempo region.

    Variable-tempo path. Each ``TempoRegion`` gets its own
    ``window/hop/kernel`` derived from its own BPM, then we concatenate
    the per-region events back into one list (timestamps offset to file
    time) and run a final same-root merge across the boundaries to
    consolidate any chord that spans a region edge.

    Beyond the obvious wide-tempo-spread case, the slicing itself
    appears to give the chord matcher beneficial boundary resets on
    songs with detected section structure even when the per-region
    windows are nearly identical — without the resets, chord events
    bleed across section transitions and confuse the cadential vote.
    """
    from harmonic_analysis.audio._chord_estimation import (
        _merge_same_root_events,
        estimate_chord_progression,
    )
    from harmonic_analysis.audio._tempo import bpm_to_rubato

    fps = sr / hop_length
    all_events: list[ChordEvent] = []

    for region in regions:
        region_start_frame = max(0, int((region.start_time - segment_start) * fps))
        region_end_frame = min(
            local_chroma.shape[1],
            int((region.end_time - segment_start) * fps),
        )
        if region_end_frame <= region_start_frame:
            continue

        chroma_slice = local_chroma[:, region_start_frame:region_end_frame]
        rms_slice = (
            rms_envelope[region_start_frame:region_end_frame]
            if rms_envelope is not None
            else None
        )
        bass_slice = (
            bass_chroma[:, region_start_frame:region_end_frame]
            if bass_chroma is not None
            else None
        )

        window_s, hop_s, kernel = bpm_to_rubato(region.bpm, region.confidence)

        # Defer the merge to the final cross-region pass below.
        region_events = estimate_chord_progression(
            chroma_slice,
            ks_key,
            sr=sr,
            hop_length=hop_length,
            window_size_s=window_s,
            hop_size_s=hop_s,
            tonal_bias=tonal_bias,
            bass_chroma_frames=bass_slice,
            bass_bonus=bass_bonus,
            bass_confidence_threshold=bass_confidence_threshold,
            min_chroma_norm=min_chroma_norm,
            rms_frames=rms_slice,
            rms_silence_threshold=rms_silence_threshold,
            trailing_silence_window_s=trailing_silence_window_s,
            trailing_silence_ratio=trailing_silence_ratio,
            median_kernel=kernel,
            merge_same_root=False,
        )

        # Offset timestamps from region-local back to file-relative.
        for ce in region_events:
            all_events.append(
                ChordEvent(
                    start_time=ce.start_time + region.start_time,
                    end_time=ce.end_time + region.start_time,
                    chord_label=ce.chord_label,
                    confidence=ce.confidence,
                    is_diatonic=ce.is_diatonic,
                )
            )

    # Final merge across all boundaries — catches chords that legitimately
    # span a region edge.
    if not merge_same_root:
        return all_events
    return _merge_same_root_events(
        all_events, max_merge_duration_s=max_merge_duration_s
    )


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
    bass_confidence_threshold: float = 0.25,
    rubato: Union[str, float] = "moderate",
    min_chroma_norm: float = 0.05,
    rms_silence_threshold: float = 0.005,
    trailing_silence_window_s: float = 3.0,
    trailing_silence_ratio: float = 0.10,
    key_detection: KeyDetectionSpec = _DEFAULT_KEY_DETECTION,
    show_analysis_details: bool = False,
    key_ensemble_weights: Optional[Dict[str, float]] = None,
    tempo_region_threshold: float = 0.20,
    merge_same_root: bool = True,
    max_merge_duration_s: float = 4.0,
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
        bass_confidence_threshold=bass_confidence_threshold,
        rubato=rubato,
        min_chroma_norm=min_chroma_norm,
        rms_silence_threshold=rms_silence_threshold,
        trailing_silence_window_s=trailing_silence_window_s,
        trailing_silence_ratio=trailing_silence_ratio,
        key_detection=key_detection,
        show_analysis_details=show_analysis_details,
        key_ensemble_weights=key_ensemble_weights,
        tempo_region_threshold=tempo_region_threshold,
        merge_same_root=merge_same_root,
        max_merge_duration_s=max_merge_duration_s,
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
    bass_confidence_threshold: float = 0.25,
    rubato: Union[str, float] = "moderate",
    min_chroma_norm: float = 0.05,
    rms_silence_threshold: float = 0.005,
    trailing_silence_window_s: float = 3.0,
    trailing_silence_ratio: float = 0.10,
    key_detection: KeyDetectionSpec = _DEFAULT_KEY_DETECTION,
    show_analysis_details: bool = False,
    key_ensemble_weights: Optional[Dict[str, float]] = None,
    tempo_region_threshold: float = 0.20,
    merge_same_root: bool = True,
    max_merge_duration_s: float = 4.0,
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
        bass_confidence_threshold=bass_confidence_threshold,
        rubato=rubato,
        min_chroma_norm=min_chroma_norm,
        rms_silence_threshold=rms_silence_threshold,
        trailing_silence_window_s=trailing_silence_window_s,
        trailing_silence_ratio=trailing_silence_ratio,
        key_detection=key_detection,
        show_analysis_details=show_analysis_details,
        key_ensemble_weights=key_ensemble_weights,
        tempo_region_threshold=tempo_region_threshold,
        merge_same_root=merge_same_root,
        max_merge_duration_s=max_merge_duration_s,
    )
