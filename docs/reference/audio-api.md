# Audio API Reference

Field-by-field reference for the audio analysis surface. For the core pattern analysis API, see [api-reference.md](api-reference.md).

## Module-Level Convenience Functions

### `analyze_audio(path, *, segment=None, quiet=False, include_chords=True, chord_window_size_s=None, chord_hop_size_s=None, tonal_bias=0.15, rubato="moderate", use_bass_chroma=False, bass_bonus=0.3, min_chroma_norm=0.05)`

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

**Returns:** `AudioAnalysisResult`

**Raises:**
- `AudioImportError` — if `librosa` or `soundfile` are not installed
- `ValueError` — for empty or too-short segments

### `analyze_audio_async(path, *, segment=None, quiet=False, include_chords=True, chord_window_size_s=None, chord_hop_size_s=None, tonal_bias=0.15, rubato="moderate", use_bass_chroma=False, bass_bonus=0.3, min_chroma_norm=0.05)`

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
| `global_key` | `KeyInfo` | K-S key estimate over the whole file |
| `local_key` | `KeyInfo` | K-S key estimate over the analyzed segment |
| `cadences` | `CadenceInfo` | V-I cadence detection result |
| `region` | `RegionInfo` | Region classification (stable / modulation / modal_shift) |
| `chords` | `list[ChordEvent]` | Timestamped chord events (empty if `include_chords=False`) |
| `segment_start` | `float` | Start of analyzed segment in seconds |
| `segment_end` | `float` | End of analyzed segment in seconds |

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

## See Also

- [Core API Reference](api-reference.md) — pattern analysis, scale/melody analysis, musical data API
- [Audio Quick Start](../tutorials/audio-quickstart.md) — 5-minute hands-on tutorial
- [How to Analyze Audio](../how-to/audio-analysis.md) — task-oriented guide
- [Audio Internals](../explanation/audio-analysis-internals.md) — design rationale
