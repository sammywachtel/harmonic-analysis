# Audio API Reference

Field-by-field reference for the audio analysis surface. For the core pattern analysis API, see [api-reference.md](api-reference.md).

## Module-Level Convenience Functions

### `analyze_audio(path, *, segment=None, quiet=False, include_chords=True, chord_window_size_s=None, chord_hop_size_s=None, tonal_bias=0.15, rubato="moderate", use_bass_chroma=False, bass_bonus=0.3, min_chroma_norm=0.05, key_detection="default", show_analysis_details=False, key_ensemble_weights=None)`

Synchronous convenience wrapper. Constructs a fresh `AudioAdapter` per call — cheap, the only real work in construction is an ffmpeg-on-PATH check.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `str \| Path` | required | Path to an audio file (WAV directly; MP3/AAC/OGG via ffmpeg) |
| `segment` | `tuple[float, float \| None] \| None` | `None` | Optional `(start_sec, end_sec)` window. `end_sec` may be `None` for "to end of file" |
| `quiet` | `bool` | `False` | Suppress the ffmpeg-missing WARNING log |
| `include_chords` | `bool` | `True` | Enable chord estimation layer |
| `chord_window_size_s` | `float \| None` | `None` | Chord estimation analysis window in seconds. When `None`, derived from `rubato`; an explicit float overrides the preset |
| `chord_hop_size_s` | `float \| None` | `None` | Chord estimation hop size in seconds. When `None`, derived from `rubato`; an explicit float overrides the preset |
| `tonal_bias` | `float` | `0.15` | Diatonic similarity bonus for chord template matching |
| `rubato` | `str \| float` | `"moderate"` | Temporal flexibility preset. Named presets: `"strict"`, `"moderate"`, `"loose"`, `"free"`. Float `0.0`–`1.0` for continuous interpolation (0.0 = tightest, 1.0 = loosest) |
| `use_bass_chroma` | `bool` | `False` | Enable bass-aware chord estimation using a second chroma extraction focused on low frequencies |
| `bass_bonus` | `float` | `0.3` | Maximum bonus added to template cosine similarity when the chord root matches the bass chroma peak. Scaled per-window by bass-chroma confidence so noisy bass detections contribute less. Only effective when `use_bass_chroma=True` |
| `min_chroma_norm` | `float` | `0.05` | Minimum L2 norm threshold for chord detection windows. Windows below this norm are treated as silence and produce no chord label |
| `key_detection` | `str \| list[str] \| dict[str, float]` | `"default"` | Ensemble preset (`"default"`, `"ks_only"`, `"full"`), explicit list of approach names, or `{name: weight}` dict. See [Key Detection Ensemble](#key-detection-ensemble) below |
| `show_analysis_details` | `bool` | `False` | When `True`, populates `result.key_analysis_details` with per-approach breakdown for debugging |
| `key_ensemble_weights` | `dict[str, float] \| None` | `None` | Optional override mapping approach name → weight; replaces preset defaults |

**Returns:** `AudioAnalysisResult`

**Raises:**
- `AudioImportError` — if `librosa` or `soundfile` are not installed
- `ValueError` — for empty or too-short segments, unknown `key_detection` preset names, empty list/dict `key_detection` specs

### `analyze_audio_async(path, *, segment=None, quiet=False, include_chords=True, chord_window_size_s=None, chord_hop_size_s=None, tonal_bias=0.15, rubato="moderate", use_bass_chroma=False, bass_bonus=0.3, min_chroma_norm=0.05, key_detection="default", show_analysis_details=False, key_ensemble_weights=None)`

Async convenience wrapper. Uses `asyncio.to_thread` to keep the blocking librosa work off the event loop. Same parameters and return type as `analyze_audio`.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `str \| Path` | required | Path to an audio file (WAV directly; MP3/AAC/OGG via ffmpeg) |
| `segment` | `tuple[float, float \| None] \| None` | `None` | Optional `(start_sec, end_sec)` window. `end_sec` may be `None` for "to end of file" |
| `quiet` | `bool` | `False` | Suppress the ffmpeg-missing WARNING log |
| `include_chords` | `bool` | `True` | Enable chord estimation layer |
| `chord_window_size_s` | `float \| None` | `None` | Chord estimation analysis window in seconds. When `None`, derived from `rubato`; an explicit float overrides the preset |
| `chord_hop_size_s` | `float \| None` | `None` | Chord estimation hop size in seconds. When `None`, derived from `rubato`; an explicit float overrides the preset |
| `tonal_bias` | `float` | `0.15` | Diatonic similarity bonus for chord template matching |
| `rubato` | `str \| float` | `"moderate"` | Temporal flexibility preset. Named presets: `"strict"`, `"moderate"`, `"loose"`, `"free"`. Float `0.0`–`1.0` for continuous interpolation (0.0 = tightest, 1.0 = loosest) |
| `use_bass_chroma` | `bool` | `False` | Enable bass-aware chord estimation using a second chroma extraction focused on low frequencies |
| `bass_bonus` | `float` | `0.3` | Maximum bonus added to template cosine similarity when the chord root matches the bass chroma peak. Scaled per-window by bass-chroma confidence so noisy bass detections contribute less. Only effective when `use_bass_chroma=True` |
| `min_chroma_norm` | `float` | `0.05` | Minimum L2 norm threshold for chord detection windows. Windows below this norm are treated as silence and produce no chord label |
| `key_detection` | `str \| list[str] \| dict[str, float]` | `"default"` | See [Key Detection Ensemble](#key-detection-ensemble) below |
| `show_analysis_details` | `bool` | `False` | Populate `result.key_analysis_details` with per-approach breakdown |
| `key_ensemble_weights` | `dict[str, float] \| None` | `None` | Override per-approach weights |

## `AudioAdapter`

Orchestrator class. Construction is the lazy-import boundary — `librosa` and `soundfile` are imported inside `__init__`.

### Constructor

```python
AudioAdapter(
    *,
    quiet: bool = False,
    include_chords: bool = True,
    chord_window_size_s: float | None = None,
    chord_hop_size_s: float | None = None,
    tonal_bias: float = 0.15,
    rubato: str | float = "moderate",
    use_bass_chroma: bool = False,
    bass_bonus: float = 0.3,
    min_chroma_norm: float = 0.05,
)
```

**Constructor Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `quiet` | `bool` | `False` | Suppress the ffmpeg-missing WARNING log |
| `include_chords` | `bool` | `True` | Enable chord estimation layer |
| `chord_window_size_s` | `float \| None` | `None` | Chord estimation analysis window in seconds. When `None`, derived from `rubato`; an explicit float overrides the preset |
| `chord_hop_size_s` | `float \| None` | `None` | Chord estimation hop size in seconds. When `None`, derived from `rubato`; an explicit float overrides the preset |
| `tonal_bias` | `float` | `0.15` | Diatonic similarity bonus for chord template matching |
| `rubato` | `str \| float` | `"moderate"` | Temporal flexibility preset. Named presets: `"strict"`, `"moderate"`, `"loose"`, `"free"`. Float `0.0`–`1.0` for continuous interpolation (0.0 = tightest, 1.0 = loosest) |
| `use_bass_chroma` | `bool` | `False` | Enable bass-aware chord estimation using a second chroma extraction focused on low frequencies |
| `bass_bonus` | `float` | `0.3` | Maximum bonus added to template cosine similarity when the chord root matches the bass chroma peak. Scaled per-window by bass-chroma confidence so noisy bass detections contribute less. Only effective when `use_bass_chroma=True` |
| `min_chroma_norm` | `float` | `0.05` | Minimum L2 norm threshold for chord detection windows. Windows below this norm are treated as silence and produce no chord label |

**Raises:** `AudioImportError` if `librosa` or `soundfile` cannot be imported.

**Attributes:**
- `ffmpeg_available: bool` — `True` if `ffmpeg` was found on PATH at construction time.

### `from_audio(filepath, *, segment=None) -> AudioAnalysisResult`

Run the full audio analysis pipeline on a file.

**Pipeline steps:**
1. Extract global chroma (1D `(12,)`) and estimate global key
2. Resolve segment bounds (default: whole file)
3. Extract local chroma (2D `(12, T)`) for the segment
4. Estimate local key from time-averaged local chroma
5. Detect cadences from raw 2D local chroma
6. Classify region against the global key
7. Chord estimation via template matching on local chroma (when `include_chords=True`)

## Result Dataclasses

All result types are frozen dataclasses.

### `AudioAnalysisResult`

The top-level result returned by `analyze_audio` and `AudioAdapter.from_audio`.

| Field | Type | Description |
|-------|------|-------------|
| `global_key` | `KeyInfo` | Ensemble key estimate over the whole file (was K-S only before iteration 02) |
| `local_key` | `KeyInfo` | Key estimate over the analyzed segment |
| `cadences` | `CadenceInfo` | V-I cadence detection result |
| `region` | `RegionInfo` | Region classification (stable / modulation / modal_shift) |
| `chords` | `list[ChordEvent]` | Timestamped chord events (empty if `include_chords=False`) |
| `segment_start` | `float` | Start of analyzed segment in seconds |
| `segment_end` | `float` | End of analyzed segment in seconds |
| `key_analysis_details` | `dict \| None` | Per-approach diagnostic payload — `None` unless `show_analysis_details=True`. See [Key Analysis Details Schema](#key-analysis-details-schema) |

**Properties:**

- `key_hint -> str` — Formats `"<tonic> <mode>"` from the local key, compatible with `PatternAnalysisService.analyze_with_patterns_async(key_hint=...)`. Maps K-S labels (Ionian/Aeolian) to standard names (major/minor). Returns `"C major"` for the zero-energy sentinel.

**Methods:**

- `chords_as_symbols() -> list[str]` — Extracts `chord_label` from each `ChordEvent`. The resulting list is directly compatible with `PatternAnalysisService.analyze_with_patterns_async(chord_symbols=...)`.

### `KeyInfo`

Result of Krumhansl-Schmuckler key estimation.

| Field | Type | Description |
|-------|------|-------------|
| `tonic` | `str` | Estimated tonic note name (e.g. `"C"`, `"F#"`) |
| `mode` | `str` | Estimated mode (`"Ionian"` or `"Aeolian"`) |
| `key_signature` | `str` | Formatted key string (e.g. `"C Ionian"`) |
| `confidence` | `float` | Correlation coefficient from K-S profile matching |
| `diatonic_pitch_classes` | `frozenset[int]` | Derived field — pitch-class integers for the diatonic scale. **Not JSON-serializable.** Computed from `tonic` + `mode` in `__post_init__` |

> **Warning:** `diatonic_pitch_classes` is a `frozenset`. Passing a `KeyInfo` through `dataclasses.asdict()` and then to a JSON serializer will raise `TypeError`. Always build response dicts manually when serializing `KeyInfo`.

### `CadenceInfo`

Result of cadence detection on a chroma segment.

| Field | Type | Description |
|-------|------|-------------|
| `detected` | `bool` | Whether a V-I cadence pattern was found |
| `strength` | `float` | Strength of the detected cadence (0.0-1.0) |

### `RegionInfo`

Region classification comparing local segment against global key.

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | One of `"stable"`, `"modulation"`, `"modal_shift"` |
| `confidence` | `float` | Classification confidence (0.0-1.0) |
| `borrowed` | `list[str]` | Pitch-class names of tones present locally but absent from the global diatonic set |

### `ChordEvent`

A single timestamped chord detection.

| Field | Type | Description |
|-------|------|-------------|
| `start_time` | `float` | Start time in seconds |
| `end_time` | `float` | End time in seconds |
| `chord_label` | `str` | Detected chord symbol (e.g. `"C"`, `"Am"`, `"Gm"`) |
| `confidence` | `float` | Cosine similarity (post-tonal-bias) averaged over constituent windows |
| `is_diatonic` | `bool` | Whether the chord root belongs to the global key's diatonic pitch-class set |

## Exceptions

### `AudioImportError`

Subclass of `ImportError`. Raised when `librosa` or `soundfile` are not installed. The message contains the strings `"audio"` and `"pip install"` for grep-friendly install guidance.

```python
from harmonic_analysis import AudioImportError

try:
    result = analyze_audio("song.wav")
except AudioImportError:
    print("Install with: pip install harmonic-analysis[audio]")
```

## Key Detection Ensemble

As of audio_score_alignment-02, the audio pipeline uses an ensemble of independent key-detection approaches that vote on the final key verdict. The single-algorithm Krumhansl-Schmuckler estimator can't reliably tell relative major/minor pairs apart (D Ionian vs B Aeolian have identical pitch-class sets); orthogonal evidence from boundary chords, bass dominance, and cadential motion breaks those ties.

### Approach Catalog (iteration_01)

| Approach | Default? | Default weight | What it does |
|----------|----------|----------------|--------------|
| `template_correlation` | Yes | 1.0 | The original K-S correlation against pitch-class profiles. Foundational; everyone else breaks its ties |
| `boundary_chords` | Yes | 0.8 | Scores keys by whether the first/last chord events match the candidate's tonic (or dominant) |
| `bass_dominance` | Yes | 0.6 | Aggregates the bass chroma over the whole segment, scores keys by tonic + dominant emphasis |
| `cadential` | Yes | 0.7 | Counts V→I (major) / V→i (minor) transitions in the chord-event sequence |
| `pattern_engine` | No (iteration_02) | 0.9 | Calls `PatternAnalysisService` per top-K candidate key; returns its confidence |
| `hmm` | No (iteration_02) | 0.5 | Viterbi over a 24-state key HMM; produces local-key segments for modulating music |

### Presets

The `key_detection` parameter accepts these preset strings:

- `"default"` — runs `template_correlation`, `boundary_chords`, `bass_dominance`, and `cadential`. The recommended setting for most use cases.
- `"ks_only"` — runs only `template_correlation`. Mirrors the pre-ensemble code path; use this to recover the exact behavior of versions before audio_score_alignment-02.
- `"full"` — runs every approach including the iteration_02 opt-ins. Currently equivalent to `"default"` until iteration_02 ships the opt-ins.

You can also pass an explicit list of approach names (`["template_correlation", "boundary_chords"]`) or a dict mapping name → weight (`{"template_correlation": 1.5, "cadential": 0.0}`).

### Two-Stage Orchestration

The chord estimator needs a key (for `tonal_bias`), and the chord-event-based approaches (`boundary_chords`, `cadential`) need chord events. The pipeline resolves this circularity in two stages:

1. **Stage 1:** Run `template_correlation` alone on the global chroma → `ks_key`.
2. **Stage 2:** Use `ks_key` to bias chord estimation. Output: chord events.
3. **Stage 3:** Run the full ensemble with chord events available. Output: `ensemble_key`.
4. **Stage 4:** `result.global_key = ensemble_key`.

The chord estimator's `tonal_bias` still uses the stage-1 K-S result (not the ensemble winner). For relative pairs this is lossless because both keys share the same diatonic set.

### Key Analysis Details Schema

When `show_analysis_details=True`, `result.key_analysis_details` is populated with this structure:

```python
{
    "approaches": [
        {
            "name": "template_correlation",
            "weight": 1.0,
            "top_3": [
                {"key": {"tonic": "B", "mode": "Aeolian", ...}, "score": 0.957},
                ...
            ],
        },
        # ... one entry per enabled approach
    ],
    "synthesis": {
        "method": "weighted_sum",
        "winner": {"tonic": "B", "mode": "Aeolian", ...},
        "runner_up": {"tonic": "D", "mode": "Ionian", ...},
        "margin": 0.483,
        "key_score_table": {"B Aeolian": 2.51, "D Ionian": 2.03, ...},
    },
    "modulations": None,  # iteration_02 will populate this when HMM is on
}
```

When `show_analysis_details=False` (the default), `result.key_analysis_details is None` — no payload bloat for production callers.

### Backward Compatibility

The old `find_best_key` import path (`from harmonic_analysis.audio._key_estimation import find_best_key`) still works and produces bit-identical results to pre-ensemble behavior. To get the same end-to-end behavior as before the ensemble shipped, pass `key_detection="ks_only"`.

## See Also

- [Core API Reference](api-reference.md) — pattern analysis, scale/melody analysis, musical data API
- [Audio Quick Start](../tutorials/audio-quickstart.md) — 5-minute hands-on tutorial
- [How to Analyze Audio](../how-to/audio-analysis.md) — task-oriented guide
- [Audio Internals](../explanation/audio-analysis-internals.md) — design rationale
