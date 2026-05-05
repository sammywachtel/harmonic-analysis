# How to Analyze Audio Files

Task-oriented guide for audio analysis with the harmonic-analysis library.

## How to Analyze an Audio File

```python
from harmonic_analysis import analyze_audio_async

result = await analyze_audio_async("song.wav")
print(f"Key: {result.global_key.tonic} {result.global_key.mode}")
print(f"Chords: {result.chords_as_symbols()}")
```

To analyze only a portion of the file, pass a `segment` tuple of `(start_seconds, end_seconds)`:

```python
# Analyze just the first 30 seconds
result = await analyze_audio_async("song.wav", segment=(0.0, 30.0))

# Analyze from 60 seconds to end of file
result = await analyze_audio_async("song.wav", segment=(60.0, None))
```

There is also a synchronous wrapper if you are not in an async context:

```python
from harmonic_analysis import analyze_audio

result = analyze_audio("song.wav")
```

## How to Chain Audio Analysis into Pattern Analysis

The audio pipeline produces key estimation and chord symbols. Feed those into the pattern engine for full harmonic analysis:

```python
from harmonic_analysis import analyze_audio_async, PatternAnalysisService

# Step 1: Extract key + chords from audio
audio_result = await analyze_audio_async("song.wav")

# Step 2: Feed into the pattern engine
service = PatternAnalysisService()
pattern_result = await service.analyze_with_patterns_async(
    chord_symbols=audio_result.chords_as_symbols(),
    key_hint=audio_result.key_hint,
    profile="classical",
)

print(f"Roman numerals: {' - '.join(pattern_result.primary.roman_numerals)}")
```

## Toolkit Migration Recipe

If you are migrating from a toolkit that expects a `ModeAnalysisResponse`-shaped dict, use this wrapper to bridge the audio pipeline into that shape:

```python
# toolkit-wrapper-recipe-start
from harmonic_analysis import analyze_audio_async


async def run_wrapper(audio_path):
    """Bridge audio pipeline output to ModeAnalysisResponse shape."""
    result = await analyze_audio_async(audio_path)

    result_dict = {
        "global": {
            "tonic": result.global_key.tonic,
            "mode": result.global_key.mode,
        },
        "local": {
            "region_type": result.region.type,
        },
        "analysis": {
            "borrowed_tones": list(result.region.borrowed),
            "cadence_detected": result.cadences.detected,
            "chromagram_summary": [0.0] * 12,
        },
        "visuals": [],
    }
    return result_dict
# toolkit-wrapper-recipe-end
```

### Serialization Gap: `visuals`

The toolkit's `ModeAnalysisResponse.visuals` field expects `List[VisualizationItem]` — matplotlib-generated plots. The harmonic-analysis library intentionally has no matplotlib dependency, so the audio pipeline does not produce visualization data.

**Options:**

- **(a)** Compute visuals locally in your wrapper using the original plot functions from the toolkit.
- **(b) RECOMMENDED:** Make `visuals: Optional[List[VisualizationItem]] = None` in the toolkit's Pydantic model. This keeps the wrapper under 15 lines and matplotlib out of the library.

Option (b) is recommended because `visuals` is a presentation concern, not a data contract. Keeping visualization logic in the toolkit where the plots are rendered avoids coupling the analysis library to a rendering framework.

### Serialization Gap: `chromagram_summary`

The toolkit's `AnalysisDetails.chromagram_summary` field expects `List[float]` — a 12-bin chroma energy vector. The library's audio pipeline uses chroma internally for key estimation but does not currently expose the raw chroma vector in the public result.

**Options:**

- **(a)** Derive the chroma locally from librosa in your wrapper:
  ```python
  import librosa
  y, sr = librosa.load(audio_path)
  chroma = librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1).tolist()
  ```
- **(b) RECOMMENDED:** Make `chromagram_summary: Optional[List[float]] = None` in the toolkit model.

Option (b) is recommended because the chroma summary is a visualization aid for the frontend, not a load-bearing analysis contract. Making it optional avoids redundant computation and keeps the wrapper simple.

## How to Handle MP3 Files

MP3, AAC, and OGG decoding requires `ffmpeg` on your system PATH. WAV files work without it.

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows (Chocolatey):**
```bash
choco install ffmpeg
```

The library checks for ffmpeg at construction time and logs a warning if it is missing. You can suppress the warning with `quiet=True`:

```python
result = await analyze_audio_async("song.mp3", quiet=True)
```

## How to Interpret Chord Confidence and `is_diatonic`

Each `ChordEvent` in the result includes:

- **`confidence`** — Cosine similarity between the audio chroma and the chord template, after tonal bias adjustment. Values above 0.7 are strong matches; below 0.4 are speculative.
- **`is_diatonic`** — Whether the detected chord belongs to the estimated global key. Non-diatonic chords may indicate borrowed chords, secondary dominants, or modulation.

```python
for chord in result.chords:
    status = "diatonic" if chord.is_diatonic else "chromatic"
    print(f"{chord.chord_label}: {chord.confidence:.2f} ({status})")
```

High confidence + non-diatonic is often the most interesting signal — it suggests intentional chromatic harmony rather than noise.

## Tuning for Different Recording Styles

Not all recordings are created equal. A studio pop track recorded to a click track and a Romantic-era piano recital with dramatic rubato need very different analysis settings. The `rubato` parameter controls how aggressively the pipeline smooths chord transitions — think of it as a "temporal flexibility" knob.

### Which `rubato` Preset Should I Use?

Pick the one that best describes your recording:

| Recording style | Preset | Why |
|---|---|---|
| Studio recording with click track | `rubato="strict"` | Tight timing means chord boundaries are predictable — minimal smoothing preserves detail |
| Live performance, moderate tempo | `rubato="moderate"` (default) | Slight timing drift but generally steady — the default handles this well |
| Chamber music, expressive timing | `rubato="loose"` | Players push and pull tempo together — wider smoothing catches stretched chords |
| Heavy rubato, fermatas, very slow passages | `rubato="free"` | Maximum smoothing for recordings where the beat is more of a suggestion |
| Fine-grained control | Float `0.0` – `1.0` | `0.0` = tightest (like strict), `1.0` = loosest (like free). Interpolate to taste |

```python
# A Chopin nocturne with plenty of rubato
result = await analyze_audio_async("chopin_nocturne.wav", rubato="free")

# A pop track with solid timing
result = await analyze_audio_async("pop_song.wav", rubato="strict")

# Somewhere in between — maybe a live jazz trio
result = await analyze_audio_async("jazz_trio.wav", rubato=0.65)
```

### Bass-Aware Chord Estimation

If your recording has a clear bass line (upright bass, bass guitar, left-hand piano), enable `use_bass_chroma=True` to help the pipeline distinguish chords that share upper chord tones but differ in the bass — Bm vs D, for instance:

```python
result = await analyze_audio_async("bass_heavy.wav", use_bass_chroma=True)
```

This is off by default because it needs more validation across diverse recordings, but it can meaningfully improve accuracy when the bass is prominent and well-separated in the mix.

### Adjusting Silence Detection

Recordings with long silences, count-ins, or very quiet passages may produce phantom chord labels where the pipeline tries to classify near-silence. The `min_chroma_norm` parameter sets the minimum energy threshold — windows below it are treated as silence:

```python
# More aggressive silence filtering for a recording with a long lead-in
result = await analyze_audio_async("live_recording.wav", min_chroma_norm=0.10)
```

The default (`0.05`) is conservative: it catches genuine silence and room tone while preserving *pianissimo* dynamics. Raise it if you see suspicious chord labels during quiet passages; lower it (toward `0.0`) only if you are losing legitimate soft chords.

## How to Debug a Wrong Key Verdict

If the analyzer returns a key that doesn't match what you hear in the recording — D major when you swear it's in B minor, for instance — the relative-pair confusion problem is usually the culprit. The audio pipeline ships an ensemble of independent key-detection approaches that vote on the verdict; turning on the diagnostic panel shows you why each approach voted the way it did.

### Step 1: Enable `show_analysis_details`

```python
from harmonic_analysis import analyze_audio_async

result = await analyze_audio_async(
    "song.wav",
    show_analysis_details=True,
)

print(f"Verdict: {result.global_key.tonic} {result.global_key.mode}")
for approach in result.key_analysis_details["approaches"]:
    print(f"\n{approach['name']} (weight={approach['weight']}):")
    for entry in approach["top_3"]:
        key = entry["key"]
        print(f"  {key['tonic']} {key['mode']:<8}  score={entry['score']:.3f}")

synth = result.key_analysis_details["synthesis"]
print(f"\nSynthesis: {synth['winner']['tonic']} {synth['winner']['mode']} "
      f"(runner-up: {synth['runner_up']['tonic']} {synth['runner_up']['mode']}, "
      f"margin: {synth['margin']:.3f})")
```

### Step 2: Read the panel

A typical "wrong K-S, right ensemble" pattern looks like this:

```
template_correlation (weight=1.0):
  D Ionian        score=0.930
  F# Aeolian      score=0.884
  B Aeolian       score=0.882

boundary_chords (weight=0.8):
  B Aeolian       score=0.714
  B Ionian        score=0.357
  E Ionian        score=0.286

bass_dominance (weight=0.6):
  B Ionian        score=0.179
  B Aeolian       score=0.179
  F# Ionian       score=0.170

cadential (weight=0.7):
  D Ionian        score=1.000
  G Aeolian       score=1.000
  B Aeolian       score=1.000

Synthesis: B Aeolian (runner-up: D Ionian, margin: 0.483)
```

K-S alone returns D Ionian with high confidence — that's the relative-pair problem. The boundary_chords approach correctly notices the song starts and ends on Bm; bass_dominance sees B in the bass; cadential picks up the V→i pattern. Together they outweigh K-S and the synthesis lands on B Aeolian.

### Step 3: Override weights if needed

If the default weights don't suit your repertoire (e.g., a corpus where boundary chords are unreliable but the bass is rock-solid), pass custom weights:

```python
result = await analyze_audio_async(
    "song.wav",
    show_analysis_details=True,
    key_ensemble_weights={
        "boundary_chords": 0.4,  # weaker
        "bass_dominance": 1.2,   # stronger
    },
)
```

Approaches not listed retain their default weight; the override is additive, not replacement.

### Step 4: Compare against `ks_only`

To see what the pre-ensemble code path would have returned:

```python
ks_result = await analyze_audio_async("song.wav", key_detection="ks_only")
print(f"K-S only: {ks_result.global_key.tonic} {ks_result.global_key.mode}")
```

This is the migration backstop — if your test suite previously asserted D major on a recording that's audibly B minor, the assertion was actually checking K-S behavior, and you can pin it via `key_detection="ks_only"` while the rest of your code uses the ensemble.

### CLI Workflow

The same diagnostic flow works from the command line:

```bash
python scripts/try_audio.py song.wav --show-analysis-details

# Override weights from the CLI
python scripts/try_audio.py song.wav --show-analysis-details \
    --ensemble-weights '{"boundary_chords": 0.4, "bass_dominance": 1.2}'

# Compare ensemble vs K-S-only on the same file
python scripts/try_audio.py song.wav
python scripts/try_audio.py song.wav --key-detection ks_only
```

## See Also

- **[Audio Quick Start Tutorial](../tutorials/audio-quickstart.md)** — 5-minute hands-on introduction
- **[Audio API Reference](../reference/audio-api.md)** — field-by-field documentation
- **[Audio Analysis Internals](../explanation/audio-analysis-internals.md)** — why the pipeline works the way it does
