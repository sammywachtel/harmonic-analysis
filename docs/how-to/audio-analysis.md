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

## See Also

- **[Audio Quick Start Tutorial](../tutorials/audio-quickstart.md)** — 5-minute hands-on introduction
- **[Audio API Reference](../reference/audio-api.md)** — field-by-field documentation
- **[Audio Analysis Internals](../explanation/audio-analysis-internals.md)** — why the pipeline works the way it does
