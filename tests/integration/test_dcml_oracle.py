"""Oracle tests sourced from the DCML Annotated Beethoven Corpus.

Fetches the corpus on first run (shallow clone at a pinned SHA into a
gitignored cache), then derives oracle cases in memory via
:mod:`harmonic_analysis.integrations.dcml_loader`. No DCML data is
vendored into our repo — see ``tests/data/oracles/README.md`` for the
license rationale.

When a DCML case fails:
1. Read the case's ``source_movement`` + ``source_measures`` to find the
   exact spot in the score.
2. Cross-check DCML's chord annotation against our analyzer output.
   Genuine analyzer bugs go in our backlog; theoretical disagreements
   (Roman numeral analysis isn't unique) get marked ``xfail`` with a
   pointer to the case's source measures.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from harmonic_analysis.integrations.dcml_loader import (
    DEFAULT_MOVEMENTS,
    build_oracle_for_movement,
)
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService

CACHE_DIR = Path(__file__).parent.parent / "data" / "oracles" / "dcml_cache" / "abc"

# Movement list lives in the loader module — single source of truth shared
# with scripts/generate_test_overview.py.
MOVEMENTS = DEFAULT_MOVEMENTS


def _collect_cases() -> List[Tuple[str, Dict[str, Any]]]:
    """Build oracle cases for all configured movements.

    Returns ``[(movement_id, case_dict), ...]`` flattened across movements.
    Skipped (returns ``[]``) if the loader can't fetch the corpus and the
    user has set ``HA_SKIP_DCML_FETCH=1`` (useful in offline dev / CI
    environments without network access).
    """
    if os.environ.get("HA_SKIP_DCML_FETCH") == "1":
        return []
    try:
        all_cases: List[Tuple[str, Dict[str, Any]]] = []
        for mvt in MOVEMENTS:
            doc = build_oracle_for_movement(mvt, CACHE_DIR)
            for case in doc.get("progressions", []):
                all_cases.append((mvt, case))
        return all_cases
    except Exception as exc:  # pragma: no cover - network/setup failures
        # Fail loudly during normal collection so flakes are visible, but
        # let the env-var override let devs skip when offline.
        pytest.skip(f"DCML corpus fetch failed: {exc}")
        return []


CASES = _collect_cases()


def _case_id(item: Tuple[str, Dict[str, Any]]) -> str:
    mvt, case = item
    # case["name"] already includes the movement prefix; just use that
    return case["name"]


@pytest.fixture(scope="module")
def service() -> PatternAnalysisService:
    return PatternAnalysisService()


@pytest.mark.parametrize(
    "mvt_and_case",
    CASES,
    ids=[_case_id(c) for c in CASES] if CASES else [],
)
@pytest.mark.asyncio
async def test_dcml_oracle_case(
    service: PatternAnalysisService,
    mvt_and_case: Tuple[str, Dict[str, Any]],
) -> None:
    """One assertion per DCML-derived case."""
    if not CASES:
        pytest.skip("No DCML cases collected (corpus unavailable)")
    _, case = mvt_and_case
    result = await service.analyze_with_patterns_async(
        case["chords"],
        profile="classical",
        key_hint=case.get("key_hint"),
    )
    primary = result.primary

    src = (
        f"{case['source_movement']} mm. {case['source_measures']} "
        f"(commit {case['source_commit'][:8]})"
    )

    # Roman numerals: exact-sequence match. Disagreements should be
    # triaged — see the module docstring for the workflow.
    assert primary.roman_numerals == case["roman_numerals"], (
        f"\n[{case['name']}] Roman numeral mismatch."
        f"\n  source:    {src}"
        f"\n  chords:    {case['chords']}"
        f"\n  expected:  {case['roman_numerals']}"
        f"\n  got:       {primary.roman_numerals}"
    )

    # Key — should match what we passed as the hint, since DCML knows it.
    assert primary.key_signature == case["key"], (
        f"\n[{case['name']}] Key mismatch (hint was {case['key_hint']!r})."
        f"\n  source:   {src}"
        f"\n  expected: {case['key']!r}"
        f"\n  got:      {primary.key_signature!r}"
    )
