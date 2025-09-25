import pytest

from harmonic_analysis.api.analysis import analyze_melody, analyze_scale


@pytest.mark.asyncio
async def test_analyze_scale_requires_key():
    with pytest.raises(ValueError, match="requires a key"):
        await analyze_scale(["C", "D", "E", "F", "G", "A", "B"], key=None)


@pytest.mark.asyncio
async def test_analyze_melody_requires_key():
    with pytest.raises(ValueError, match="requires a key"):
        await analyze_melody(["C4", "E4", "G4"], key=None)
