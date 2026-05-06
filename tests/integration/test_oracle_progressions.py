"""Hand-curated oracle tests across all *.oracle.json fixtures.

Auto-discovers every fixture file matching tests/fixtures/progressions/*.oracle.json
and parametrizes a single test function across all cases. Drop a new oracle
file into the directory and the next pytest run picks it up — no test code
to add.

Unlike the bulk auto-generated suite (which validates the analyzer against
expectations computed by the same code paths it tests), every expected value
in an *.oracle.json file is hand-written from music theory. When one of
these fails, the analyzer is wrong — not the fixture.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

ORACLE_DIR = Path(__file__).parent.parent / "fixtures" / "progressions"


def _load_all_cases() -> List[Tuple[str, Dict[str, Any]]]:
    """Return list of (fixture_filename, case_dict) tuples across all
    *.oracle.json files, sorted for deterministic ordering."""
    cases: List[Tuple[str, Dict[str, Any]]] = []
    for path in sorted(ORACLE_DIR.glob("*.oracle.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data.get("progressions", []):
            cases.append((path.name, case))
    return cases


CASES = _load_all_cases()


def _case_id(item: Tuple[str, Dict[str, Any]]) -> str:
    fixture, case = item
    # Strip the .oracle.json suffix for a tighter test ID
    short = fixture.removesuffix(".oracle.json")
    return f"{short}::{case['name']}"


@pytest.fixture(scope="module")
def service() -> PatternAnalysisService:
    return PatternAnalysisService()


@pytest.mark.parametrize("fixture_and_case", CASES, ids=[_case_id(c) for c in CASES])
@pytest.mark.asyncio
async def test_oracle_progression(
    service: PatternAnalysisService,
    fixture_and_case: Tuple[str, Dict[str, Any]],
) -> None:
    """Run analyzer end-to-end and assert against hand-curated expectations.

    By default no key hint is passed — the analyzer detects the key itself,
    mirroring how a real caller invokes it. Cases set key_hint when needed
    to isolate the test from unrelated key-detection ambiguity (explicitly
    documented in the case comment).
    """
    fixture, case = fixture_and_case
    result = await service.analyze_with_patterns_async(
        case["chords"],
        profile="classical",
        key_hint=case.get("key_hint"),
    )
    primary = result.primary
    rationale = case.get("comment", "")

    # Roman numerals: exact-sequence match. The whole point of an oracle.
    assert primary.roman_numerals == case["roman_numerals"], (
        f"\n[{fixture} :: {case['name']}] Roman numeral mismatch."
        f"\n  chords:    {case['chords']}"
        f"\n  expected:  {case['roman_numerals']}"
        f"\n  got:       {primary.roman_numerals}"
        f"\n  rationale: {rationale}"
    )

    # Key: the analyzer should land on the expected tonal center.
    assert primary.key_signature == case["key"], (
        f"\n[{fixture} :: {case['name']}] Key mismatch."
        f"\n  expected: {case['key']!r}"
        f"\n  got:      {primary.key_signature!r}"
        f"\n  rationale: {rationale}"
    )

    # Negative mode assertions: the analyzer must not commit to a mode whose
    # characteristic notes are absent from the chord pitches.
    forbidden_modes = case.get("mode_must_not_be", [])
    if forbidden_modes:
        assert primary.mode not in forbidden_modes, (
            f"\n[{fixture} :: {case['name']}] Analyzer committed to a mode "
            "not supported by the chord pitches."
            f"\n  forbidden: {forbidden_modes}"
            f"\n  got:       {primary.mode!r}"
            f"\n  rationale: {rationale}"
        )

    # Positive mode assertion: when chord pitches genuinely support a specific
    # mode (raised 6 for Dorian, ♭7 for Mixolydian, etc.), it must be reported.
    expected_mode = case.get("mode_expected")
    if expected_mode is not None:
        assert primary.mode == expected_mode, (
            f"\n[{fixture} :: {case['name']}] Mode mismatch (positive control)."
            f"\n  expected: {expected_mode!r}"
            f"\n  got:      {primary.mode!r}"
            f"\n  rationale: {rationale}"
        )
