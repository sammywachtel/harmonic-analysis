# Audio Analysis Internals

Design rationale for the audio analysis pipeline. This document explains *why* the pipeline makes the choices it does, not *how* to use it (see [How to Analyze Audio](../how-to/audio-analysis.md)) or *what* the API looks like (see [Audio API Reference](../reference/audio-api.md)).

## Why Krumhansl-Schmuckler for Key Estimation

The Krumhansl-Schmuckler (K-S) algorithm correlates a chroma vector against psychoacoustically derived key profiles. It was chosen for several reasons:

1. **Simplicity.** K-S is a single dot-product per candidate key — 24 correlations total (12 major + 12 minor). This keeps inference fast enough for real-time segment analysis.
2. **Well-studied failure modes.** K-S has been benchmarked extensively in MIR literature. Its biases are predictable: it overestimates major keys for ambiguous inputs and struggles with modal music. Knowing the failure modes lets us compensate downstream.
3. **No training data required.** The key profiles are fixed constants, not learned parameters. This avoids the cold-start problem and makes results deterministic.

The primary limitation is that K-S only distinguishes major (Ionian) from minor (Aeolian). It cannot detect Dorian, Mixolydian, or other modes directly. The pattern engine handles modal detection in a second pass, using the K-S result as a starting hypothesis.

## How Template Matching Works for Chord Estimation

The chord estimation layer slides a window across the 2D chroma matrix `(12, T)` and computes the cosine similarity between each window's chroma and a set of chord templates (major, minor, diminished, augmented triads and dominant 7ths).

### Template construction

Each template is a 12-dimensional binary vector with 1s at the chord tones and 0s elsewhere. For example, a C major template has 1s at pitch classes 0 (C), 4 (E), and 7 (G).

### Tonal bias

Before comparison, the cosine similarity for chords that are diatonic to the estimated global key receives a small additive bonus (default: 0.15). This breaks ties in favor of diatonic interpretations, which is the musically correct default for most tonal music.

### Limitations

- **Only major/minor triads and dom7 for v1.** The template set intentionally omits diminished, augmented, and extended chords. Adding them would increase false positives more than it would improve recall — the chroma resolution of most audio is too coarse to distinguish, say, Cmaj7 from C.
- **No voice leading.** Templates treat each window independently. A proper chord tracker would use Viterbi decoding or HMM smoothing across windows, which is a natural v2 extension.
- **Polyphonic music only.** Monophonic lines produce very sparse chroma and the cosine metric degenerates. For monophonic analysis, use the melody pipeline instead.

## When to Trust the Chord Layer

**Trust it when:**
- The audio is polyphonic (guitar strumming, piano, ensemble)
- The recording is relatively clean (low reverb, no heavy distortion)
- Chord confidence values are above 0.6

**Be skeptical when:**
- Confidence is below 0.4 — the pipeline is guessing
- `is_diatonic` is `False` for most chords — this may indicate the global key estimate is wrong rather than the music being chromatic
- The audio is heavily processed (autotune, vocoder, heavy compression)

## Why the Tonal Bias Defaults to 0.15

The tonal bias parameter (`tonal_bias=0.15`) was tuned empirically against a corpus of pop and classical recordings. The tradeoffs:

- **0.0 (no bias):** Pure cosine similarity. Works well for chromatic jazz and atonal music, but produces noisy results for tonal music because diatonic and chromatic chords compete on equal footing.
- **0.10-0.20:** Sweet spot for most Western tonal music. Diatonic chords win ties without suppressing genuinely chromatic passages.
- **0.30+:** Over-biased. Starts forcing diatonic interpretations on passages that are genuinely chromatic. Secondary dominants and borrowed chords get misclassified.

The default of 0.15 biases toward diatonic interpretations just enough to smooth out noise without hiding interesting chromatic harmony. You can adjust it per call:

```python
# Analyzing chromatic jazz — reduce tonal bias
result = await analyze_audio_async("coltrane.wav", tonal_bias=0.05)

# Analyzing a hymn — increase tonal bias
result = await analyze_audio_async("hymn.wav", tonal_bias=0.25)
```

## The Segment Parameter as a Future-Windowing Seam

The `segment=(start, end)` parameter currently selects a single contiguous time window for analysis. This is a deliberate architectural seam for future windowed analysis:

- **v1 (current):** Caller specifies one segment; pipeline analyzes it as a unit.
- **v2 (planned):** A higher-level orchestrator could slice a file into overlapping windows, call `from_audio(segment=...)` for each, and stitch the results into a time-varying key/chord track. The single-segment API is the primitive that makes this possible without requiring changes to the core pipeline.

The segment bounds appear in the result as `segment_start` and `segment_end`, making it straightforward to align results from multiple calls.

## Diatonic-Only Quality Claim for v1

The v1 audio pipeline makes a deliberate quality/scope tradeoff: it only claims to reliably detect **diatonic** harmony (major and minor triads, dominant 7ths, within a major or minor key).

What this means in practice:
- Modal music (Dorian, Mixolydian, etc.) gets the correct *key signature* but the mode label will be "Ionian" or "Aeolian" — the K-S algorithm cannot distinguish modes. Pass the result through `PatternAnalysisService` for proper modal detection.
- Extended chords (maj7, min9, sus4) are simplified to their nearest triad or dom7 template. This is lossy but intentional — chroma resolution in most audio is insufficient for reliable extended chord detection.
- Chromatic passages (augmented sixths, Neapolitan chords, tritone subs) will be detected as whatever diatonic chord their chroma most resembles. The `is_diatonic=False` flag on individual `ChordEvent` entries signals when the pipeline is less confident about diatonic membership.

This is not a permanent limitation — it is the honest boundary of what template-matching on chroma can deliver without HMM smoothing or neural network chord recognition. Future iterations will extend the quality boundary outward.

## Bass-Chroma Disambiguation

Standard chroma extraction collapses all octaves into a single 12-bin vector. This works beautifully for most chords, but it creates a blind spot: chords that share the same pitch-class content but differ in their bass note become indistinguishable. The classic case is **Bm (B-D-F#) vs. D major (D-F#-A)** — when both are voiced with shared tones ringing, the chroma vectors overlap enough that cosine similarity alone cannot reliably separate them.

Bass-chroma extraction (`use_bass_chroma=True`) addresses this by computing a second chroma vector from only the low-frequency band (roughly below 300 Hz). The bass note stands out clearly in this range, providing a strong disambiguating signal. The `bass_bonus` parameter (default 0.3) sets the maximum weight this bass evidence can contribute when scoring candidate chord labels — for templates whose root matches the bass chroma peak, the bonus is added to the cosine similarity, scaled per-window by the bass-chroma confidence so that ambiguous bass detections contribute less.

### Why the Default is `False`

Honest answer: bass-chroma extraction helps a lot on clean recordings with well-separated bass lines (acoustic jazz trio, classical piano) but can hurt on recordings where the bass frequencies are muddy, boosted, or dominated by kick drum. We have not yet validated across a broad enough corpus to make it the default. For now, it is an opt-in tool for users who know their recordings have a clean, prominent bass.

## Silent-Window Suppression

Live recordings, rehearsal tapes, and bedroom demos frequently have silent lead-ins, long pauses between movements, or near-silence during fermatas. The chord estimation layer does not know about silence — it dutifully slides its window across the chroma matrix and picks the best-matching template for every window, even when the chroma energy is essentially noise floor.

The result: phantom chord labels during silence. A quiet room-tone window might produce a confident-looking "Am" label simply because the ambient noise happened to correlate with that template. These phantom labels are misleading and can confuse downstream pattern analysis.

### How the L2 Norm Threshold Works

The `min_chroma_norm` parameter sets a minimum L2 (Euclidean) norm threshold for each analysis window's chroma vector. Before template matching, the pipeline computes `||chroma||₂` for the window. If the norm falls below the threshold, the window is classified as silence and skipped — no `ChordEvent` is emitted.

### Why 0.05

The default of `0.05` was chosen to be conservative:

- **Below 0.05:** Genuine silence, microphone self-noise, room tone. There is no musical content to analyze.
- **0.05–0.15:** The gray zone. Very quiet *pianissimo* passages live here, as do some near-silent transitions. The default preserves these, erring on the side of keeping real (if quiet) musical content.
- **Above 0.15:** Clearly audible musical content. No risk of suppression.

If your recordings have unusual noise floors (e.g., a live concert with ambient crowd noise, or a recording with a persistent hum), you may need to raise the threshold. Conversely, if you are analyzing extremely quiet passages and losing chord events, lower it toward `0.0` — but expect some phantom labels to creep back in.

## See Also

- [Audio API Reference](../reference/audio-api.md) — field-by-field documentation
- [How to Analyze Audio](../how-to/audio-analysis.md) — task-oriented guide
- [Audio Quick Start](../tutorials/audio-quickstart.md) — hands-on tutorial
