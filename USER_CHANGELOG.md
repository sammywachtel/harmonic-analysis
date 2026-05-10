# What's New in Harmonic Analysis

The human-friendly companion to [CHANGELOG.md](CHANGELOG.md). Technical minutiae live there;
the good stuff — what you can actually *do* now — lives here.

---

## [0.3.1-beta.4] - 2026-05-10

### 🎼 Minor-Key Roman Numerals Are Honest About Their Flats Now

🎹 **`♭III`, `♭VI`, `♭VII` now consistently carry their flat marker** in minor-key analysis output. Previously a progression like A-minor's Andalusian cadence (`Am G F E`) came back as `i bVII VI V` — mixing flat and no-flat spellings for chords that are *all* flatted relative to parallel A major. Now you get `i ♭VII ♭VI V`. Same chords, same theory, just labels that don't gaslight you about which degrees are diatonic and which are altered. The Unicode `♭` is the standard music-notation glyph; the old ASCII `bVII` is gone.

🎯 **The "B-minor-looks-like-Dorian" bug is dead.** Drop a pure B-Aeolian progression (`Bm A G A Bm` — chords pulled straight from B natural minor with no raised-6 anywhere) into the analyzer, and it used to come back tagged B Dorian. Three layers of the analyzer were conspiring against the obvious answer — they're now all on the same page. Aeolian gets called Aeolian, no Dorian heuristics quietly hijacking results in the background.

🐛 **Slot-4 in minor keys no longer fabricates a phantom `iv`.** A chord rooted a major-third above the minor tonic (the chromatic mediant — think G♯ over E minor) used to label itself `iv`, but the diatonic `iv` is the minor subdominant a *perfect-fourth* above. Now it correctly emits `♯III`. A tucked-away bug nobody had stumbled into yet, plugged with a regression test before they could.

### 🔄 Heads-Up for Downstream Consumers

If any of your code does string-matching against the analyzer's roman numeral output, the changed tokens are:

- `bVII` → `♭VII` (ASCII flat replaced with Unicode flat)
- `VI` (in minor keys) → `♭VI`
- `III` (in minor keys) → `♭III`
- `iv` at slot 4 → `♯III` (this was a bug fix; if your code relied on the old behavior, it was already wrong)

The major-key roman table is unchanged. The library's public Python API surface is unchanged — same methods, same signatures, just different (more accurate) string content inside the result objects.

---

## [0.3.1-beta.2] - 2026-05-05

### 🔧 Fixed: The "Minor Key Identity Crisis" Is Over

🎹 **No more B minor misidentified as D major.** If you've been feeding real recordings into the
key detector and getting the relative major back instead of the actual minor key — this one's for
you. Two bugs in the ensemble detector were conspiring against minor keys: low-quality edge events
were getting to vote on the key, and the V→i cadence (minor resolution!) was being scored as less
convincing than V→I. Both are fixed. Recordings in minor keys now get their due.

### ✨ New Things You Can Do

🎸 **Disambiguate slash chords and inversions with bass-chroma analysis.** New `use_bass_chroma`
parameter on `analyze_audio` and `AudioAdapter` (default `False`). When enabled, the chord
estimator uses low-frequency chroma to bias matching toward chords whose root or third lines up
with the detected bass note — so Bm and D/B stop being the same thing. Opt-in because it costs
a bit extra and not every recording has clean bass separation.

⏲️ **Tune the analysis for how loosely the recording was played.** New `rubato` parameter accepts
`"strict"`, `"moderate"`, `"loose"`, or `"free"` (or a float from 0.0 to 1.0). Rubato controls
the analysis window size and smoothing — a free-tempo piano performance needs different settings
than a click-tracked studio take. Default is `"moderate"`, which matches the previous behavior
exactly, so you won't notice a thing unless you opt in.

### 🛠️ Under the Hood

🔇 **Silence is no longer a chord.** Leading silence and quiet sections used to generate phantom
chord events; they don't anymore. Analysis windows below the minimum chroma energy threshold are
skipped entirely. Your timestamps will actually mean something now.

📊 **Real-audio regression tests** now guard the relative-pair fix. Four integration tests run
against a real piano recording and will loudly object if B minor starts coming back as D major again.

---

## [0.3.1-beta.1] - 2026-05-05

### ✨ New Things You Can Do

🎵 **Audio Analysis**: You can now analyze audio files directly — just `POST` a file to
`/api/analyze/audio` and get back chord events and key estimates. No more transcribing by hand
before running harmonic analysis; drop in a WAV (or MP3/OGG with ffmpeg) and let the library
do the listening.

📦 **Opt into audio without bloating your install.** Audio dependencies (librosa, soundfile) are
now tucked behind an optional extra: `pip install harmonic-analysis[audio]`. If you don't need
audio analysis, your install stays lean — `import harmonic_analysis` works exactly as before,
no extra baggage.

⏱️ **Analyze just the part you care about.** The audio endpoint accepts optional `start` and `end`
time parameters so you can zoom in on a specific section of a long recording instead of processing
the whole file.

### 📚 New Documentation

Full audio analysis docs are now live: quickstart tutorial, how-to guide, API reference, and an
internals explainer covering how the chroma extraction and key detection pipeline actually works.

---

## [0.3.0] - 2026-05-04

### ✨ New Things You Can Do

🎸 **See your progression through every stylistic lens at once.** The library now runs a full
multi-profile sweep (classical, jazz, pop, modal) in one call and ranks the results by confidence.
You can now call `analyze_with_patterns_async` without specifying a profile and get back a ranked
list of interpretations — finally an honest answer to "is this jazz or just accidentally cool?"

🧩 **Get a per-style breakdown from the demo API.** The `/analyze` endpoint now returns a
`style_analysis` map (one entry per style) and a `dominant_style` field. You can now build
integrations that show your users exactly which stylistic box their progression fits into, and
how confident the engine is about each one.

🎛️ **Skip the profile picker in the demo app.** The UI no longer holds analysis hostage behind a
profile selection. You can now hit "Analyze" without choosing a style — the app runs all profiles
and shows a collapsible Style Analysis section with confidence bars and a dominant-style badge.

### 🔄 Things That Work a Little Differently

**Profile is now optional everywhere.** If you were passing a profile to gate the analysis, you
can keep doing that — nothing broke. But omitting it now gets you *more*, not less.

**The pattern engine is style-aware.** Under the hood, every matched pattern now carries its
originating style profile. If you're consuming raw engine output, expect a new `profile` tag on
pattern match objects.

---

*For the full technical diff, see [CHANGELOG.md](CHANGELOG.md).*
