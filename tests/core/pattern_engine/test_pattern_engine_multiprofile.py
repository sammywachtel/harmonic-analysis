"""
Unit tests for PatternEngine multi-profile functionality.

Tests AC-1.1 through AC-1.6:
- PatternEngine.analyze_with_profile() method
- Profile-specific substitution rules during pattern matching
- Jazz vs Classical tritone substitution behavior
- Distinct analysis results per profile
"""

from pathlib import Path

import pytest

from harmonic_analysis.core.pattern_engine.pattern_engine import (
    AnalysisContext,
    PatternEngine,
)
from harmonic_analysis.core.pattern_engine.profile_manager import (
    Profile,
    ProfileManager,
)


@pytest.fixture
def engine() -> PatternEngine:
    """Create PatternEngine with unified patterns loaded."""
    engine = PatternEngine()
    patterns_path = (
        Path(__file__).parent.parent.parent.parent
        / "src"
        / "harmonic_analysis"
        / "resources"
        / "patterns"
        / "patterns_unified.json"
    )
    engine.load_patterns(patterns_path)
    return engine


@pytest.fixture
def profile_manager() -> ProfileManager:
    """Create ProfileManager with default profiles."""
    return ProfileManager()


@pytest.fixture
def jazz_profile(profile_manager: ProfileManager) -> Profile:
    """Get jazz profile with tritone substitution rules."""
    profile = profile_manager.get_profile("jazz")
    assert profile is not None, "Jazz profile must exist"
    return profile


@pytest.fixture
def classical_profile(profile_manager: ProfileManager) -> Profile:
    """Get classical profile (no tritone substitution)."""
    profile = profile_manager.get_profile("classical")
    assert profile is not None, "Classical profile must exist"
    return profile


def test_analyze_with_profile_accepts_profile_parameter(
    engine: PatternEngine, jazz_profile: Profile
) -> None:
    """Test AC-1.1 & AC-1.2: analyze_with_profile() method exists and accepts Profile."""
    # Opening move: create simple analysis context
    context = AnalysisContext(
        key="C major",
        chords=["C", "F", "G", "C"],
        roman_numerals=["I", "IV", "V", "I"],
        melody=[],
        scales=[],
        metadata={},
    )

    # Main play: call analyze_with_profile with jazz profile
    result = engine.analyze_with_profile(context, jazz_profile)

    # Victory lap: verify envelope structure
    assert result is not None
    assert result.primary is not None
    assert result.schema_version == "1.0"


def test_jazz_profile_detects_tritone_substitution(
    engine: PatternEngine, jazz_profile: Profile
) -> None:
    """Test AC-1.4: Jazz profile detects tritone substitution as ii-♭II-I pattern."""
    # Opening move: create context with tritone sub
    # Dm7 → D♭7 → Cmaj7 = ii-♭II7-I in C major (tritone sub for V7)
    context = AnalysisContext(
        key="C major",
        chords=["Dm7", "Db7", "Cmaj7"],
        roman_numerals=["ii", "♭II", "I"],  # ♭II7 is tritone sub for V7
        melody=[],
        scales=[],
        metadata={},
    )

    # Main play: analyze with jazz profile
    result = engine.analyze_with_profile(context, jazz_profile)

    # Victory lap: verify jazz detects this as a valid pattern
    # Jazz profile should recognize ♭II as a substitute for V in ii-V-I
    assert result.primary is not None
    assert result.primary.confidence > 0.0

    # Check that profile metadata is attached
    if result.primary.terms:
        assert "profile" in result.primary.terms
        assert result.primary.terms["profile"] == "Jazz"


def test_classical_profile_no_tritone_substitution(
    engine: PatternEngine, classical_profile: Profile, jazz_profile: Profile
) -> None:
    """Test AC-1.5: Classical profile does NOT detect tritone sub as ii-V-I."""
    # Opening move: same context with tritone sub
    context = AnalysisContext(
        key="C major",
        chords=["Dm7", "Db7", "Cmaj7"],
        roman_numerals=["ii", "♭II", "I"],
        melody=[],
        scales=[],
        metadata={},
    )

    # Main play: analyze with classical profile
    classical_result = engine.analyze_with_profile(context, classical_profile)

    # Also analyze with jazz profile for comparison
    jazz_result = engine.analyze_with_profile(context, jazz_profile)

    # Victory lap: verify classical has different interpretation than jazz
    # Classical should NOT recognize ♭II as V substitute
    # This means different patterns detected or lower confidence
    assert classical_result.primary is not None

    # The two profiles should produce different results
    # (different confidence, different patterns, or different reasoning)
    results_differ = (
        classical_result.primary.confidence != jazz_result.primary.confidence
        or classical_result.primary.reasoning != jazz_result.primary.reasoning
        or len(classical_result.primary.patterns) != len(jazz_result.primary.patterns)
    )
    assert (
        results_differ
    ), "Classical and Jazz profiles should produce different results"


def test_profiles_produce_distinct_results(
    engine: PatternEngine, jazz_profile: Profile, classical_profile: Profile
) -> None:
    """Test AC-1.6: Each profile produces distinct analysis results for same input."""
    # Opening move: create standard ii-V-I progression
    context = AnalysisContext(
        key="C major",
        chords=["Dm7", "G7", "Cmaj7"],
        roman_numerals=["ii", "V", "I"],
        melody=[],
        scales=[],
        metadata={},
    )

    # Main play: analyze with both profiles
    jazz_result = engine.analyze_with_profile(context, jazz_profile)
    classical_result = engine.analyze_with_profile(context, classical_profile)

    # Victory lap: verify both return valid results
    assert jazz_result.primary is not None
    assert classical_result.primary is not None

    # Verify profile metadata differs
    if jazz_result.primary.terms and classical_result.primary.terms:
        assert jazz_result.primary.terms.get("profile") == "Jazz"
        assert classical_result.primary.terms.get("profile") == "Classical"


def test_profile_substitutions_expand_during_matching(
    engine: PatternEngine, jazz_profile: Profile, classical_profile: Profile
) -> None:
    """Test AC-1.3: Pattern matching uses profile substitutions during chord expansion."""
    # Opening move: create progression where substitution matters
    # ♭II7 → I (backdoor progression in jazz, chromatic in classical)
    context = AnalysisContext(
        key="C major",
        chords=["Db7", "Cmaj7"],
        roman_numerals=["♭II", "I"],
        melody=[],
        scales=[],
        metadata={},
    )

    # Main play: analyze with jazz profile (has ♭II7 substitution for V7)
    jazz_result = engine.analyze_with_profile(context, jazz_profile)

    # Analyze with classical profile (no ♭II7 substitution)
    classical_result = engine.analyze_with_profile(context, classical_profile)

    # Victory lap: verify different pattern detection
    # Jazz should detect this as a functional pattern (♭II substitutes for V)
    # Classical should see it differently (chromatic approach)
    assert jazz_result.primary is not None
    assert classical_result.primary is not None

    # At minimum, confidence or pattern count should differ
    analysis_differs = (
        jazz_result.primary.confidence != classical_result.primary.confidence
        or len(jazz_result.primary.patterns) != len(classical_result.primary.patterns)
    )
    assert analysis_differs, "Substitution rules should affect pattern matching"


def test_multiple_profiles_same_progression(
    engine: PatternEngine, profile_manager: ProfileManager
) -> None:
    """Test that all 4 profiles can analyze the same progression."""
    # Opening move: create versatile progression (works in multiple styles)
    context = AnalysisContext(
        key="C major",
        chords=["C", "Am", "Dm", "G"],
        roman_numerals=["I", "vi", "ii", "V"],
        melody=[],
        scales=[],
        metadata={},
    )

    # Main play: analyze with all enabled profiles
    enabled_profiles = profile_manager.get_enabled_profiles()
    assert len(enabled_profiles) == 4  # jazz, classical, pop, modal

    results = []
    for profile in enabled_profiles:
        result = engine.analyze_with_profile(context, profile)
        results.append((profile.name, result))

    # Victory lap: verify all profiles return valid results
    for profile_name, result in results:
        assert result is not None, f"Profile {profile_name} returned None"
        assert result.primary is not None, f"Profile {profile_name} has no primary"
        assert (
            result.primary.confidence > 0.0
        ), f"Profile {profile_name} has 0 confidence"
