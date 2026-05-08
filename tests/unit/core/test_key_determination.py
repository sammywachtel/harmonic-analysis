"""Spot-check tests for hintless key determination.

These tests exist because the analyzer used to flip a textbook major-key
progression like ``C Am F G C`` (I-vi-IV-V-I in C major) to the relative
minor when no key hint was supplied. The bug lived in the unified pattern
service's modal-signature router: any minor chord in the progression
flagged "Dorian", which routed the result through the minor-key fallback
even when the cadence evidence said major.

The fix added a pair of detectors to ``UnifiedPatternService``: a 5-chord
``_matches_I_vi_IV_V_I_pattern`` for the doo-wop loop, and a plain
``_matches_V_I_major_pattern`` for V→I cadences resolving to a major
triad. Both apply the cadence-quality principle: the *resolving* chord's
quality settles the mode of the key, not the V chord's. G→C
(major→major) lands on C major; B7→Em (dominant→minor) lands on E minor;
the interval math is identical in both cases — the resolution quality is
what breaks the tie.

Two ambiguous progressions (``Em G C D`` and ``Am C F G``) are also
locked in here. Either tonal interpretation is musically defensible; the
tests assert whatever the heuristic actually produces with a written
defense in the docstring, so a future heuristic change has to either
keep this answer or come up with a deliberate reason to change it.
"""

from __future__ import annotations

import asyncio

import pytest

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


@pytest.fixture(scope="module")
def service() -> PatternAnalysisService:
    """Shared pattern-analysis service for end-to-end checks."""
    return PatternAnalysisService()


def _run_async(coro):  # type: ignore[no-untyped-def]
    """Tiny helper so the sync test body can await the async service call.

    pytest-asyncio is configured strict-mode in this repo; rather than
    wire up the async-test plumbing for a one-liner, we run the
    coroutine through asyncio.run. Cheap, isolated, fits the
    direct-call style these spot-checks want.
    """
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Hard-requirement spot checks (named in iteration plan AC3)
# ---------------------------------------------------------------------------


def test_C_Am_F_G_C_returns_C_major(service: PatternAnalysisService) -> None:
    """``C Am F G C`` — the doo-wop loop reproducer.

    I-vi-IV-V-I in C major, all five chord roots and qualities consistent
    with that reading. The 5-chord detector catches this directly; the
    final V→I to a major C nails the cadence-quality gate.

    Pre-fix: analyzer returned C minor because the modal-signature router
    flagged "any minor chord = Dorian" and the minor-key fallback fired
    even though the actual cadence is plainly major.
    """
    result = _run_async(
        service.analyze_with_patterns_async(
            ["C", "Am", "F", "G", "C"], profile="classical"
        )
    )
    assert result.primary.key_signature == "C major"
    # The vi chord must be lowercase 'vi', not '♯vi' (the latter was the
    # symptom: the analyzer was reading it as a raised-vi in a C-minor
    # context).
    assert result.primary.roman_numerals[1] == "vi"


def test_Em_Am_B7_Em_stays_E_minor(service: PatternAnalysisService) -> None:
    """``Em Am B7 Em`` — minor-key regression guard.

    V7→i to a minor triad is an authentic cadence in E minor. The
    cadence-quality gate must NOT flip this to major just because the
    interval math (B→E = 5 semitones) looks like a V→I. The resolving
    Em is minor; the key is minor. This is the load-bearing case for the
    cadence-quality tie-break: identical +5 root motion as G→C, but the
    resolving-chord quality settles the mode in the opposite direction.
    """
    result = _run_async(
        service.analyze_with_patterns_async(
            ["Em", "Am", "B7", "Em"], profile="classical"
        )
    )
    assert result.primary.key_signature == "E minor"


def test_Am_G_F_E_andalusian_stays_A_minor(service: PatternAnalysisService) -> None:
    """``Am G F E`` — Andalusian cadence guard.

    Ends on a major E triad, but F→E is interval 11 (a leading-tone
    half-step), not 5 (a perfect fourth). The V→I detector keys on the
    +5 interval, so the trailing major chord must NOT trick the matcher
    into thinking this is E major. It's the bVII→V endgame in A minor —
    a different beast entirely.
    """
    result = _run_async(
        service.analyze_with_patterns_async(["Am", "G", "F", "E"], profile="classical")
    )
    assert result.primary.key_signature == "A minor"


# ---------------------------------------------------------------------------
# Truly ambiguous spot checks — outcomes locked to current heuristic
# ---------------------------------------------------------------------------


def test_Em_G_C_D_locked_to_E_minor(service: PatternAnalysisService) -> None:
    """``Em G C D`` — ambiguous between E minor and G major.

    Could be read as either:
      * E minor: i-III-VI-bVII (Aeolian vamp ending on bVII)
      * G major: vi-I-IV-V (deceptive opening, ending on V)

    The current heuristic chooses E minor: the first chord is Em, which
    drops first_quality into the "minor" branch of
    `_infer_key_from_progression`, and `_detect_functional_major_key`
    finds no matching pattern (E→G→C→D is not vi-ii-V-I or vi-IV-I-V or
    any other named loop), so it falls through to `f"{first_root} minor"`.

    Defensible: the progression starts with the named tonic candidate as
    a minor triad, doesn't end on a strong major-key cadence (D is V of
    G but no I of G follows), and the chord set is fully diatonic to E
    Aeolian. If a future heuristic decides to read this as G major,
    that's a deliberate change requiring its own justification — this
    test will catch the drift.
    """
    result = _run_async(
        service.analyze_with_patterns_async(["Em", "G", "C", "D"], profile="classical")
    )
    assert result.primary.key_signature == "E minor"


def test_Am_C_F_G_locked_to_A_minor(service: PatternAnalysisService) -> None:
    """``Am C F G`` — ambiguous between A minor and C major.

    Could be read as either:
      * A minor: i-III-VI-VII (Aeolian vamp)
      * C major: vi-I-IV-V (deceptive opening)

    The current heuristic chooses A minor for the same reason as
    ``Em G C D``: first chord is Am (minor), no functional-major
    pattern in `_detect_functional_major_key` matches the
    A-C-F-G interval profile, so the minor-first-chord branch wins.

    Defensible: the progression doesn't resolve — it ends on V of C
    (G major), but no C follows. Without a resolving I, neither reading
    is privileged on cadence grounds, so the first-chord heuristic is a
    reasonable fallback. Whichever way a future heuristic goes, the
    decision should be deliberate; this test pins the current behavior
    so drift is visible.
    """
    result = _run_async(
        service.analyze_with_patterns_async(["Am", "C", "F", "G"], profile="classical")
    )
    assert result.primary.key_signature == "A minor"
