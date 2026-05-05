"""Regression test: the documented toolkit wrapper recipe must actually work.

Reads docs/how-to/audio-analysis.md, extracts the sentinel-tagged code fence,
runs it against a synthetic WAV, and asserts the result has all ModeAnalysisResponse
required fields. The doc IS the test fixture — no copy-paste duplication.
"""

import textwrap
from pathlib import Path

import numpy as np
import pytest

librosa = pytest.importorskip("librosa")
sf = pytest.importorskip("soundfile")


# Path to the how-to doc (the test fixture)
HOWTO_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "how-to" / "audio-analysis.md"
)

SENTINEL_START = "# toolkit-wrapper-recipe-start"
SENTINEL_END = "# toolkit-wrapper-recipe-end"


def _extract_recipe(howto_path: Path) -> str:
    """Parse the markdown, find the sentinel-tagged fence, return the code."""
    text = howto_path.read_text()
    lines = text.splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == SENTINEL_START:
            start_idx = i
        elif stripped == SENTINEL_END:
            end_idx = i
            break
    assert start_idx is not None, f"Sentinel start not found in {howto_path}"
    assert end_idx is not None, f"Sentinel end not found in {howto_path}"
    recipe_lines = lines[start_idx + 1 : end_idx]
    return textwrap.dedent("\n".join(recipe_lines))


def _make_synthetic_wav(path: Path, duration: float = 2.0, sr: int = 22050) -> None:
    """Generate a sine-wave WAV. Not music, but enough to exercise the pipeline."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # A4 = 440 Hz — recognizable enough for key estimation to latch onto something
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(str(path), signal, sr)


@pytest.mark.asyncio
async def test_toolkit_wrapper_recipe_produces_valid_result(tmp_path):
    """The documented recipe must produce a dict with all ModeAnalysisResponse fields."""
    # Generate synthetic WAV
    wav_path = tmp_path / "test_tone.wav"
    _make_synthetic_wav(wav_path)

    # Extract recipe from the doc — the doc is the single source of truth,
    # so if the recipe drifts from what the test expects, we find out here
    # instead of in production.
    recipe_code = _extract_recipe(HOWTO_PATH)

    # Run the recipe in a controlled namespace. We use compile+exec because
    # the recipe defines an async function (run_wrapper) that we then call.
    # This is NOT the same as running arbitrary user input — the source is
    # our own checked-in documentation file.
    namespace = {"audio_path": str(wav_path)}
    compiled = compile(recipe_code, "<toolkit-wrapper-recipe>", "exec")
    # Safe: source is our own docs/how-to/audio-analysis.md, not user input
    exec(compiled, namespace)  # noqa: S102

    # The recipe must define an async function we can call. Since exec can't
    # await top-level async code, the recipe defines
    # `async def run_wrapper(audio_path)` that returns result_dict.
    assert "run_wrapper" in namespace, (
        "Recipe must define 'async def run_wrapper(audio_path)' "
        "that returns a ModeAnalysisResponse-shaped dict"
    )
    result_dict = await namespace["run_wrapper"](str(wav_path))

    # Assert all ModeAnalysisResponse required fields
    assert isinstance(result_dict["global"]["tonic"], str)
    assert isinstance(result_dict["global"]["mode"], str)
    assert isinstance(result_dict["local"]["region_type"], str)
    assert isinstance(result_dict["analysis"]["borrowed_tones"], list)
    assert isinstance(result_dict["analysis"]["cadence_detected"], bool)

    # chromagram_summary: list of exactly 12 floats
    chroma = result_dict["analysis"]["chromagram_summary"]
    assert isinstance(chroma, list)
    assert len(chroma) == 12
    assert all(isinstance(v, float) for v in chroma)

    # visuals: list (may be empty)
    assert isinstance(result_dict["visuals"], list)
