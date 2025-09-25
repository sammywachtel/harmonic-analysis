# Enhancements with Music21 Integration

## Score Ingestion and Normalization
- Use `converter.parse` to accept MusicXML, MIDI, and humdrum scores, then convert them into `Stream` objects that can be fed through our pipeline.
- Standardize score metadata (composer, era, key signatures, time signatures) via `stream.metadata` to inform profile selection and confidence heuristics.
- Leverage `stream.expandRepeats()` and `measure.offsetMap` to align measures/beats before we map to chord events.
- Cache parsed results with `freeze/thaw` streams or pickled chord event lists so repeated analyses stay fast.

## Chord Extraction and Mapping
- Apply `Stream.chordify()` to derive block chords, then translate each `music21.chord.Chord` into our internal chord symbol representation, preserving offsets, durations, and voicing evidence.
- Use `ChordSymbol` and `romanText.streamToRomanText` to double-check enharmonic spellings and maintain figured-bass annotations we can surface in explanations.
- Capture rhythmic context by pairing chordify output with `meter.TimeSignature` and `stream.recurse().notesAndRests` so our analyzers see phrase boundaries and cadential emphasis.
- Provide a helper that packages score-derived chords into the same structures consumed by `PatternAnalysisService`, allowing fully automated score → chords → pattern detection workflows.

## Enhanced Analysis Features Powered by music21
- Tap `analysis.discrete.KrumhanslSchmuckler`, `analysis.reduction`, and cadence detection to benchmark or supplement our key and cadence engines when confidence dips below a threshold.
- Integrate `roman.RomanNumeral` and `figuredBass` utilities to validate inversion labeling, generate alternative spellings, and enrich evidence strings for users.
- Use `voiceLeading.similarity`, `interval.Interval`, and `counterpoint` checks to expand our bass motion and voice-leading diagnostics, improving pattern engine evidence and chromatic analysis descriptions.
- Extract `features.jSymbolic`, set-class info, or modal characteristics from `scale` and `pitch` modules to deepen our musical character narratives.

## Corpus, Testing, and Workflow Improvements
- Mine the built-in `corpus` collections (Bach chorales, Tin Pan Alley, jazz standards) to seed regression fixtures and demonstrate cross-style coverage.
- Hook corpus metadata into `corpus_miner` so we can auto-tag pieces by era/style and bias suggestion frameworks appropriately.
- Add developer tooling to round-trip: ingest score → generate chords/analysis → export annotated MusicXML (with `stream.write`) for score review and QA.
- Document a CLI pipeline (`parse-score --export-chords`) that relies on music21 under the hood, giving users a reproducible path from raw scores to our analysis reports.
