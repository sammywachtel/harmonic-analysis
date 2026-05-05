# Troubleshooting

Common errors and how to fix them.

## Imports and installation

### `ImportError` when running audio analysis

**Symptom:**
```python
>>> from harmonic_analysis import analyze_audio_async
>>> await analyze_audio_async("song.wav")
AudioImportError: The audio extra is required for audio analysis. Install with: pip install harmonic-analysis[audio]
```

**Cause:** The library imports without errors even when audio dependencies (`librosa`, `soundfile`) are missing — the symbols are exported as stubs that raise on first use. This keeps the bare `import harmonic_analysis` cheap.

**Fix:**
```bash
pip install harmonic-analysis[audio]
```

If MP3/AAC files don't load after that, you also need `ffmpeg` on the system PATH. Install with `brew install ffmpeg` (macOS), `apt install ffmpeg` (Debian/Ubuntu), or [download a build](https://ffmpeg.org/download.html) for Windows.

### `ModuleNotFoundError: No module named 'src'`

**Symptom:** Code copied from a doc or older example uses `from src.harmonic_analysis.X import Y`.

**Cause:** The `src.` prefix only works when running from the repo root with `PYTHONPATH=src`. Pip-installed users don't have that.

**Fix:** Use `from harmonic_analysis.X import Y`. The `src.` prefix never belongs in user code.

### Importing internal modules works but isn't supported

**Symptom:** You imported `PatternEngine`, `MultipleInterpretationService`, `EnhancedModalAnalyzer`, `FunctionalHarmonyAnalyzer`, or similar directly from internal paths.

**Cause:** These are internal components. The `__all__` list in `harmonic_analysis/__init__.py` is the supported public surface. Internal classes can change without notice.

**Fix:** Use the public services:

```python
# Internal (avoid):
from harmonic_analysis.core.pattern_engine import PatternEngine
from harmonic_analysis.core.functional_harmony import FunctionalHarmonyAnalyzer

# Public (use these):
from harmonic_analysis import PatternAnalysisService, UnifiedPatternService
```

## Result-shape gotchas

### `AttributeError: 'AnalysisEnvelope' object has no attribute 'primary_analysis'`

**Cause:** Older code or docs used `result.primary_analysis` and `result.alternative_analyses`. The current return type, `AnalysisEnvelope`, uses `.primary` and `.alternatives`.

**Fix:**

```python
# Old (broken):
result.primary_analysis.confidence
result.alternative_analyses

# Current:
result.primary.confidence
result.alternatives
```

### `AttributeError: 'AnalysisEnvelope' object has no attribute 'metadata'`

**Cause:** `AnalysisEnvelope` does not have a single `metadata` field. Metadata is split across named fields.

**Fix:**

```python
result.analysis_time_ms     # Optional[float]
result.chord_symbols        # List[str] — echo of the input
result.evidence             # List[EvidenceDTO]
result.schema_version       # str — e.g. "1.0"
```

### `TypeError: Object of type frozenset is not JSON serializable`

**Cause:** `KeyInfo` (returned by audio analysis) carries a `diatonic_pitch_classes` field that is a `frozenset`. Naively serializing it via `dataclasses.asdict()` and `json.dumps()` raises.

**Fix:** Build the response dict manually:

```python
key_dict = {
    "tonic": result.global_key.tonic,
    "mode": result.global_key.mode,
    "key_signature": result.global_key.key_signature,
    "confidence": result.global_key.confidence,
}
```

The demo backend in `demo/backend/rest_api/routes.py` does this for every audio response — copy that pattern if you're building your own REST layer.

## Async / sync confusion

### `RuntimeError: This event loop is already running`

**Cause:** You called the sync `analyze_with_patterns()` from inside an already-running event loop (e.g., from inside a Jupyter cell, or from inside another async function).

**Fix:** Use the async version:

```python
result = await service.analyze_with_patterns_async(...)
```

The sync wrapper handles "no loop running" cases by spinning up its own; if you're already in a loop, `await` the async method directly.

### Sync code, but I want async-style throughput

```python
import asyncio

async def batch():
    service = PatternAnalysisService()
    return await asyncio.gather(*[
        service.analyze_with_patterns_async(prog, profile="classical")
        for prog in progressions
    ])

results = asyncio.run(batch())
```

## Analysis quality

### "The library returned modal analysis but I expected functional"

**Likely cause:** No `key_hint`. Without explicit key context, the engine picks the analysis type that best fits the chord set. If the progression is also a valid modal interpretation (e.g., `Dm7 G7 Cmaj7` could be ii-V-I or D Dorian vamp), modal sometimes wins.

**Fix:** Pass `key_hint`:

```python
result = await service.analyze_with_patterns_async(
    chord_symbols=["Dm7", "G7", "Cmaj7"],
    key_hint="C major",
    profile="classical",
)
# Now produces functional analysis with Roman numerals.
```

The library will also surface a `parent_key_suggestions` entry on the envelope when adding a key would unlock better analysis.

### "Confidence is below 0.5 — should I trust this?"

**Use case-by-case judgment:**

- **Below 0.4** — the library is uncertain. Try adding a `key_hint`, lengthening the progression, or checking that the input is actually within Western tonal/modal harmony.
- **0.4–0.6** — multiple interpretations are valid. Look at `result.alternatives`; sometimes the second-place interpretation is the one you wanted.
- **Above 0.6** — solid. The reasoning string explains why.

### Audio analysis returned the wrong key

**For relative-pair confusion (e.g., D major when you wanted B minor):**
The default ensemble specifically disambiguates relative pairs. If you're getting the wrong one, turn on the diagnostic panel and inspect:

```python
result = await analyze_audio_async("song.wav", show_analysis_details=True)

for approach in result.key_analysis_details["approaches"]:
    print(approach["name"], approach["weight"])
    for entry in approach["top_3"]:
        print(" ", entry["key"]["tonic"], entry["key"]["mode"], entry["score"])

print("Synthesis margin:", result.key_analysis_details["synthesis"]["margin"])
```

A small margin (< 0.1) means the ensemble was close to picking the relative pair partner. See [How to Analyze Audio](audio-analysis.md) for tuning options (`key_ensemble_weights`, weight overrides).

**For "the K-S baseline got it right but the ensemble didn't":**
Run with `key_detection="ks_only"` and see if it differs:

```python
ks = await analyze_audio_async("song.wav", key_detection="ks_only")
ensemble = await analyze_audio_async("song.wav", key_detection="default")
```

If they agree, the bug isn't in the ensemble. If they disagree, file an issue with the diagnostic panel output and a representative recording.

### "No chord events detected"

**Causes:**
- The clip is shorter than the chord-estimation window.
- The audio is below the silence threshold (`min_chroma_norm=0.05` by default).
- `include_chords=False` was passed.

**Fix:** Pass a longer segment, lower `min_chroma_norm`, or check `include_chords=True`. Single-instrument lines (solo melody, percussion-only) don't produce reliable chord estimates by design.

## Where to ask for help

- **Bug reports / unexpected results:** open an issue at <https://github.com/sammywachtel/harmonic-analysis/issues> with a minimal reproducer (input, expected, actual).
- **Feature requests:** same place — describe the use case, not just the feature.
- **Understanding what the engine did:** [Debugging Patterns](debugging-patterns.md) and [Architecture Overview](../explanation/architecture.md) explain the internals.

## See also

- [API Quick Reference](../reference/api-quick-reference.md)
- [Debugging Patterns](debugging-patterns.md)
- [Audio Analysis Guide](audio-analysis.md)
