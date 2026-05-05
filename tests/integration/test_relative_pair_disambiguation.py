"""Integration test: ensemble disambiguates relative major/minor pairs.

The diagnostic recording that motivated this scope (`iwasonce_steinway.mp3`)
plays in B minor but Krumhansl-Schmuckler returns D major. K-S can't tell
relative pairs apart — they share pitch-class sets. The fix is the
ensemble: boundary chords on Bm + bass dominance at B + cadential V→i
patterns all break the tie toward B Aeolian.

This test constructs a synthetic WAV fixture that exhibits the same
property:
  * Time-averaged chroma is balanced enough that K-S leans D major
  * First and last chord events parse as Bm (boundary_chords vote)
  * Bass register dominates pitch class B (bass_dominance vote)
  * V→i patterns appear (F# → Bm transitions, cadential vote)

Under ``key_detection="default"`` (full ensemble), the verdict should be
B Aeolian. Under ``key_detection="ks_only"``, the verdict reverts to
whatever the K-S correlation returns — proving the ensemble is doing
the disambiguation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

# Skip the whole module if the audio extras aren't installed.
pytest.importorskip("librosa")
pytest.importorskip("soundfile")


def _generate_bm_diagnostic_wav(
    path: Path, duration_sec: float = 12.0, sr: int = 22050
) -> Path:
    """Synthesize a WAV that demonstrates the relative-pair problem.

    The construction goal: K-S correlation alone must lean D major; the
    ensemble must lean B Aeolian. Achieving this means tilting the chroma
    statistics toward D-major-prominent pitches (lots of D, F#, A) while
    keeping the chord events at the boundaries clearly Bm.

    Strategy:
      * Most of the time is in D-major content (heavy A and D).
      * Bookend chords (start ~1s and end ~1s) read as Bm via chord
        estimation (B2 + D3 + F#3 stack — bass-heavy enough for the
        chord template matcher to label it Bm).
      * In between, a long D-major section establishes the chroma
        average that K-S uses.
      * V→i cadence (F# → Bm) at the close.

    The rest of the music-theory rationalization writes itself: this is
    a piece in B minor that spends most of its time on the relative
    major (vi → III in B minor terms).
    """
    sf = pytest.importorskip("soundfile")

    # Pitch frequencies (concert pitch). The bass register matters for
    # the chord-estimator's boundary labels (Bm at the start/end), but
    # the time-averaged chroma — which is what K-S sees — gets dominated
    # by whatever pitches we sustain longest. Keep Bm sections short.
    notes = {
        "B2": 123.47,
        "D3": 146.83,
        "F#3": 185.00,
        "A3": 220.00,
        "B3": 246.94,
        "A#3": 233.08,
        "C#4": 277.18,
        "E3": 164.81,
        "G3": 196.00,
        "D4": 293.66,
    }

    def _chord(
        freqs: list[float], dur: float, weights: list[float] | None = None
    ) -> np.ndarray:
        t = np.linspace(0.0, dur, int(sr * dur), endpoint=False)
        if weights is None:
            weights = [1.0] * len(freqs)
        sig = np.zeros_like(t)
        for f, w in zip(freqs, weights):
            sig += w * np.sin(2 * np.pi * f * t)
        return sig / max(sum(weights), 1.0)

    sections = []

    # Bookend opener: Bm (1.0s). Short — we want the chord estimator
    # to see "Bm" but K-S not to overweight B.
    sections.append(
        _chord(
            [notes["B2"], notes["D3"], notes["F#3"]],
            1.0,
            weights=[1.5, 1.0, 1.0],
        )
    )

    # Long D-major-content stretch (5.0s total). This is the chroma-mass
    # section that pushes K-S toward D Ionian. We rotate through D-major
    # diatonic chords with bass A and D dominating — keeps the bass
    # register pointing at A/D, not B. Time-averaging means whichever
    # chord we play longest wins K-S.
    # D major (D-F#-A) for 1.5s with A in bass to lift A-class.
    sections.append(
        _chord(
            [notes["A3"], notes["D4"], notes["F#3"]],
            1.5,
            weights=[2.0, 1.0, 1.0],
        )
    )
    # G major (G-B-D) for 1.0s. G is part of D-major diatonic but adds B.
    sections.append(
        _chord(
            [notes["G3"], notes["D4"], notes["F#3"]],
            1.0,
            weights=[1.5, 1.0, 0.7],
        )
    )
    # A major (A-C#-E) for 1.5s — the V chord of D major, heavy on A.
    sections.append(
        _chord(
            [notes["A3"], notes["C#4"], notes["E3"]],
            1.5,
            weights=[2.0, 1.0, 1.2],
        )
    )
    # D major resolution (1.0s) — D Ionian's I chord.
    sections.append(
        _chord(
            [notes["D3"], notes["F#3"], notes["A3"]],
            1.0,
            weights=[1.5, 1.0, 1.0],
        )
    )

    # F# major (V of B minor) — 1.0s. Cadence setup. F# + A# + C#.
    sections.append(
        _chord(
            [notes["F#3"], notes["A#3"], notes["C#4"]],
            1.0,
            weights=[1.3, 1.0, 1.0],
        )
    )

    # Bm cadence resolution (i in B minor) — 1.0s.
    sections.append(
        _chord(
            [notes["B2"], notes["D3"], notes["F#3"]],
            1.0,
            weights=[1.5, 1.0, 1.0],
        )
    )

    # Bookend closer: Bm again (1.0s).
    sections.append(
        _chord(
            [notes["B2"], notes["D3"], notes["F#3"]],
            1.0,
            weights=[1.5, 1.0, 1.0],
        )
    )

    signal = np.concatenate(sections)
    signal = (signal * 0.45).astype(np.float32)
    sf.write(str(path), signal, sr)
    return path


@pytest.fixture
def bm_diagnostic_wav(tmp_path: Path) -> Path:
    return _generate_bm_diagnostic_wav(tmp_path / "bm_diagnostic.wav")


# ---------------------------------------------------------------------------
# AC-01: default ensemble produces B Aeolian; ks_only produces something
# different (typically D major). The point is the divergence — the ensemble
# is doing real work.
# ---------------------------------------------------------------------------
async def test_default_ensemble_picks_b_aeolian(
    bm_diagnostic_wav: Path,
) -> None:
    """``key_detection="default"`` should pick B Aeolian on the Bm fixture."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(
        bm_diagnostic_wav, quiet=True, key_detection="default"
    )

    assert result.global_key.tonic == "B", (
        f"Expected B (default ensemble disambiguates relative pair), "
        f"got {result.global_key.tonic} {result.global_key.mode}"
    )
    assert (
        "Aeolian" in result.global_key.mode
    ), f"Expected Aeolian mode, got {result.global_key.mode}"


async def test_ks_only_diverges_from_default(
    bm_diagnostic_wav: Path,
) -> None:
    """``ks_only`` must give a DIFFERENT answer from default on this fixture.

    The exact tonic depends on chroma weighting — typically D, sometimes
    F# major or A major. Whatever it is, it must not be B Aeolian (else
    the fixture doesn't exercise the relative-pair problem we're trying
    to test).
    """
    from harmonic_analysis import analyze_audio_async

    ks_result = await analyze_audio_async(
        bm_diagnostic_wav, quiet=True, key_detection="ks_only"
    )
    default_result = await analyze_audio_async(
        bm_diagnostic_wav, quiet=True, key_detection="default"
    )

    # The ks_only verdict and the default verdict must differ —
    # otherwise the ensemble isn't doing any disambiguation work.
    assert (ks_result.global_key.tonic, ks_result.global_key.mode) != (
        default_result.global_key.tonic,
        default_result.global_key.mode,
    ), (
        f"Fixture failed to exercise the ensemble: ks_only and default "
        f"both returned {ks_result.global_key.tonic} {ks_result.global_key.mode}"
    )


async def test_show_analysis_details_populates_payload(
    bm_diagnostic_wav: Path,
) -> None:
    """AC-05: show_analysis_details=True populates structured breakdown."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(
        bm_diagnostic_wav,
        quiet=True,
        key_detection="default",
        show_analysis_details=True,
    )

    details = result.key_analysis_details
    assert details is not None, "key_analysis_details should be populated"
    assert "approaches" in details
    assert "synthesis" in details
    assert "modulations" in details

    # Each approach entry must have name, weight, top_3
    assert len(details["approaches"]) > 0
    for approach in details["approaches"]:
        assert "name" in approach
        assert "weight" in approach
        assert "top_3" in approach
        assert isinstance(approach["top_3"], list)

    # Synthesis dict has the documented keys
    synth = details["synthesis"]
    assert "method" in synth
    assert "winner" in synth
    assert "runner_up" in synth
    assert "margin" in synth
    assert "key_score_table" in synth

    # iteration_01 doesn't ship HMM, so modulations is None
    assert details["modulations"] is None


async def test_show_analysis_details_default_keeps_payload_none(
    bm_diagnostic_wav: Path,
) -> None:
    """AC-06: show_analysis_details defaults to False; payload is None."""
    from harmonic_analysis import analyze_audio_async

    # Explicit False
    res_explicit = await analyze_audio_async(
        bm_diagnostic_wav,
        quiet=True,
        key_detection="default",
        show_analysis_details=False,
    )
    assert res_explicit.key_analysis_details is None

    # Default (omitted)
    res_default = await analyze_audio_async(bm_diagnostic_wav, quiet=True)
    assert res_default.key_analysis_details is None


async def test_ks_only_with_details_shows_single_approach(
    bm_diagnostic_wav: Path,
) -> None:
    """AC-05 corner: ks_only + details on → exactly one approach in the panel."""
    from harmonic_analysis import analyze_audio_async

    result = await analyze_audio_async(
        bm_diagnostic_wav,
        quiet=True,
        key_detection="ks_only",
        show_analysis_details=True,
    )
    assert result.key_analysis_details is not None
    approaches = result.key_analysis_details["approaches"]
    assert len(approaches) == 1
    assert approaches[0]["name"] == "template_correlation"


async def test_invalid_key_detection_preset_raises(
    bm_diagnostic_wav: Path,
) -> None:
    """Unknown preset string should raise ValueError at construction."""
    from harmonic_analysis import analyze_audio_async

    with pytest.raises(ValueError):
        await analyze_audio_async(
            bm_diagnostic_wav, quiet=True, key_detection="nonexistent_preset"
        )
