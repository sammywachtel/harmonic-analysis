# Audio Analysis Quick Start

A 5-minute hands-on walkthrough: install the audio extra, point it at a WAV file, and see what comes back.

## Prerequisites

- Python 3.10+
- A working `harmonic-analysis` installation (see [Getting Started](getting-started.md))

## Step 1 — Install the Audio Extra

```bash
pip install harmonic-analysis[audio]
```

This pulls in `librosa` (signal processing) and `soundfile` (audio I/O). If you plan to analyze MP3 or AAC files, you also need `ffmpeg` on your PATH — WAV works without it.

## Step 2 — Get or Create a Sample File

Any WAV file will do. If you don't have one handy, generate a quick test tone:

```python
import numpy as np
import soundfile as sf

sr = 22050
t = np.linspace(0, 3.0, int(sr * 3.0), endpoint=False)
# A major chord: A4 + C#5 + E5
signal = (
    0.4 * np.sin(2 * np.pi * 440 * t)
    + 0.3 * np.sin(2 * np.pi * 554.37 * t)
    + 0.3 * np.sin(2 * np.pi * 659.25 * t)
)
sf.write("sample.wav", signal, sr)
```

## Step 3 — Run the Analysis

```python
import asyncio
from harmonic_analysis import analyze_audio_async

async def main():
    result = await analyze_audio_async("sample.wav")

    print(f"Global key: {result.global_key.tonic} {result.global_key.mode}")
    print(f"  Confidence: {result.global_key.confidence:.2f}")
    print(f"Cadence detected: {result.cadences.detected}")
    print(f"Region type: {result.region.type}")
    print(f"Chords found: {len(result.chords)}")

    for chord in result.chords[:5]:
        print(
            f"  [{chord.start_time:.2f}-{chord.end_time:.2f}] "
            f"{chord.chord_label} (conf={chord.confidence:.2f}, "
            f"diatonic={chord.is_diatonic})"
        )

asyncio.run(main())
```

## Step 4 — Understand the Output

| Field | What it tells you |
|-------|-------------------|
| `global_key` | Krumhansl-Schmuckler key estimate over the whole file |
| `local_key` | Key estimate for the analyzed segment (same as global when no segment is given) |
| `cadences` | Whether a V-I cadence was detected and how strong it is |
| `region` | Whether the segment is stable, a modulation, or a modal shift |
| `chords` | Timestamped chord events with template-matching confidence |
| `segment_start` / `segment_end` | The time window that was analyzed (seconds) |

The `key_hint` property on the result formats a service-ready string like `"A major"` that you can pass directly to `PatternAnalysisService.analyze_with_patterns_async(key_hint=...)` for follow-up pattern analysis.

## What's Next

- **[How to analyze audio files](../how-to/audio-analysis.md)** — task-oriented guide with segment windowing, MP3 setup, and toolkit integration recipes
- **[Audio API Reference](../reference/audio-api.md)** — field-by-field documentation for every dataclass and function
- **[Audio Analysis Internals](../explanation/audio-analysis-internals.md)** — why the pipeline makes the choices it does
