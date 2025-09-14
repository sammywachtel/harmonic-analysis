def _norm_text(s: str) -> str:
    """Normalize text for robust name/alias matching.
    - lowercases
    - converts Unicode dashes to ASCII '-'
    - converts flats/sharps to b/#
    - normalizes Unicode superscripts 0-9 to ASCII
    - collapses multiple spaces and strips
    """
    if not s:
        return ""
    s = s.lower()
    # unify dashes (en, em, minus) to hyphen
    for ch in ("–", "—", "−", "‒", "―"):
        s = s.replace(ch, "-")
    # unify flats/sharps
    s = s.replace("♭", "b").replace("♯", "#")
    # superscripts → ascii
    supers = {
        "⁰": "0",
        "¹": "1",
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
    }
    for k, v in supers.items():
        s = s.replace(k, v)
    # collapse spaces
    s = " ".join(s.split())
    return s


import json  # noqa: E402
import pathlib  # noqa: E402
import sys  # noqa: E402

import pytest  # noqa: E402

# Ensure project root on sys.path (from pattern_engine subdirectory)
ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harmonic_analysis.services.pattern_analysis_service import (  # noqa: E402
    PatternAnalysisService,
)

DATA_PATH = ROOT / "tests" / "data" / "pattern_tests.json"


def _load_tests():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    aliases = {
        _norm_text(k): [_norm_text(a) for a in v]
        for k, v in data.get("aliases", {}).items()
    }
    tests = data.get("tests", [])
    return aliases, tests


ALIASES, TESTS = _load_tests()


def _found_sets(analysis):
    """Lowercased sets of pattern names and families from the engine result."""
    names = [_norm_text(m.get("name", "")) for m in analysis.get("pattern_matches", [])]
    fams = [
        _norm_text(m.get("family", "")) for m in analysis.get("pattern_matches", [])
    ]
    return set(names), set(fams)


def _found_sets_from_envelope(envelope):
    """Lowercased sets of pattern names and families from AnalysisEnvelope DTO."""
    patterns = envelope.primary.patterns
    names = [_norm_text(p.name) for p in patterns]
    fams = [_norm_text(p.family) for p in patterns]
    return set(names), set(fams)


def _name_has(needle, names):
    """True if name or any alias substring appears in names."""
    needle = _norm_text(needle)
    if any(needle in _norm_text(n) for n in names):
        return True
    for alias in ALIASES.get(needle, []):
        if any(alias in _norm_text(n) for n in names):
            return True
    return False


def _fam_has(needle, fams):
    needle = needle.lower()
    return any(needle in f for f in fams)


def _pattern_found(expected, names, fams):
    e = expected.lower()
    # 1) exact or alias name hit
    if _name_has(e, names):
        return True

    # 2) sensible family fallbacks (broad patterns only)
    # Macros that commonly appear under jazz_pop/sequence families
    if e in ("vi-iv-i-v", "ii-v-i"):
        return _fam_has("jazz_pop", fams) or _fam_has("sequence", fams)
    # Classical cadence umbrella
    if e in ("pac", "iac", "half_cadence", "phrygian"):
        return _fam_has("cadence", fams)
    # Schemata umbrella
    if e == "pachelbel":
        return _fam_has("schema", fams)

    # 3) Require explicit name/alias (no generic family fallback)
    if e in ("andalusian", "backdoor"):
        return False

    return False


@pytest.mark.parametrize("case", TESTS, ids=[c["name"] for c in TESTS])
def test_patterns_from_json(case):
    svc = PatternAnalysisService()

    chords = case["chords"]
    profile = case.get("profile", "classical")
    best_cover = case.get(
        "best_cover", False
    )  # existence-based by default for validation

    # Run analysis (optionally hint/lock key if available)
    key_hint = case.get("key_hint") or case.get("expected_key")
    if key_hint:
        print(f"[tests] key_hint requested: {key_hint}")

    analysis = svc.analyze_with_patterns(
        chords, profile=profile, best_cover=best_cover, key_hint=key_hint
    )

    found_names, found_fams = _found_sets_from_envelope(analysis)

    # Pass if ANY expected pattern is found (name/alias/family-aware)
    expected_list = case.get("expected_patterns", [])
    pattern_found = any(
        _pattern_found(e, found_names, found_fams) for e in expected_list
    )

    # If this is an 'expected failure until implemented', assert the inverse for now
    if case.get("xfail_until_implemented"):
        if pattern_found:
            pytest.fail(
                f"'{case['name']}' unexpectedly passed (remove xfail flag). Found: {sorted(found_names)}"
            )
        pytest.xfail(f"'{case['name']}' not implemented yet")
    else:
        assert pattern_found, (
            f"Expected one of {expected_list} but saw names={sorted(found_names)}, "
            f"families={sorted(found_fams)} for chords={chords} (profile={profile})"
        )
