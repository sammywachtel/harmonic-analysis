#!/usr/bin/env python3
"""Poke the audio adapter from the command line.

Direct library call — no server, no curl. Skips the HTTP layer entirely
so you're testing what `analyze_audio_async` actually returns, not what
the FastAPI serializer made of it.

Usage:
    python scripts/try_audio.py path/to/your.wav
    python scripts/try_audio.py path/to/your.wav --start 0 --end 30
    python scripts/try_audio.py --synth  # generate + analyze /tmp/a_major.wav
    python scripts/try_audio.py path/to/your.wav --json # raw JSON-ish dump

Requires: pip install -e ".[audio]"  (librosa + soundfile)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional


def _make_synth_wav(path: Path, duration: float = 5.0, sr: int = 22050) -> Path:
    """A-major triad: tonic + major third + perfect fifth.

    Three partials, equal weights. Pure 440 Hz alone tilts K-S toward A
    minor about as easily as A major; the C#5 + E5 stack is what makes
    the 'expect tonic == A' assertion robust.
    """
    import numpy as np
    import soundfile as sf

    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    a4 = np.sin(2 * np.pi * 440.00 * t)
    cs5 = np.sin(2 * np.pi * 554.37 * t)
    e5 = np.sin(2 * np.pi * 659.25 * t)
    sig = ((a4 + cs5 + e5) / 3.0 * 0.5).astype("float32")
    sf.write(str(path), sig, sr)
    return path


def _print_human(result) -> None:
    """Render the result as a human-friendly summary, not a JSON dump."""
    g = result.global_key
    loc = result.local_key
    reg = result.region
    cad = result.cadences

    print(f"global key   : {g.tonic} {g.mode}  (conf {g.confidence:.2f})")
    print(f"local key    : {loc.tonic} {loc.mode}  (conf {loc.confidence:.2f})")
    print(f"region       : {reg.type}  (conf {reg.confidence:.2f})")
    if reg.borrowed:
        print(f"borrowed     : {', '.join(reg.borrowed)}")
    print(f"cadence      : detected={cad.detected}  strength={cad.strength:.2f}")
    print(f"segment      : {result.segment_start:.2f}s – {result.segment_end:.2f}s")

    if result.chords:
        print(f"chords       : {len(result.chords)} events")
        # First 10 only — long files can get spammy. If you want the rest
        # use --json and pipe to jq.
        for c in result.chords[:10]:
            flag = "yes" if c.is_diatonic else "no "
            print(
                f"  {c.start_time:6.2f}-{c.end_time:6.2f}s  "
                f"{c.chord_label:8}  conf {c.confidence:.2f}  diatonic {flag}"
            )
        if len(result.chords) > 10:
            print(f"  ... and {len(result.chords) - 10} more")
    else:
        print("chords       : none detected")


def _to_json(result) -> dict:
    """Manual dict construction. asdict() chokes on KeyInfo's frozenset
    field — same trap the route dodges. Don't reach for asdict here."""
    return {
        "global": {
            "tonic": result.global_key.tonic,
            "mode": result.global_key.mode,
            "key_signature": result.global_key.key_signature,
            "confidence": result.global_key.confidence,
        },
        "local": {
            "tonic": result.local_key.tonic,
            "mode": result.local_key.mode,
            "key_signature": result.local_key.key_signature,
            "confidence": result.local_key.confidence,
        },
        "region": {
            "type": result.region.type,
            "confidence": result.region.confidence,
            "borrowed": list(result.region.borrowed),
        },
        "cadence": {
            "detected": result.cadences.detected,
            "strength": result.cadences.strength,
        },
        "segment": {
            "start": result.segment_start,
            "end": result.segment_end,
        },
        "chords": [
            {
                "start_time": c.start_time,
                "end_time": c.end_time,
                "chord_label": c.chord_label,
                "confidence": c.confidence,
                "is_diatonic": c.is_diatonic,
            }
            for c in result.chords
        ],
    }


async def _run(
    filepath: Path,
    start: Optional[float],
    end: Optional[float],
    as_json: bool,
    tonal_bias: float,
    window: float,
    hop: float,
    bass_chroma: bool,
    bass_bonus: float,
) -> int:
    try:
        from harmonic_analysis import analyze_audio_async
    except ImportError as exc:
        print(
            f"error: harmonic_analysis import failed: {exc}\n"
            f'hint:  pip install -e ".[audio]"  from project root',
            file=sys.stderr,
        )
        return 2

    segment = (start, end) if start is not None else None
    result = await analyze_audio_async(
        filepath,
        segment=segment,
        tonal_bias=tonal_bias,
        chord_window_size_s=window,
        chord_hop_size_s=hop,
        use_bass_chroma=bass_chroma,
        bass_bonus=bass_bonus,
    )

    if as_json:
        print(json.dumps(_to_json(result), indent=2))
    else:
        _print_human(result)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the audio adapter against a file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        type=Path,
        help="path to a WAV/FLAC/MP3 file (MP3 needs ffmpeg on PATH)",
    )
    parser.add_argument(
        "--start", type=float, default=None, help="segment start (seconds)"
    )
    parser.add_argument("--end", type=float, default=None, help="segment end (seconds)")
    parser.add_argument(
        "--synth",
        action="store_true",
        help="generate /tmp/a_major.wav and analyze it (no input file needed)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of the human-friendly summary",
    )
    # Chord-layer knobs. Defaults match the library defaults; expose them
    # so you can A/B without editing this file. Common diagnostic moves:
    #   --tonal-bias 0       turn off the tonic-preference nudge entirely
    #   --tonal-bias 0.05    softer bias for songs that pivot to vi often
    #   --window 0.25        smaller window catches faster chord changes
    parser.add_argument(
        "--tonal-bias",
        type=float,
        default=0.15,
        dest="tonal_bias",
        help="tonic preference weight (default 0.15, set 0 to disable)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=0.5,
        help="chord window size in seconds (default 0.5)",
    )
    parser.add_argument(
        "--hop",
        type=float,
        default=0.25,
        help="chord hop size in seconds (default 0.25)",
    )
    # Bass-aware chord estimation. Off by default — opt in to A/B against
    # the existing full-spectrum-only behavior. Disambiguates relative
    # pairs (Bm vs D, Am vs C) when the bass note is the discriminator.
    parser.add_argument(
        "--bass-chroma",
        action="store_true",
        dest="bass_chroma",
        help="enable bass-aware chord estimation (extra chroma pass over bass register)",  # noqa: E501
    )
    parser.add_argument(
        "--bass-bonus",
        type=float,
        default=0.3,
        dest="bass_bonus",
        help="bass-root-match bonus when --bass-chroma is on (default 0.3)",
    )
    args = parser.parse_args()

    if args.synth:
        target = Path("/tmp/a_major.wav")
        try:
            _make_synth_wav(target)
        except ImportError as exc:
            print(
                f"error: numpy/soundfile not available: {exc}\n"
                f'hint:  pip install -e ".[audio]"',
                file=sys.stderr,
            )
            return 2
        if not args.json:
            print(f"(generated synthetic A-major WAV at {target})")
        args.filepath = target

    if args.filepath is None:
        parser.print_usage(sys.stderr)
        print("error: provide a filepath or use --synth", file=sys.stderr)
        return 2

    if not args.filepath.exists():
        print(f"error: no such file: {args.filepath}", file=sys.stderr)
        return 2

    return asyncio.run(
        _run(
            args.filepath,
            args.start,
            args.end,
            args.json,
            args.tonal_bias,
            args.window,
            args.hop,
            args.bass_chroma,
            args.bass_bonus,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
