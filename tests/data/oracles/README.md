# External Oracle Corpora — Decision Document

**Status:** Draft recommendation — research only, no code yet
**Date:** 2026-05-06
**Audience:** the human or robot who picks up task 4 (DCML loader)

## Top-line Recommendation

> **Use the DCML Annotated Beethoven Corpus (ABC) — string quartets — as the
> first external oracle source.** It is the cheapest path from "we have 15
> hand-curated minor-key cases" to "we have several hundred independently-
> validated test cases that exercise the exact bug classes we just fixed":
> minor keys, secondary dominants in minor, augmented sixths, modulation, and
> chromatic passing diminished chords.

**Two-sentence rationale.** ABC is a flat, well-typed TSV (parseable with
stdlib `csv` — no music21 required), it has 21 minor-key movements totalling
~7,900 minor-key chord labels (Mozart's piano sonatas, by contrast, have only
6 minor-key movements / ~1,600 minor-key labels), and the DCML chord labels
already break out everything we care about into separate columns
(`numeral`, `figbass`, `relativeroot`, `chord_type`) so we can ingest without
a heavyweight Roman-numeral parser. The license (CC-BY-NC-SA 4.0) is the only
real downside, and we can live with NC for an internal test fixture as long
as we keep the published library and demo separable from the test data.

---

## Comparison Table

| Corpus | Format | License | Pieces | Total chord labels | Minor-key labels | RN convention | Aug6 | V/iv etc. | Modulation | Stdlib parseable? |
|---|---|---|---|---|---|---|---|---|---|---|
| **DCML ABC (Beethoven SQs)** | TSV (29 cols) | CC-BY-NC-SA 4.0 | 70 movts (16 quartets) | 28,089 | **7,911** | lowercase=minor, slash=secondary, decomposed columns | `It6` `Ger6` `Fr6` (own `chord_type`) | yes — `V7/iv` etc. | per-row `globalkey` + `localkey` | **yes — pure CSV** |
| **DCML Mozart Piano Sonatas** | TSV (29 cols) | CC-BY-NC-SA 4.0 | 54 movts (18 sonatas) | ~9–13k (est.) | ~1,608 (only 6 minor movts) | same as ABC | yes (K310-1 has all 3) | yes | yes | yes |
| **DCML Beethoven Piano Sonatas** | TSV (29 cols) | CC-BY-NC-SA 4.0 | 91 movts | 21,963 | 6,326 | same as ABC | yes | yes | yes | yes |
| **DCML Schubert Winterreise** | TSV | CC-BY-NC-SA 4.0 | 24 songs | (large) | high (Schubert + minor) | same | yes | yes | heavy modulation | yes |
| **DCML Romantic Piano Corpus** | TSV (meta-corpus, 9 sub-corpora) | CC-BY-NC-SA 4.0 | hundreds | very large | high (Chopin Mazurkas alone: 5,226 minor labels in 56 pieces) | same | yes | yes | very heavy chromaticism | yes |
| **DCML Chopin Mazurkas** (subset of romantic_piano_corpus) | TSV | CC-BY-NC-SA 4.0 | 56 pieces | 9,125 | **5,226** | same | yes | yes | dense modulation, Polish folk modes | yes |
| **When-in-Rome (Gotham)** | RomanText (`.txt`) | CC-BY-SA 4.0 | **1,295 analyses** across 9 categories | very large | large (incl. Bach chorales, Schubert lieder) | RomanText / music21 syntax — `ø` `o` `+` `Cad64` `It6` `Fr43` `Ger65` `||` for pivots | first-class shorthands | first-class | first-class (`||` pivot syntax) | **no — needs RomanText parser or music21** |
| **TAVERN** (Devaney) | `**kern` (humdrum) | CC-BY-SA 4.0 | 27 sets / 281 variations | small per file | 121 minor phrases (out of 1,060) | upper/lower + figured bass; sparser | basic | yes | per-variation key changes | **no — needs humdrum parser** |

### Quick takeaways

- **License:** Only WiR and TAVERN are NC-free (`CC-BY-SA 4.0`). Every DCML
  corpus is `CC-BY-NC-SA 4.0` — fine for internal tests, awkward if we ever
  bundle test fixtures into a published wheel that's used commercially. (Test
  data shipped to PyPI is borderline. We should keep test fixtures out of the
  installed package via `MANIFEST.in` regardless.)
- **Format:** DCML TSV is by far the easiest to ingest. RomanText is human-
  readable but requires a real parser (or music21). `**kern` is a fixed-width
  humdrum format that's a non-starter without a dedicated library.
- **Decomposition:** DCML pre-splits the chord label into `numeral` / `form` /
  `figbass` / `relativeroot` / `chord_type` columns, so we don't need to write
  (or trust) a Roman-numeral parser to extract structure. This was the single
  biggest surprise in this research — *the corpus has already done the parsing
  work for us*.

### What surprised me

1. **The DCML TSV is way more structured than I expected.** I assumed we'd be
   writing a regex like `r'(b{0,2}|#{0,2})([VvIi]+)([oø+%]?)(\d{0,2})(?:/(.+))?'`
   to extract the parts. But the DCML pipeline already runs the regex from the
   [official annotation guidelines](https://dcmlab.github.io/standards) and
   stores the parts as separate columns. We don't need a parser; we need a
   column mapper.
2. **DCML is uniformly CC-BY-NC-SA, not CC-BY.** Several papers and second-
   hand summaries cite "CC-BY 4.0" for these corpora. The actual `LICENSE`
   files are NC-SA. Don't trust the metadata badges; check the file.
3. **TAVERN is much smaller than its reputation.** 121 minor-key phrases is
   barely larger than what we already have curated by hand. It exists for
   theme-and-variation studies, not as a general harmonic-analysis oracle.
4. **When-in-Rome already mirrors the DCML corpora into RomanText.** Each
   piece in WiR can have `analysis.txt` AND `analysis_DCML.txt` (the same
   content auto-converted from the DCML TSV). If you want a single permissive-
   licensed front door to "all of it," WiR is it — but you pay for that with a
   RomanText parser.
5. **Mozart's piano sonatas are mostly major-key.** Only 6 of 54 movements
   are in minor (K280-2 in f, K310-1/3 in a, K331-3 "Alla Turca" in a, K457-1/3
   in c). For a library whose minor-key handling we just fixed, Mozart sonatas
   are the *worst* DCML corpus to start with.
6. **The pipe-separated `label` column is annotated with phrase markers**
   (`{`, `}`, `|PAC`, `|HC`, `|DC`) that we'll want to strip on ingest. The
   normalized `chord` and `numeral` columns are already cleaned.
7. **K310-1 alone contains every chord type that exposed our bugs.**
   Italian, German, AND French sixth chords; V7/iv, V7/IV, V/VI, V/III,
   V/VII; ♭v°-ish chromatic passing diminished sevenths; modal mixture
   (V(64), v6, IIIM65). One movement, 71 distinct chord labels, all the bug
   classes. This is a strong case for *also* including K310-1 as a sanity
   loader-test, even if the main extraction targets ABC.

---

## Recommended Initial Subset (~50–100 cases)

We don't want all 28,000 ABC chord rows — most of them are common-practice
diatonic plumbing we already test elsewhere. We want progressions that
exercise the *failure modes* the existing oracle covers:

### Tier 1: minor-key sonata-allegro openings (high-density bug bait)

These movements are guaranteed to have V/iv, V/V, augmented sixths, and
chromatic passing chords, and they use modulation seriously.

| Piece | Key | Labels | Why we want it |
|---|---|---|---|
| `n04op18-4_01` | c minor | 554 | C minor opening, well-studied, classical-period chromaticism |
| `n08op59-2_01` | e minor | 445 | "Razumovsky" no.2 — heavy modulation through III, V/iv |
| `n11op95_01` | f minor | 245 | "Serioso" — compact, very chromatic |
| `n14op131_01` | c# minor | 334 | Late Beethoven fugal opening — extreme modulation |
| `n15op132_01` | a minor | 622 | Op. 132 — "Heiliger Dankgesang" precursor, modal |
| `n09op59-3_02` | a minor | 481 | Andante in slow tempo — clear functional motion |

**Subtotal: ~2,680 chord rows.** From these we extract phrases (between
phrase-end markers `}{`) — typically 4–12 chords each, yielding maybe
**150–250 candidate progressions** before filtering.

### Tier 2: filter for "interesting" rows

After ingestion, keep only progressions where at least one chord has:

- `relativeroot` non-empty (secondary dominant / tonicization)
- `chord_type ∈ {Ger, It, Fr, +M, +}` (augmented sixth or augmented triad)
- `chord_type ∈ {o7, %7}` AND `numeral` starts with `#` (chromatic passing dim)
- `localkey != "i"` AND `localkey != "I"` (non-tonic local key — modulation)
- a chord label with `b` or `#` accidental on the numeral

This filter is the cheap version of "does this case stress the bugs we just
fixed?" Drop the rest. Aim for **~80–100 final cases** in the first pass.

### Tier 3: deliberate "boring" controls

Add ~10–15 progressions that are *purely* diatonic (no flags from Tier 2) so
we have negative controls — confirms the analyzer doesn't hallucinate
chromaticism on plain i–iv–V–i.

### Tier 4: K310-1 sanity card

Include the complete A-minor exposition of Mozart K310-1 (the first ~30
chords up to the first PAC) as a single golden-trace test. It's small, it's
famous, and if our ingest can handle K310-1 cleanly it can handle anything in
ABC. Use this as the loader's smoke test before scaling up.

---

## License & Attribution Requirements

If we vendor a subset of ABC into `tests/data/oracles/abc/`:

### Required notices

1. **A copy of the CC-BY-NC-SA 4.0 license text** lives at
   `tests/data/oracles/abc/LICENSE`. Copy it from the upstream repo.
2. **Attribution file** at `tests/data/oracles/abc/ATTRIBUTION.md` listing:
   - Source repo: `https://github.com/DCMLab/ABC` (commit hash pinned)
   - Citation: Hentschel, J., Neuwirth, M., & Rohrmeier, M. (2021).
     "The Annotated Mozart Sonatas: Score, Harmony, and Cadence."
     *Transactions of the International Society for Music Information
     Retrieval*, 4(1), 67–80. (Adapt to ABC paper for the actual citation;
     see `CITATION.cff` in the upstream repo.)
   - Statement: "This directory contains a subset of the DCML Annotated
     Beethoven Corpus, used unmodified except for filtering by phrase
     boundary. Original column structure preserved. Distributed under
     CC-BY-NC-SA 4.0."
3. **`ShareAlike`** means any modifications we publish must also be CC-BY-NC-SA.
   *Our ingestion-time extracted JSON oracle counts as a derivative work.*
   So `tests/data/oracles/abc/derived/*.json` must also be marked CC-BY-NC-SA.

### What "NonCommercial" means in practice

CC-BY-NC restricts *commercial distribution* of the licensed material. The
internal test suite is fine. The published `harmonic-analysis` wheel on PyPI
is fine *as long as we don't ship the test fixtures inside the package*.
Belt-and-suspenders:

- Add `recursive-exclude tests/data/oracles *` to `MANIFEST.in`.
- Confirm `pyproject.toml` `[tool.setuptools.packages.find]` doesn't sweep
  `tests/`. (It shouldn't — `tests/` is conventionally excluded.)
- Run `python -m build` and inspect the resulting `.whl` to verify no oracle
  files are bundled.

If we later want to ship oracle data with the wheel (e.g. for users to run
acceptance tests), we'd need to switch to a permissive-licensed source. The
fallback is **When-in-Rome (CC-BY-SA 4.0)** — same `ShareAlike` constraint,
no NC restriction. That's the reason WiR is recommendation #2 below.

### Plan-B option

If NC turns out to be a deal-breaker (e.g., a downstream consumer is a
commercial product), pivot to **When-in-Rome** and write a RomanText parser.
Cost estimate: ~300 lines of Python, ~1 day of focused work, plus a music21
dev dependency or a hand-rolled parser. Roughly 3× the effort of the DCML
loader. The `analysis_DCML.txt` files in WiR would help — they're DCML
content in RomanText syntax, so they're a Rosetta stone for the conversion.

---

## Known Incompatibilities With Our Codebase Conventions

The DCML chord syntax is mostly compatible with our codebase but differs in
several specific places. The DCML loader's normalization layer must handle:

### 1. Augmented sixth notation

| DCML | Our codebase | Fix |
|---|---|---|
| `It6` | `It+6` | insert `+` before `6` when chord_type ∈ {It, Ger, Fr} |
| `Ger65` | `Ger+6` (we don't track inversion) | strip figbass, normalize to base name |
| `Fr43` | `Fr+6` | same |

Our `low_level_events.py` matches against `["+6", "it+6", "fr+6", "ger+6", "aug6"]`.
The loader should emit `It+6`, `Ger+6`, `Fr+6` (without inversion figures) for
the test chord labels. The original DCML inversion *can* be preserved in a
separate metadata field if we want it later.

### 2. Flat/sharp encoding (Unicode vs ASCII)

| DCML | Our oracle | Our codebase |
|---|---|---|
| `bVII` (ASCII `b`) | `♭VII` (Unicode U+266D) | accepts both |

The existing `minor_key.oracle.json` uses `♭VII`, `♭VI`, `♭v°` (Unicode flat).
The codebase explicitly handles both (`grep` showed `bVII` and `♭VII` as
synonyms in `validation_errors.py` and `chromatic_analysis.py`). Loader
recommendation: emit Unicode flat to match the existing oracle file's style.
Conversion: `label.replace('b', '♭')` is too aggressive (would mangle `Bb`,
`bVII` only — but `b` after a digit is a different beast, and `b` in an inversion
figure like `V7(b9)` is a *third* meaning). Safer rule: only replace leading
`b`/`#` on the numeral itself, not inside parenthesized alterations.

A conservative tokenizer:
```
^([b#]{0,2})([IVXivx]+)(.*)$
```
Replace the leading accidental group only. Leave everything to the right of
the numeral unchanged.

### 3. Half-diminished marker

| DCML | Our codebase |
|---|---|
| `ii%65` | `iiø` or `ii°7` (we don't strongly distinguish in tests) |

DCML uses `%` for half-diminished. Our convention varies. The minor-key oracle
uses `°` (degree sign U+00B0) for fully diminished. We should map:
- `chord_type=o`/`o7` → `°` suffix
- `chord_type=%`/`%7` → `ø` (U+00F8) suffix
- `form=o` (in label) → preserve as `°` in normalized roman

### 4. Inversion figures

| DCML | Our codebase |
|---|---|
| `V65`, `V43`, `V42`, `V2` | same — we accept these |
| `V7` | `V7` — same |
| `I64` (cadential) | `I64` or `Cad64` — we accept either |

Inversion figures are essentially compatible. Note DCML uses `2` for
`V42` shorthand sometimes; check `figbass` column for the canonical form.

### 5. Modulation handling (the big one)

DCML stores `globalkey` and `localkey` as separate columns, where `localkey`
is itself a Roman numeral relative to `globalkey`. So a chord row from a
C-major piece in the dominant key area looks like:

```
globalkey=C  localkey=V  numeral=ii  →  chord is "ii of G major" = a minor
```

Our oracle uses absolute keys (`"key": "E minor"`). The loader has to
**resolve** `localkey` relative to `globalkey` to produce an absolute key
label per progression. Algorithm:

1. Parse `globalkey` → absolute pitch + mode (e.g., `c` → `C minor`).
2. Parse `localkey` Roman numeral → scale degree + mode-implied quality.
3. Compute absolute pitch of localkey degree in globalkey.
4. Emit `"key": "<absolute>"`.

Edge case: when `localkey` changes mid-progression (modulation), we either
(a) split the progression at the modulation point, or (b) emit a multi-key
test case. Recommendation: **split**. Pivot chords get duplicated into both
sub-progressions with a `pivot: true` flag. Trying to test modulation
detection from a single oracle entry is biting off too much for v1.

### 6. Phrase boundaries and label punctuation

The raw `label` column can contain:
- `{` / `}` — phrase begin/end markers
- `|PAC`, `|IAC`, `|HC`, `|DC` — cadence type after the chord
- `[chord]` — predicted/expected chord (we can ignore for now)
- `(#9)`, `(b5)`, `(+M7)` — alterations in parens
- `[no5]`, `[add9]` — explicit chord-tone removals/additions

Recommended approach: **trust the cleaned `chord` column** instead of
re-parsing `label`. The DCML pipeline already strips phrase markers and
cadence flags from the `chord` column. Pull cadence info separately from the
`cadence` column and phrase boundaries from the `phraseend` column.

### 7. Minor-mode 6th/7th degree spelling

Subtle. DCML follows the convention that uppercase/lowercase reflects the
**triad quality**, not the diatonic position. So in C minor, `VII` means
B♭-major (♭7 triad) and `vii` means b-diminished (raised-7 triad — Picardy-
like). The natural-minor `♭VII` is just written `VII` (because in C minor,
B♭ is diatonic, so no accidental is needed). When we emit our roman numeral,
if the codebase wants `♭VII` for the natural-minor seventh-degree triad in a
minor key, the loader needs to **add the `♭` prefix** when:
- `globalkey_is_minor=1` AND `numeral=VII` AND chord root is a whole step
  below tonic (i.e., natural-minor scale degree).

Same logic for `III` ↔ `♭III` and `VI` ↔ `♭VI` in minor keys. Our existing
oracle already follows this convention (minor key shows `♭VII` not `VII`).

### 8. Things the loader should NOT try to handle in v1

- **Pedal points** (`pedal` column non-empty) — drop these progressions or
  flag them as "not for v1."
- **Chord_tones / added_tones** columns — useful debugging info, but our
  test format doesn't have a place for them.
- **Voice-leading inversions** below the figured-bass level — out of scope.
- **Repeated phrase markers** (`}{` = phrase-end-and-start in same row) —
  use as a phrase splitter; don't try to preserve.

---

## Next Steps for Task 4 (DCML Loader)

Concrete checklist for whoever implements `tools/oracles/dcml_loader.py`:

### Loader API surface

```python
# pseudocode — actual signatures TBD
def load_dcml_tsv(path: Path) -> list[ProgressionCase]:
    """Parse a DCML harmonies.tsv file into normalized ProgressionCase objects."""

def filter_interesting(cases: list[ProgressionCase]) -> list[ProgressionCase]:
    """Tier 2 filter — keep only cases with secondary dominants / aug6 /
    chromatic dim / modulation / accidentals."""

def emit_oracle_json(cases: list[ProgressionCase], out: Path) -> None:
    """Write filtered cases as oracle JSON matching the schema of
    tests/fixtures/progressions/minor_key.oracle.json."""
```

### Implementation steps

1. **Pin the corpus version.** Vendor a single commit hash from
   `DCMLab/ABC` — don't track `main`. Document the hash in
   `tests/data/oracles/abc/COMMIT_HASH`. We need reproducibility; the upstream
   gets re-annotated periodically.

2. **Vendor the 6 Tier-1 movements only.** Copy
   `harmonies/n04op18-4_01.harmonies.tsv` etc. into
   `tests/data/oracles/abc/raw/`. Don't pull `harmonies/` wholesale —
   28,000 rows is overkill and bloats git. Keep `metadata.tsv` for context.

3. **Write the column mapper.** Read the TSV with stdlib `csv.DictReader`,
   `delimiter='\t'`. The columns we care about are:
   - `mc`, `mn` — measure number (use as progression sequence index)
   - `chord` — already-cleaned chord label
   - `numeral`, `form`, `figbass`, `relativeroot`, `chord_type` — for the
     Tier-2 filter and our roman-numeral output
   - `globalkey`, `localkey`, `globalkey_is_minor`, `localkey_is_minor` —
     for absolute-key resolution
   - `cadence`, `phraseend` — for phrase splitting

4. **Phrase splitter.** Walk rows in order; start a new progression on
   `phraseend ∈ {"}", "}{"}` AND on `localkey` change. Keep progressions
   between 3 and 16 chords (drop singletons; cap long stretches).

5. **Resolve local→global key.** Use the already-computed `chord_tones`
   column (semitone offsets from globalkey root) to verify the absolute pitch
   of the localkey root. Pitch arithmetic on `localkey` Roman numeral plus
   `globalkey` letter name.

6. **Apply the normalization rules in §"Known Incompatibilities".** Emit
   roman numerals matching the existing `minor_key.oracle.json` style.

7. **Filter.** Run `filter_interesting`. Aim for ~80–100 final cases per
   movement set, not per movement. We'd rather have 80 high-signal cases than
   500 mediocre ones.

8. **Ground-truth-only flag.** Each emitted case should include
   `"source": "dcml_abc"`, `"source_movement": "n04op18-4_01"`,
   `"source_measures": "12-15"`, and `"source_commit": "<sha>"`. When a test
   fails, we need to know exactly which expert annotation we're disagreeing
   with so a human can adjudicate.

9. **Schema compatibility.** Match the existing oracle JSON schema:
   ```json
   {
     "name": "...",
     "chords": ["...", "..."],
     "key": "...",
     "roman_numerals": ["...", "..."],
     "comment": "..."
   }
   ```
   Add optional fields: `source`, `source_movement`, `source_measures`,
   `source_commit`, `cadence_at_end` (if `cadence` column non-empty on the
   last row).

10. **Don't auto-trust the oracle.** The first run will surface cases where
    our analyzer disagrees with the DCML annotation. Some of those will be
    our bugs. Some will be DCML's. Some will be legitimate ambiguity (Roman
    numeral analysis is famously not unique). Build a triage workflow:
    - Disagreements get logged to `tests/data/oracles/abc/disagreements.md`.
    - A human reviews and either (a) marks the case as `disputed: true` and
      drops it from CI, (b) accepts the DCML answer and files a bug, or
      (c) accepts our answer and files an upstream issue.

11. **CI integration.** Add a new pytest module
    `tests/test_external_oracle_abc.py` that loads the JSON oracle and asserts
    `roman_numerals` matches. Run it in the standard test job. Make
    failures *informative* (show source movement + measures, not just diff).

12. **Document everything.** When task 4 is done, update this README with:
    - Final case count.
    - Any normalization rules discovered during implementation.
    - Disagreement triage results from the first pass.
    - A short "lessons learned" section for the next corpus we ingest.

### What NOT to do in task 4

- Don't try to ingest WiR in the same pass. Different format, different
  parser, different scope. One corpus per task.
- Don't try to handle pedal points, `[no5]`/`[add9]` alterations, or split
  measures. Filter them out and revisit later.
- Don't try to resolve every `disputed` case immediately. Some of these are
  genuine theoretical disagreements; budgeting hours per case is a trap.
- Don't ship the raw TSV files inside the published wheel. (See §License.)

### Stretch goals for task 5+

- Add Mozart K310-1 (DCML mozart_piano_sonatas) as a small permissive-style
  smoke test — one movement, one progression, one key, exhaustive coverage of
  the chord-type space.
- Add `n13op130_02` (Op. 130 Cavatina) as a "this is hard" stress test —
  late Beethoven harmonies routinely break analyzers.
- Once the DCML loader is solid, the WiR loader is the natural next step:
  it gives us 1,295 analyses and a permissive license at the cost of one
  RomanText parser. Most of the schema work is shared between the two.

---

## References

- DCML ABC: https://github.com/DCMLab/ABC
- DCML Mozart Piano Sonatas: https://github.com/DCMLab/mozart_piano_sonatas
- DCML Beethoven Piano Sonatas: https://github.com/DCMLab/beethoven_piano_sonatas
- DCML Schubert Winterreise: https://github.com/DCMLab/schubert_winterreise
- DCML Romantic Piano Corpus: https://github.com/DCMLab/romantic_piano_corpus
- DCML Annotation Standard: https://dcmlab.github.io/standards/build/html/reference/specs.html
- When-in-Rome: https://github.com/MarkGotham/When-in-Rome
- TAVERN: https://github.com/jcdevaney/TAVERN
- Hentschel et al. (2025) Scientific Data paper on DCML infrastructure:
  https://doi.org/10.1038/s41597-025-04976-z
