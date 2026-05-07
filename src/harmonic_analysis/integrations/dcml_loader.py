"""DCML corpus loader — fetch-at-test-time, no vendoring.

Loads hand-annotated harmonic-analysis data from the DCML Annotated Beethoven
Corpus (CC-BY-NC-SA 4.0) and converts it into oracle fixtures matching the
shape of ``tests/fixtures/progressions/*.oracle.json``.

Design notes
============

**Path B (no vendoring).** This library is MIT-licensed; DCML is CC-BY-NC-SA.
We never copy DCML data into our git repo. Instead we shallow-clone the
upstream corpus at a pinned commit SHA into a cache directory under
``tests/data/oracles/dcml_cache/`` (gitignored). Tests + scripts that need
DCML data call :func:`ensure_corpus_cached` on demand. CI caches the directory
keyed on the pinned SHA so the clone happens once per cache lifetime.

**Apples-to-apples ground truth.** DCML annotates Roman numerals with
inversion figures (``V6``, ``I64``) and secondary-dominant context (``V7/IV``)
that our analyzer doesn't try to produce — it emits root-position, chord-as-
it-stands labels. So we don't compare analyzer output to DCML's full annotation
string. Instead, the loader uses DCML's pre-decomposed ``root`` /
``chord_type`` / ``globalkey`` columns to derive a *simpler* expected Roman
numeral that an ideal analyzer (matching our project's conventions) would
produce. Disagreements between this derived expectation and the actual
analyzer output are real bugs, not representation gaps.

**Sidesteps task #8.** The loader passes ``key_hint=globalkey`` to the
analyzer. The corpus has the key labeled definitively; passing it isolates
our oracle from the major-mode key-detection bug we already filed.

**Out of scope for v1.** Modulation handling (split at localkey changes),
pedal points, voice-leading inversions, alteration parens (``V(b9)``),
secondary-dominant function detection, augmented sixths.
"""

from __future__ import annotations

import csv
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache management — fetch at test time, pin by SHA
# ---------------------------------------------------------------------------

# Pinned commit SHA for reproducibility. Bumping this is a deliberate decision:
# DCML annotations get re-reviewed periodically and a bump can change which
# cases pass/fail. Always bump in a dedicated PR with a triage of the diff.
DCML_ABC_REPO = "https://github.com/DCMLab/ABC.git"
# Pinned at HEAD-of-main on 2026-05-06. To bump: open a dedicated PR with
# the diff between old and new annotation outputs and a manual triage of
# any newly-failing oracle cases.
DCML_ABC_PINNED_SHA = (
    "b6b7d38500bacb30c81db7e09d8790df1a2edd46"  # pragma: allowlist secret
)

# Tier-1 movement set: 5 minor-key first movements + the original C-major mvt-2
# from op. 18-4. Sonata-form first movements have the densest harmonic
# activity. Single source of truth — both the test harness and the
# pedagogical overview generator import this.
DEFAULT_MOVEMENTS: List[str] = [
    "n04op18-4_01",  # C minor — op. 18 No. 4 mvt 1 (early, classical)
    "n04op18-4_02",  # C major — op. 18 No. 4 mvt 2 (contrast piece)
    "n08op59-2_01",  # E minor — op. 59 No. 2 mvt 1 ("Razumovsky" #2)
    "n11op95_01",  # F minor — op. 95 mvt 1 ("Serioso", late-middle)
    "n14op131_01",  # C# minor — op. 131 mvt 1 (late, fugal)
    "n15op132_01",  # A minor — op. 132 mvt 1 (late "Heiliger Dankgesang")
]


def ensure_corpus_cached(
    repo_url: str,
    pinned_sha: str,
    cache_dir: Path,
) -> Path:
    """Shallow-fetch *repo_url* at *pinned_sha* into *cache_dir*; idempotent.

    Returns the path to the cached corpus root. If the directory already
    exists with a ``.git`` subdir AND its HEAD matches the pinned SHA we
    trust it and return without fetching. Mismatched SHAs trigger a
    re-fetch (so bumping the pin works without manual cache cleanup).

    Implementation note: ``git clone --depth=1 --branch <X>`` only accepts
    branch / tag names, not SHAs. To pin precisely we have to init + fetch
    + checkout in three steps. Slightly more code, but the pinning is the
    whole point of Path B.
    """
    cache_dir = cache_dir.expanduser().resolve()

    if (cache_dir / ".git").exists():
        try:
            head = subprocess.check_output(
                ["git", "-C", str(cache_dir), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            if head == pinned_sha:
                return cache_dir
            logger.info(
                "Cache at %s is at %s, expected %s — re-fetching",
                cache_dir,
                head[:8],
                pinned_sha[:8],
            )
        except subprocess.CalledProcessError:
            pass  # Fall through to re-init

    # Either no cache yet, or stale cache. Wipe + re-init.
    if cache_dir.exists():
        import shutil

        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching %s @ %s into %s", repo_url, pinned_sha, cache_dir)
    subprocess.run(["git", "init", "--quiet", str(cache_dir)], check=True)
    subprocess.run(
        ["git", "-C", str(cache_dir), "remote", "add", "origin", repo_url],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(cache_dir),
            "fetch",
            "--depth=1",
            "--quiet",
            "origin",
            pinned_sha,
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(cache_dir), "checkout", "--quiet", "FETCH_HEAD"],
        check=True,
    )
    return cache_dir


# ---------------------------------------------------------------------------
# Line-of-fifths arithmetic
# ---------------------------------------------------------------------------

# Anchored so F = 0; each step + adds a sharp / removes a flat.
# DCML's ``root`` and ``chord_tones`` columns are LoF offsets relative to
# the globalkey tonic (positive = sharper, negative = flatter).
_LOF_LETTERS = {
    -14: "Fbb",
    -13: "Cbb",
    -12: "Gbb",
    -11: "Dbb",
    -10: "Abb",
    -9: "Ebb",
    -8: "Bbb",
    -7: "Fb",
    -6: "Cb",
    -5: "Gb",
    -4: "Db",
    -3: "Ab",
    -2: "Eb",
    -1: "Bb",
    0: "F",
    1: "C",
    2: "G",
    3: "D",
    4: "A",
    5: "E",
    6: "B",
    7: "F#",
    8: "C#",
    9: "G#",
    10: "D#",
    11: "A#",
    12: "E#",
    13: "B#",
    14: "F##",
    15: "C##",
}
_LETTER_TO_LOF = {v: k for k, v in _LOF_LETTERS.items()}


# Semitone interval covered by N fifths (perfect fifth = 7 semitones, mod 12).
def _semitone_for_lof_offset(offset: int) -> int:
    return (offset * 7) % 12


def letter_for_lof(offset_from_globalkey: int, globalkey_letter: str) -> str:
    """Translate ``root=N`` (LoF offset from globalkey tonic) to a letter."""
    gk_pos = _LETTER_TO_LOF.get(_normalize_letter(globalkey_letter))
    if gk_pos is None:
        raise ValueError(f"Unknown globalkey letter: {globalkey_letter!r}")
    target = gk_pos + offset_from_globalkey
    if target not in _LOF_LETTERS:
        raise ValueError(
            f"LoF offset out of supported range: {target} "
            f"(from {globalkey_letter!r} + {offset_from_globalkey})"
        )
    return _LOF_LETTERS[target]


def _normalize_letter(letter: str) -> str:
    """Normalize DCML's letter encoding to our LoF table.

    DCML uses lowercase for minor keys (``c`` = C minor, ``C`` = C major) but
    the letter-to-pitch mapping is the same. We uppercase the first character
    only — accidentals (``b``/``#``) keep their case.
    """
    if not letter:
        return letter
    return letter[0].upper() + letter[1:]


# ---------------------------------------------------------------------------
# Chord type → symbol suffix
# ---------------------------------------------------------------------------

# DCML's chord_type column → (analyzer chord-symbol suffix, expected-roman-suffix)
# - chord_symbol_suffix: appended to root letter for analyzer input
# - roman_suffix: appended to base roman AFTER case + ° / + adornments
#
# IMPORTANT: roman_suffix here does NOT include the quality marker (°, +, ø).
# The case-correction code in convert_row() adds those, conditional on
# whether the base roman already carries them (e.g., minor_romans[11] is
# pre-baked as "vii°", which would double-stamp if we appended another ° here).
_CHORD_TYPE_TABLE: Dict[str, tuple[str, str]] = {
    # Triads
    "M": ("", ""),  # major triad
    "m": ("m", ""),  # minor triad
    "o": ("dim", ""),  # diminished triad   (° added in convert_row)
    "+": ("aug", ""),  # augmented triad    (+ added in convert_row)
    # Sevenths — suffix carries only the '7' (and 'maj' for MM7); the quality
    # marker is added separately so it sits BEFORE the 7 (e.g. 'vii°7' not 'vii7°').
    "Mm7": ("7", "7"),  # dominant 7th
    "mm7": ("m7", "7"),  # minor 7
    "MM7": ("maj7", "maj7"),  # major 7
    "mM7": ("mM7", "M7"),  # minor-major 7 (rare)
    "o7": ("dim7", "7"),  # fully-diminished 7 (° + 7 → "°7")
    "%7": ("m7b5", "ø7"),  # half-diminished 7  (ø not in any base table; safe)
    # Augmented sevenths
    "+M7": ("augmaj7", "maj7"),  # + + maj7 → "+maj7"
    "+7": ("aug7", "7"),  # + + 7 → "+7"
}


# ---------------------------------------------------------------------------
# Roman tables — mirror the analyzer's CURRENT conventions
# ---------------------------------------------------------------------------

# Major key: each entry is the "default" roman at that semitone offset from
# tonic; case is later adjusted based on actual chord quality.
_MAJOR_ROMANS = [
    "I",
    "♭II",
    "II",
    "♭III",
    "III",
    "IV",
    "♭V",
    "V",
    "♭VI",
    "VI",
    "♭VII",
    "VII",
]

# Minor key: matches src/.../token_converter.py's minor_romans table. The
# slot 6 entry was fixed in task #6 (♭v at the tritone, not ♭VI). The mixed
# convention at slots 3/8/10 (no flat on III/VI but flat on ♭VII) is task #9.
_MINOR_ROMANS = [
    "i",
    "♭II",
    "ii",
    "III",
    "iv",
    "IV",
    "♭v",
    "v",
    "VI",
    "♯VI",
    "♭VII",
    "vii°",
]


def _set_roman_case(roman: str, *, upper: bool) -> str:
    """Uppercase or lowercase the alphabetic part of a roman, preserving
    leading flat/sharp prefix and any trailing markers (e.g., ``°``).
    Mirrors the same helper used inside the analyzer."""
    m = re.match(r"^([♭b♯#]?)([ivIV]+)(.*)$", roman)
    if not m:
        return roman
    prefix, alpha, rest = m.groups()
    return prefix + (alpha.upper() if upper else alpha.lower()) + rest


# ---------------------------------------------------------------------------
# Row → chord symbol + expected roman
# ---------------------------------------------------------------------------


@dataclass
class RowConversion:
    """One DCML row converted into analyzer-compatible inputs and expectations."""

    chord_symbol: str
    expected_roman: str
    raw_chord_label: str  # DCML's `chord` column — kept for attribution / debug


def _is_minor_quality(chord_type: str) -> bool:
    return chord_type in {"m", "mm7", "mM7"}


def _is_dim_quality(chord_type: str) -> bool:
    return chord_type in {"o", "o7"}


def _is_half_dim_quality(chord_type: str) -> bool:
    return chord_type == "%7"


def convert_row(
    row: Dict[str, str], globalkey: str, globalkey_is_minor: bool
) -> Optional[RowConversion]:
    """Convert one DCML harmonies-TSV row to (chord_symbol, expected_roman).

    Returns ``None`` for rows we can't / shouldn't handle in v1:
    - empty / placeholder rows (``@none``)
    - chord types not in our table
    - rows with an active pedal point (out of v1 scope)
    """
    chord_label = (row.get("chord") or "").strip()
    chord_type = (row.get("chord_type") or "").strip()
    root_str = (row.get("root") or "").strip()

    if not chord_label or chord_label == "@none":
        return None
    if not chord_type or chord_type not in _CHORD_TYPE_TABLE:
        return None
    if not root_str:
        return None
    if (row.get("pedal") or "").strip():
        return None

    try:
        root_lof = int(root_str)
    except ValueError:
        return None

    chord_suffix, roman_suffix = _CHORD_TYPE_TABLE[chord_type]
    try:
        root_letter = letter_for_lof(root_lof, globalkey)
    except ValueError:
        return None
    chord_symbol = root_letter + chord_suffix

    # Expected roman: derive from interval + quality, NOT from DCML's annotation
    # (which carries inversion + secondary-dominant info we don't compare on).
    interval = _semitone_for_lof_offset(root_lof)
    table = _MINOR_ROMANS if globalkey_is_minor else _MAJOR_ROMANS
    base_roman = table[interval]

    if _is_dim_quality(chord_type):
        # Diminished: lowercase + exactly one '°'. Some table slots
        # pre-bake '°' (slot 11 = "vii°"); add it only if missing to
        # avoid 'vii°°7' double-stamping.
        base_roman = _set_roman_case(base_roman, upper=False)
        if "°" not in base_roman:
            base_roman += "°"
    elif _is_half_dim_quality(chord_type):
        # Half-dim: lowercase; 'ø' is part of roman_suffix (no base
        # tables pre-bake it, so doubling isn't a risk).
        base_roman = _set_roman_case(base_roman, upper=False)
    elif _is_minor_quality(chord_type):
        base_roman = _set_roman_case(base_roman, upper=False)
    elif chord_type in {"+", "+7", "+M7"}:
        # Augmented: uppercase + exactly one '+'. No table slot pre-bakes
        # '+', but stay defensive parallel to the dim handler.
        base_roman = _set_roman_case(base_roman, upper=True)
        if "+" not in base_roman:
            base_roman += "+"
    else:
        # Major-quality (M, Mm7, MM7) → uppercase roman
        base_roman = _set_roman_case(base_roman, upper=True)

    expected_roman = base_roman + roman_suffix
    return RowConversion(
        chord_symbol=chord_symbol,
        expected_roman=expected_roman,
        raw_chord_label=chord_label,
    )


# ---------------------------------------------------------------------------
# TSV parsing + phrase grouping
# ---------------------------------------------------------------------------


def parse_dcml_tsv(path: Path) -> List[Dict[str, str]]:
    """Load a DCML harmonies TSV. Stdlib only — no music21 / pandas."""
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def split_into_phrases(
    rows: List[Dict[str, str]],
    *,
    chunk_size: int = 8,
) -> List[List[Dict[str, str]]]:
    """Split a row list into oracle-sized chunks.

    Real DCML phrase markers (``phraseend``, ``cadence``) turn out to be
    sparse across the ABC corpus — most movements have zero of either.
    So we use a two-pass split:

    1. **Localkey boundaries** are real musical events (modulations).
       Modulation handling is out of v1 scope, so each constant-localkey
       segment becomes its own group.
    2. **Long segments get window-chunked** into ``chunk_size``-chord
       windows. The chunks aren't musically meaningful boundaries, but
       they keep individual oracle cases small enough to inspect by eye
       when one fails. Each chord is independently labeled by DCML, so
       splitting mid-phrase doesn't introduce error — it just changes the
       granularity of the test.

    DCML phraseend markers (``}``, ``}{``) are still respected when
    present — they just don't fire on most ABC movements.
    """
    # Pass 1: localkey + phraseend boundaries
    primary: List[List[Dict[str, str]]] = []
    current: List[Dict[str, str]] = []
    last_localkey: Optional[str] = None
    for row in rows:
        localkey = (row.get("localkey") or "").strip()
        phraseend = (row.get("phraseend") or "").strip()

        if last_localkey is not None and localkey and localkey != last_localkey:
            if current:
                primary.append(current)
                current = []
        last_localkey = localkey or last_localkey

        current.append(row)

        if phraseend in {"}", "}{"}:
            if current:
                primary.append(current)
                current = []
    if current:
        primary.append(current)

    # Pass 2: window-chunk long segments
    chunked: List[List[Dict[str, str]]] = []
    for segment in primary:
        if len(segment) <= chunk_size:
            chunked.append(segment)
            continue
        for start in range(0, len(segment), chunk_size):
            chunked.append(segment[start : start + chunk_size])
    return chunked


# ---------------------------------------------------------------------------
# Fixture emitter
# ---------------------------------------------------------------------------


@dataclass
class DCMLFixtureCase:
    """One emitted oracle case (will serialize to JSON in the oracle file)."""

    name: str
    chords: List[str] = field(default_factory=list)
    key: str = ""
    key_hint: str = ""
    roman_numerals: List[str] = field(default_factory=list)
    source: str = "dcml_abc"
    source_movement: str = ""
    source_measures: str = ""
    source_commit: str = ""
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "chords": self.chords,
            "key": self.key,
            "key_hint": self.key_hint,
            "roman_numerals": self.roman_numerals,
            "source": self.source,
            "source_movement": self.source_movement,
            "source_measures": self.source_measures,
            "source_commit": self.source_commit,
            "comment": self.comment,
        }


def _absolute_key(globalkey: str, is_minor: bool) -> str:
    """Render a DCML globalkey as our analyzer's expected key string.

    DCML uses lowercase for minor (``c`` = C minor) and we want
    ``"C minor"`` / ``"C major"``.
    """
    letter = _normalize_letter(globalkey)
    return f"{letter} {'minor' if is_minor else 'major'}"


def fixture_from_phrase(
    rows: List[Dict[str, str]],
    movement_id: str,
    pinned_sha: str,
    case_index: int,
    *,
    min_chords: int = 3,
    max_chords: int = 16,
) -> Optional[DCMLFixtureCase]:
    """Build one oracle case from a phrase's worth of rows.

    Returns ``None`` if:
    - The phrase is too short or too long
    - The phrase contains no convertible rows
    - The phrase is in a non-globalkey area (modulation — v1 only handles
      passages where localkey == globalkey or is empty/'I'/'i'). Modulation
      support is task 4-followup; see tests/data/oracles/README.md.
    """
    if not rows:
        return None
    globalkey = (rows[0].get("globalkey") or "").strip()
    is_minor = (rows[0].get("globalkey_is_minor") or "").strip() == "1"
    if not globalkey:
        return None

    # Skip modulating segments: localkey 'I' or 'i' or empty means "still
    # in the global key" — anything else is a tonicization or modulation
    # we don't yet resolve. Filter the whole phrase out rather than emit a
    # case with a wrong key context.
    GLOBALKEY_LOCALKEYS = {"", "I", "i"}
    for row in rows:
        lk = (row.get("localkey") or "").strip()
        if lk not in GLOBALKEY_LOCALKEYS:
            return None

    conversions: List[RowConversion] = []
    for row in rows:
        conv = convert_row(row, globalkey, is_minor)
        if conv is not None:
            conversions.append(conv)

    if len(conversions) < min_chords or len(conversions) > max_chords:
        return None

    first_mc = (rows[0].get("mc") or "").strip()
    last_mc = (rows[-1].get("mc") or "").strip()
    measures = f"{first_mc}-{last_mc}" if first_mc and last_mc else ""

    abs_key = _absolute_key(globalkey, is_minor)
    return DCMLFixtureCase(
        name=f"{movement_id}_phrase_{case_index:03d}",
        chords=[c.chord_symbol for c in conversions],
        key=abs_key,
        key_hint=abs_key,  # always pass the hint — DCML knows the key
        roman_numerals=[c.expected_roman for c in conversions],
        source="dcml_abc",
        source_movement=movement_id,
        source_measures=measures,
        source_commit=pinned_sha,
        comment=(
            f"DCML ABC {movement_id} mm. {measures}. Expected romans derived "
            f"from DCML's pre-decomposed root + chord_type columns using the "
            f"analyzer's current conventions; disagreements are real bugs."
        ),
    )


def fixtures_from_tsv(
    tsv_path: Path,
    movement_id: str,
    pinned_sha: str,
) -> List[DCMLFixtureCase]:
    """Convert one harmonies TSV into a list of oracle cases."""
    rows = parse_dcml_tsv(tsv_path)
    phrases = split_into_phrases(rows)
    cases: List[DCMLFixtureCase] = []
    for i, phrase in enumerate(phrases):
        case = fixture_from_phrase(phrase, movement_id, pinned_sha, i)
        if case is not None:
            cases.append(case)
    return cases


# ---------------------------------------------------------------------------
# Public top-level entry point
# ---------------------------------------------------------------------------


def build_oracle_for_movement(
    movement_id: str,
    cache_dir: Path,
    pinned_sha: str = DCML_ABC_PINNED_SHA,
) -> Dict[str, Any]:
    """Top-level: ensure cache, locate the TSV, emit a full fixture document.

    Returns a dict shaped like an existing ``*.oracle.json`` file
    (``description`` + ``progressions`` array), ready to dump with
    ``json.dump``.
    """
    corpus_root = ensure_corpus_cached(DCML_ABC_REPO, pinned_sha, cache_dir)
    tsv_path = corpus_root / "harmonies" / f"{movement_id}.harmonies.tsv"
    if not tsv_path.exists():
        raise FileNotFoundError(
            f"Movement TSV not found: {tsv_path} "
            f"(check movement_id and corpus structure)"
        )
    cases = fixtures_from_tsv(tsv_path, movement_id, pinned_sha)
    return {
        "description": (
            f"DCML Annotated Beethoven Corpus — {movement_id}. "
            f"Auto-generated from harmonies TSV at commit {pinned_sha}. "
            f"License: CC-BY-NC-SA 4.0 (data fetched at test time, never "
            f"vendored — see tests/data/oracles/README.md)."
        ),
        "schema_notes": [
            "Each case is one phrase (split at phraseend or localkey change).",
            "key_hint is always passed — DCML knows the global key, "
            "so we sidestep task #8.",
            "Expected romans derived from DCML root + chord_type, "
            "NOT from DCML's literal chord label (which carries inversion + "
            "secondary-dominant info we don't currently compare on).",
            "Modulation, pedal points, and chord_type values not in our table "
            "are skipped in v1.",
        ],
        "progressions": [c.to_dict() for c in cases],
    }
