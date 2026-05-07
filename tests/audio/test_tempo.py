"""Tests for tempo detection and BPM-to-rubato mapping.

Variable-tempo behavior is exercised end-to-end via the audio adapter
in test_audio_adapter.py; these tests cover the standalone helpers.
"""

from __future__ import annotations

import numpy as np
import pytest

# Module-level skip — ``_tempo`` transitively imports librosa, so the whole
# module fails to COLLECT (not just skip) on environments without the audio
# extras installed (the CI Backend Quality job is one). Same pattern used
# by tests/audio/test_chord_estimation.py.
librosa = pytest.importorskip("librosa")

from harmonic_analysis.audio._tempo import (  # noqa: E402
    TempoRegion,
    _segment_tempo,
    bpm_to_rubato,
)


class TestBpmToRubato:
    """``bpm_to_rubato`` maps detected BPM to (window, hop, kernel)."""

    def test_low_confidence_falls_back_to_loose(self):
        """Confidence below threshold ignores BPM and returns the loose
        preset (0.75s window, 5-frame kernel).

        Material that defeats BPM detection — pop with electronic onsets,
        heavy reverb, free-tempo classical — is exactly what produces the
        most chord fragmentation under moderate's 0.5s window. Loose
        absorbs the ambiguity; callers who want tight grids can pass a
        static preset explicitly.
        """
        # 60 BPM but unreliable — fall back to loose defaults.
        w, h, k = bpm_to_rubato(60.0, confidence=0.1)
        assert (w, h, k) == (0.75, 0.4, 5)

    def test_zero_bpm_falls_back_to_loose(self):
        """Sentinel BPM=0 means detection failed; use loose."""
        w, h, k = bpm_to_rubato(0.0, confidence=1.0)
        assert (w, h, k) == (0.75, 0.4, 5)

    def test_classical_tempo_clamps_at_ceiling(self):
        """At ~70 BPM, raw 2-beat window would be ~1.7s but is capped to 1.0s.

        The cap exists because piano music in this tempo range often has
        chord-per-beat harmonic rhythm, and a 1.7s window over-smooths
        the brief dominant chords that key detection relies on. See the
        bpm_to_rubato docstring for the iwasonce regression that
        motivated this.
        """
        w, h, k = bpm_to_rubato(70.0, confidence=0.8)
        assert w == 1.0
        assert h == 0.5
        assert k == 5

    def test_pop_tempo_gives_full_one_second_window(self):
        """At 120 BPM, the 2-beat window is exactly 1.0s — at the cap."""
        w, h, k = bpm_to_rubato(120.0, confidence=0.8)
        assert w == pytest.approx(1.0, rel=0.01)
        assert h == pytest.approx(0.5, rel=0.01)
        assert k == 5

    def test_fast_tempo_below_cap(self):
        """At 132 BPM (Bach), 2-beat window is 0.91s — below the cap."""
        w, h, k = bpm_to_rubato(132.0, confidence=0.8)
        assert w == pytest.approx(0.909, rel=0.01)
        assert h == pytest.approx(0.455, rel=0.01)
        assert k == 5

    def test_very_fast_tempo_clamped_at_minimum(self):
        """Above ~300 BPM the window would go below 0.4s; clamp it."""
        w, h, k = bpm_to_rubato(400.0, confidence=0.8)
        assert w == 0.4
        assert h == 0.2
        assert k == 3  # below 0.7s threshold → narrow kernel

    def test_very_slow_tempo_clamped_at_ceiling(self):
        """Below ~120 BPM the 2-beat window exceeds 1.0s; cap to 1.0s."""
        w, h, k = bpm_to_rubato(40.0, confidence=0.8)
        assert w == 1.0
        assert h == 0.5
        assert k == 5


class TestSegmentTempo:
    """``_segment_tempo`` splits per-frame BPM into constant-tempo regions."""

    SR = 22050  # matches the audio module default

    def test_constant_tempo_one_region(self):
        """A constant 120-BPM curve produces a single region."""
        tempo = np.full(800, 120.0)
        regions = _segment_tempo(
            tempo, sr=self.SR, segment_start=0.0, change_threshold=0.20
        )
        assert len(regions) == 1
        assert regions[0].bpm == pytest.approx(120.0)
        assert regions[0].confidence > 0.99

    def test_two_distinct_tempos_split_correctly(self):
        """A 60-BPM half followed by a 120-BPM half produces two regions."""
        # 800 frames total, split halfway. fps ~ 43, so each half is ~9s.
        tempo = np.concatenate([np.full(400, 60.0), np.full(400, 120.0)])
        regions = _segment_tempo(
            tempo, sr=self.SR, segment_start=0.0, change_threshold=0.20
        )
        assert len(regions) == 2
        assert regions[0].bpm == pytest.approx(60.0)
        assert regions[1].bpm == pytest.approx(120.0)
        # Boundary is at frame 400 → time 400 * (512/22050) ≈ 9.29s
        boundary = regions[0].end_time
        assert 8.5 < boundary < 10.0

    def test_wobble_within_threshold_stays_one_region(self):
        """Per-frame jitter under the change threshold doesn't split."""
        # Mostly 100 BPM, some frames at 110 (10% wobble — under 20%).
        rng = np.random.default_rng(42)
        tempo = 100.0 + rng.uniform(-10, 10, 800)
        regions = _segment_tempo(
            tempo, sr=self.SR, segment_start=0.0, change_threshold=0.20
        )
        assert (
            len(regions) == 1
        ), f"Expected 1 region for sub-threshold wobble, got {len(regions)}"

    def test_single_outlier_does_not_create_region(self):
        """One spike frame in an otherwise-stable curve doesn't create a new region.

        This is the bug the third-pass mean-merge fixes: pass 1 starts a
        new region on any frame > threshold from the running mean, but a
        single outlier frame followed by similar-mean frames shouldn't
        produce two regions with similar means.
        """
        tempo = np.full(800, 100.0)
        tempo[400] = 200.0  # one wild outlier frame (100% deviation)
        regions = _segment_tempo(
            tempo, sr=self.SR, segment_start=0.0, change_threshold=0.20
        )
        # The third-pass merge should collapse any same-mean neighbors
        # back into one region — we should NOT see two regions both
        # at ~100 BPM.
        means = [r.bpm for r in regions]
        assert all(
            abs(m - 100.0) < 5 for m in means
        ), f"All region means should be ~100 BPM, got {means}"
        # And the regions that survived shouldn't all have the same mean
        # (that's the exact case the merge guards against).
        if len(regions) > 1:
            unique_means = set(round(r.bpm, 1) for r in regions)
            assert (
                len(unique_means) > 1
            ), f"Multiple regions all near 100 BPM — merge failed: {means}"

    def test_segment_start_offsets_region_times(self):
        """``segment_start`` shifts all region times into file time."""
        tempo = np.full(400, 120.0)
        regions = _segment_tempo(
            tempo, sr=self.SR, segment_start=10.0, change_threshold=0.20
        )
        assert len(regions) == 1
        assert regions[0].start_time == pytest.approx(10.0)
        # End is 10.0 + 400 * (512/22050) ≈ 10 + 9.29 = 19.29
        assert 18.5 < regions[0].end_time < 20.0


class TestTempoRegion:
    """``TempoRegion`` is a frozen dataclass; sanity-check the contract."""

    def test_frozen(self):
        r = TempoRegion(start_time=0.0, end_time=10.0, bpm=120.0, confidence=0.9)
        with pytest.raises((AttributeError, Exception)):
            r.bpm = 60.0  # type: ignore[misc]

    def test_fields_round_trip(self):
        r = TempoRegion(start_time=1.5, end_time=10.0, bpm=85.5, confidence=0.7)
        assert r.start_time == 1.5
        assert r.end_time == 10.0
        assert r.bpm == 85.5
        assert r.confidence == 0.7
