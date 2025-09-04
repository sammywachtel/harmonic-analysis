# Pattern Engine

## Glossary

- **DP (Dynamic Programming)** — An algorithmic technique used here to choose the best non‑overlapping set of pattern matches (weighted interval scheduling).
- **Token** — A harmonic event, typically a Roman numeral with optional role, inversion, voice info, or flags.
- **Roman Numeral** — A harmony label relative to the key (e.g., `I`, `ii`, `V7`, `iv6`, `V/ii`). Uppercase typically indicates major, lowercase minor.
- **Roman Root** — The *root* of the Roman numeral, ignoring quality/tensions/inversion (e.g., `V65` → root `V`; `ii6/5` → root `ii`; `V/ii` → root `V` with a **secondary** of `ii`).
- **Inversion** — Figured‑bass suffix indicating which chord member is in the bass: `6` (first inversion), `64` (second inversion triad or cadential 6–4), `65/43/42` (seventh‑chord inversions).
- **Scale Degree** — Numbered pitch classes 1..7 relative to the key (1 = tonic). Used for soprano/bass melodies and constraints like `arrival_soprano_any_of`.
- **Soprano** — Highest voice (melodic line). In this engine, `soprano_degree` is an optional integer 1..7 provided by upstream and used by cadence checks (e.g., PAC on 1/3/5).
- **Bass** — Lowest voice. We may use `bass_motion_from_prev` (semitones or diatonic steps) to enforce motions like the Phrygian −1 into V or circle‑of‑fifths chains.
- **Cadence** — A phrase‑ending harmonic motion (e.g., **PAC**, **IAC**, **half**, **Phrygian**). Encoded as patterns in the `cadence` family.
- **Cadential 6–4** — A tonic triad in second inversion (`I64`) functioning like a dominant preparation; often notated as suspensions over V. In this engine, patterns can set `treat_I64_as_D: true` and/or require a `cadential_64` flag.
- **Phrygian Cadence** — In minor, `iv6 → V` with a characteristic **−1** step in the bass into the dominant. Can be enforced with `phrygian_bass_step` when motion data is available.
- **T / PD / D** — Functional roles: **T**onic (I/vi/iii), **P**re‑**D**ominant (ii/IV/N6), **D**ominant (V/vii°). Used for role checks in step specs.
- **T_or_D** — A relaxed role requirement that accepts either tonic or dominant function (helpful when function is ambiguous but PD should be excluded).
- **Profile** — Style context (`classical`, `jazz`, `pop`) that controls substitutions and matching leniency.
- **SubstitutionEngine** — Applies profile‑specific equivalences (e.g., in jazz, `V ↔ ♭II7` tritone substitution).
- **Secondary Dominant** — `V/x` targets the dominant of another degree (e.g., `V/ii`). Matched via root parsing; substitutions may permit surface alternates.
- **Tritone Substitution** — Jazz equivalence replacing `V7` with `♭II7` (same tritone). Enabled via profile substitutions.
- **Chromatic Mediant** — Mediant‑related harmony with chromatic alteration (e.g., `♭VI` in major). A descriptor can flag its presence.
- **Mixture (Modal Mixture)** — Borrowing from the parallel mode (e.g., `iv` in major). Often appears in `mixture_modal` family patterns.
- **Schema (Schemata)** — Conventional phrase‑level progressions (e.g., **Pachelbel**, **Prinner**, **Monte/Fonte**). Recognized via descriptors or root templates.
- **Constraint** — A pattern‑level requirement (e.g., `mode`, `arrival_soprano_any_of`, `require_flag_any_of`, `treat_I64_as_D`). Evaluated after the step sequence aligns.
- **Descriptor** — A phrase‑level detector that checks broader context (e.g., `pachelbel_core`, `circle_of_fifths`).
- **Window** — The span of tokens considered for a pattern: `{min, max}`. The matcher slides windows of this size over the token stream.
- **Best Cover** — The final, non‑overlapping set of matches chosen by DP to maximize total score.


*A fast, profile‑aware harmonic pattern matcher for tonal music.*

This document explains how the pattern engine works end‑to‑end: data model, JSON
schema, matching algorithm, constraints/descriptor system, substitution profiles, scoring,
best‑cover selection, testing, and how to extend it.

> TL;DR — You feed the engine a Romanized stream (tokens with roman figures,
> functional roles, and optional voice/flag info). It slides windows, checks each
> JSON pattern (steps + constraints + descriptors), scores matches, then picks the
> **best non‑overlapping cover** of the passage with dynamic programming.

---

## 1) High‑level architecture

```
romanizer  →  tokens  →  matcher (sequence + descriptors + constraints + subs)
                             ↓
                       candidate matches
                             ↓
                  best non‑overlapping cover (DP)
```

**Key modules** (in `matcher.py`):

- **Token** — one harmonic event with fields used by the matcher.
- **SubstitutionEngine** — style/profile‑specific equivalences (classical/jazz/pop).
- **DescriptorRegistry** — phrase‑level detectors (e.g., Pachelbel core, circle of fifths).
- **ConstraintValidator** — evaluates pattern‑level constraints (mode, flags, arrival soprano, phrygian step, etc.).
- **SequenceMatchStrategy** — sliding‑window matcher for step sequences; now supports
  *effective role remapping* (e.g., treat **I⁶⁴** as **D** when a pattern sets `treat_I64_as_D`).
- **IntervalSchedulingSolver** — DP to select the maximum‑score set of non‑overlapping matches.

The public entry points are typically methods on your service wrapper, e.g. `analyze_with_patterns()`.

---

## 2) Token model (input to the matcher)

The matcher doesn’t do Romanization; it expects **tokens** created by your upstream analyzer.

Minimal fields (the matcher uses the ones you supply):

```python
@dataclass
class Token:
    roman: str                   # e.g., "V7", "ii6", "I64", "V/ii" (secondary ok)
    role: str | None = None      # e.g., "T", "PD", "D" (or None if unknown)
    soprano_degree: int | None = None   # 1..7 (scale‑degree in key), optional
    bass_motion_from_prev: int | None = None  # semitone or diatonic delta, optional
    flags: list[str] | None = None     # e.g., ["cadential_64", "passing_64"], optional
```

Convenience helpers on `Token` (used internally):

- `roman_root()` — root with inversion retained when explicit (e.g., `V65` stays `V65`).
- `roman_base()` — **inversion‑insensitive** base (e.g., `V65` → `V`, `ii6/5` → `ii`).

> If you can also provide `mode` and `bass_degree`, some constraints/descriptors become
> more precise, but they are optional.

---

## 3) Pattern JSON schema

Each JSON pattern is an object with **identity**, a **sequence** of step specs, and optional
**constraints**, **descriptors**, **substitutions**, and **score**.

```json
{
  "id": "ii_V_I_root_macro",
  "family": "jazz_pop",               // taxonomy bucket (cadence, jazz_pop, schema, ...)
  "name": "ii–V–I",                   // display name
  "window": { "min": 3, "max": 3 }, // required window size in tokens
  "sequence": [                        // ordered step specs
    { "roman_root_any_of": ["ii", "ii7", "iiø7", "ii6", "ii65"] },
    { "roman_root_any_of": ["V", "V7", "♭II7"] },
    { "roman_root_any_of": ["I", "i", "Imaj7"] }
  ],
  "constraints": {                     // pattern‑level checks (optional)
    "mode": "major|minor",
    "arrival_soprano_any_of": [1,3,5],
    "require_flag_any_of": ["cadential_64"],
    "forbid_flag_any_of":   ["passing_64", "pedal_64"],
    "treat_I64_as_D": true,
    "phrygian_bass_step": true
  },
  "descriptors": ["pachelbel_core", "circle_of_fifths"],  // extra detectors (optional)
  "substitutions": { "V": ["♭II7"] },                    // augment allowed chords (optional)
  "score": { "base": 1.0 }                                // base score (optional)
}
```

### StepSpec fields
Each entry in `sequence` may specify:

- `roman_root_any_of: string[]` — allowed Roman roots for the step. This is **inversion‑agnostic**
  unless the allowed set explicitly includes an inversion figure (e.g., `"V65"`).
- `role: "T"|"PD"|"D"|"T_or_D"` (optional) — functional role to require.
- `inversion_any_of: string[]` (optional) — enforce inversions (e.g., `["64", "65"]`).
- `optional: true` (optional) — step may be skipped when matching window bounds.

> **Note:** Step‑level flag requirements should be expressed via **pattern‑level**
> `require_flag_any_of` / `forbid_flag_any_of` for clarity.

### Families (taxonomy)
Common values: `cadence`, `pd_d_chain`, `schema`, `sequence`, `jazz_pop`, `mixture_modal`, `prolongation`.

---

## 4) Matching pipeline (what happens under the hood)

1. **Windowing** — For each pattern, slide a window of size `window.min..window.max` over the tokens.
2. **Substitutions** — Expand each step’s `roman_root_any_of` via the current **profile** (style). E.g., in `jazz`, `V ≈ ♭II7`.
3. **Step matching** — For each step in order, the matcher checks:
   - Root match (inversion‑sensitive **only** if the allowed set names an inversion like `"V65"`).
   - Optional `inversion_any_of`.
   - **Role match** using the token’s **effective role** (see below).
4. **Constraints** — If all steps align, run pattern‑level constraints:
   - `mode`, `arrival_soprano_any_of`, `require_flag_any_of`, `forbid_flag_any_of`, `phrygian_bass_step`, etc.
5. **Descriptors** — Optional phrase‑level detectors may further validate (e.g., `pachelbel_core`, `circle_of_fifths`, `chromatic_mediant`).
6. **Scoring** — Start from `score.base`; (optional) bonuses may apply (e.g., stylistic inversion preference).
7. **Collect candidate** — Record `{id, name, family, score, span=[i,j], evidence}`.
8. **Best non‑overlapping cover** — Use interval‑scheduling DP to choose the max‑score set of non‑overlapping matches.

### Effective role & cadential 6–4
Some patterns can set `"treat_I64_as_D": true`. In that case, during step matching the engine computes an
**effective role** per token:

- If a token is **I⁶⁴** (`roman` ends with `64` and `roman_base()` is `I`) and either:
  - the token is flagged `cadential_64`, **or**
  - the **next** token’s `roman_base()` starts with `V`,

then the token’s effective role becomes **`D`** for this match attempt only.

This makes **PAC** patterns robust to cadential 6–4 realizations without misclassifying passing/pedal 6–4 elsewhere. You can further tighten with `require_flag_any_of`/`forbid_flag_any_of`.

---

## 5) Substitution profiles

Style‑specific equivalences live in the `SubstitutionEngine` and are selected via the `profile` parameter
(`"classical"`, `"jazz"`, `"pop"`). They influence StepSpec root checks and avoid pattern duplication.

Examples:

- **Classical**: conservative; few or no dominant replacements.
- **Jazz**: allow **tritone sub** `V ↔ ♭II7`; treat `°7` as a **rootless** `V7♭9` where appropriate.
- **Pop**: ignore extended tensions (7/9/11/13) as mere color.

> Profiles are applied at match‑time; JSON stays clean and portable across styles.

---

## 6) Built‑in constraints

Pattern‑level constraints implemented by `ConstraintValidator`:

- `mode: "major"|"minor"` — require global mode (if available from upstream).
- `arrival_soprano_any_of: [..]` — require soprano degree on the **arrival** token.
- `soprano_any_of: [..]` — allow soprano degree **somewhere in the window**.
- `require_flag_any_of: [..]` — any token in window must carry one of these flags.
- `forbid_flag_any_of: [..]` — no token in window may carry any of these flags.
- `phrygian_bass_step: true` — require a −1 step into **V** (uses `bass_motion_from_prev`).
- `treat_I64_as_D: true` — local role remap (see effective role above).

If a field your constraint depends on is missing (e.g., no soprano or motion info), the constraint may
conservatively pass or fail depending on its semantics; tighten only when your upstream provides the signal.

---

## 7) Descriptors (phrase‑level detectors)

Descriptors complement sequence checks with broader musical context. Implemented detectors include:

- `pachelbel_core` — exact inversion‑insensitive root template `I–V–vi–iii–IV–I–IV–V` (8 chords).
- `circle_of_fifths` — detects contiguous down‑a‑fifth motion; tolerant of −7 semitone **or** −5 diatonic coding.
- `chromatic_mediant` — flags presence of common chromatic mediant markers (supports `♭/♯` and `b/#`).
- (optional/experimental) `prinner`, `monte_or_fonte`, `romanesca`, `lament_tetrachord` — can be enabled as needed.

Add new detectors by extending `DescriptorRegistry` and referencing their names in `pattern.descriptors`.

---

## 8) Examples

### A. Pop loop (vi–IV–I–V)
```json
{
  "id": "pop_vi_IV_I_V",
  "family": "jazz_pop",
  "name": "vi–IV–I–V",
  "window": {"min": 4, "max": 4},
  "sequence": [
    {"roman_root_any_of": ["vi"]},
    {"roman_root_any_of": ["IV"]},
    {"roman_root_any_of": ["I"]},
    {"roman_root_any_of": ["V"]}
  ]
}
```

### B. ii–V–I (jazz/classical macro)
```json
{
  "id": "ii_V_I_root_macro",
  "family": "jazz_pop",
  "name": "ii–V–I",
  "window": {"min": 3, "max": 3},
  "sequence": [
    {"roman_root_any_of": ["ii", "ii7", "iiø7", "ii6", "ii65"]},
    {"roman_root_any_of": ["V", "V7", "♭II7"]},
    {"roman_root_any_of": ["I", "i", "Imaj7"]}
  ],
  "substitutions": {"V": ["♭II7"]}
}
```

### C. Cadential 6–4 → V → I (strict)
```json
{
  "id": "cadential_64_to_V_to_I",
  "family": "cadence",
  "name": "Cadential 6–4 → V → I",
  "window": {"min": 2, "max": 3},
  "sequence": [
    {"roman_root_any_of": ["I"], "inversion_any_of": ["64"]},
    {"roman_root_any_of": ["V", "V7"]},
    {"roman_root_any_of": ["I", "i"], "optional": true}
  ],
  "constraints": {
    "treat_I64_as_D": true,
    "require_flag_any_of": ["cadential_64"],
    "forbid_flag_any_of": ["passing_64", "pedal_64"]
  },
  "score": {"base": 1.0}
}
```

### D. Pachelbel canon core (schema)
```json
{
  "id": "pachelbel_canon_core_roots",
  "family": "schema",
  "name": "Pachelbel canon core (root template)",
  "window": {"min": 8, "max": 8},
  "sequence": [
    {"roman_root_any_of": ["I"]},
    {"roman_root_any_of": ["V"]},
    {"roman_root_any_of": ["vi"]},
    {"roman_root_any_of": ["iii"]},
    {"roman_root_any_of": ["IV"]},
    {"roman_root_any_of": ["I"]},
    {"roman_root_any_of": ["IV"]},
    {"roman_root_any_of": ["V"]}
  ]
}
```

---

## 9) Scoring & best‑cover selection

Each pattern may provide `score.base` (default 1.0). The matcher assigns this score to the candidate.
You can add future bonuses (e.g., inversion preference, voice‑leading) to break ties.

The **IntervalSchedulingSolver** then selects a set of non‑overlapping candidates with maximum total score.
This is the classic weighted interval scheduling DP (O(M log M)) where M is candidate count.

---

## 10) Profiles & calling the matcher

You can run the matcher under different **profiles** to enable style‑specific substitutions:

```python
result = matcher.match(tokens, profile="classical")  # or "jazz", "pop"
```

## 11) Tuning & parameter recommendations

This section gives **practical defaults** and **when to relax/tighten** knobs so patterns are both
robust and discriminative.

### A. Window sizes (`window.min` / `window.max`)
- **Cadences**
  - PAC/IAC: `{min: 2, max: 3}` (usually `V→I` with optional cadential 6–4 or I elision)
  - Half cadence: `{min: 1, max: 4}` (ends on V; keep `min=1` so short arrivals are allowed)
  - Phrygian: `{min: 2, max: 2}` (strict), or `{min: 2, max: 3}` (allow pickup PD)
- **Pop/Jazz macros**
  - 4‑chord loops (e.g., `I–V–vi–IV`, `vi–IV–I–V`): `{min: 4, max: 4}`
  - ii–V–I: `{min: 3, max: 3}` (keep it tight to avoid drift)
- **Schemata (Pachelbel, Prinner, etc.)**
  - Pachelbel root template: `{min: 8, max: 8}`
  - Prinner / Monte‑Fonte: `{min: 3, max: 5}` depending on how much elision you allow

**Rule of thumb:** set `max = min` for canonical, fixed spans; allow `max > min` only when genuine
surface variation is common (pickups, cadential 6–4, elisions).

### B. Optional steps (`optional: true`)
Use sparingly, to handle **common elisions** without exploding false positives:
- PAC/IAC: make the final tonic step optional if you want to catch phrase endings that **omit the last I**.
- Cadential 6–4: allow the I arrival to be optional (often the cadence is heard at V).
- Schema variants (e.g., Prinner): allow a missing arrival tone when the soprano compresses to 3 notes.

Avoid optional steps in 3‑ and 4‑chord **macro loops**—it weakens discrimination and causes overlap.

### C. Inversions
- **Default**: **do not** require inversions; rely on `roman_root_any_of` with the matcher’s
  inversion‑insensitive comparison (`roman_base`).
- **Require inversions** only when identity‑defining:
  - Cadential 6–4: `inversion_any_of: ["64"]` on I, plus `treat_I64_as_D` and flags.
  - Phrygian: `iv6 → V` in minor.
  - V⁴₂ behavior (7th in bass) if you explicitly encode it.

### D. Functional roles (`role`)
- Prefer **role‑agnostic** steps for **macros** (ii–V–I, pop loops). Roles vary by context and profile.
- Use role checks for **cadences** and **PD→D→T** chains where function is musically the point.
- When unsure, use `"T_or_D"` to keep doors open without collapsing PD.

### E. Constraints
- `arrival_soprano_any_of`: require for **PAC variants**; keep ranges tight (e.g., `[1,3,5]`).
- `require_flag_any_of` / `forbid_flag_any_of`: use to **disambiguate 6–4s** (cadential vs passing/pedal).
- `phrygian_bass_step`: enable once your upstream provides `bass_motion_from_prev`; otherwise prefer the relaxed variant.
- `treat_I64_as_D`: set on cadence patterns to robustly match I⁶⁴→V; pair with flag constraints when available.

### F. Substitutions & profiles
- **Classical**: minimal substitutions; keep patterns literal.
- **Jazz**: include `"substitutions": {"V": ["♭II7"]}` in ii–V–I patterns; let the profile expand the allowed set.
- **Pop**: ignore tensions (7/9/11/13) in allowed roots; match on the base.

### G. Scoring hints
- Keep `score.base` simple (0.8–1.2). Use small bonuses to break ties:
  - +0.1 if `ii` appears in first inversion before V (classical bias).
  - +0.1 if `arrival_soprano` matches the targeted scale degree (e.g., 1 for PAC‑on‑1).
- Avoid heavy score spreads; the DP cover works best when candidates are roughly comparable.

### H. Mining parameters (for `mine_patterns_from_corpus.py`)
- `--min_n 3 --max_n 4` for pop/jazz corpora; `--min_n 2 --max_n 3` for chorales.
- Enable **adjacent‑duplicate collapse** to avoid `I–I`/`V–V` noise (already on in the miner).
- Post‑process cadences into **single macros** instead of keeping raw bigrams.

### I. When to add a relaxed companion pattern
Create a **relaxed** variant when upstream signals are incomplete (missing soprano degrees or bass motion):
- `cadence_phrygian_relaxed` alongside strict `cadence_phrygian`.
- Root‑only `pachelbel_canon_core_roots` alongside `pachelbel_core` descriptor.

Tighten or remove relaxed entries as your tokenization improves.

---

## 12) Validation & tests

The `validate_core_patterns()` suite exercises cadences, ii–V–I, pop loops, Phrygian, and Pachelbel.
Tests are **name/alias/family aware** so macro names or their component evidence can pass.

Add dedicated fixtures for:

- **Cadential 6–4**: include `I64` with the `cadential_64` flag and a following `V`.
- **Phrygian**: minor `iv6 → V` (optionally with −1 bass step).
- **Pachelbel**: 8‑chord root template in the target key.

---

## 13) Pattern mining (optional workflow)

`scripts/mine_patterns_from_corpus.py` can auto‑propose candidates from corpora:

- Input: `--source music21-bach` or `--json my_songs.json` with Roman streams.
- Output: `candidates_patterns.json` and `ngram_frequencies.csv` you can curate and merge.
- Heuristics: inversion‑agnostic roots, rotation awareness for pop loops, basic cadence macros.

---

## 14) Extending the engine

- **New patterns**: prefer **root templates** with minimal roles; add constraints for the tricky cases.
- **New constraints**: implement a `ConstraintChecker` subclass and register it in `ConstraintValidator`.
- **New descriptors**: add a checker in `DescriptorRegistry` and reference it by name in patterns.
- **Profiles**: extend `SubstitutionEngine` maps per style; keep JSON portable.
- **Inversions**: make them optional unless identity‑defining (cadential 6–4, Phrygian iv6, V42 behavior).

---

## 15) Observability & debugging

Each match records `span`, `score`, `family`, and `name`. You can also collect `evidence` per step
(e.g., which token matched which spec, which constraint/descriptor passed) to aid debugging.

For troubleshooting:

- Dump `tokens` with `roman`, `role`, `soprano_degree`, `flags`.
- Log which substitutions the profile expanded for each step.
- Enable trace on constraint/descriptor checks to see why a near‑miss failed.

---

## 16) Known limitations

- The engine assumes a stable global key/mode; frequent tonicizations can confuse simple patterns.
- Without soprano/motion info, some constraints (arrival soprano, Phrygian step) fall back to looser checks.
- Descriptors are conservative by default; enable or extend as needed per repertoire.

---

## 17) Version & contact

This README describes the **refactored matcher** with effective‑role support (`treat_I64_as_D`),
flag constraints (`require_flag_any_of`, `forbid_flag_any_of`), improved descriptors (Pachelbel, chromatic mediant,
robust circle‑of‑fifths), and profile‑aware root matching. If you see mismatches with code, grep for the
corresponding checker names in `matcher.py`.

```
