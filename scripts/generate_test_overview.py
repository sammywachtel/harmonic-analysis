#!/usr/bin/env python3
"""Generate a pedagogical view of harmonic-analysis test scenarios.

For every fixture-based test case we can find, this script writes one entry
showing input, source attribution, expected output, what the analyzer
actually produced, and which cadences/patterns fired (with explanations).

It's meant to be re-run as the suite grows — add a new `*.oracle.json` file
under tests/fixtures/progressions/ or a DCML-derived fixture, and the next
run picks it up automatically.

Output: docs/explanation/test-overview.md (Diátaxis: understanding-oriented).
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from harmonic_analysis.core.pattern_engine.glossary_provider import (  # noqa: E402
    GlossaryProvider,
)
from harmonic_analysis.services.pattern_analysis_service import (  # noqa: E402
    PatternAnalysisService,
)

# Modal labels that are equivalent to functional minor/major keys.
# When a fixture says "A aeolian" and the analyzer says "A minor", that's
# a convention difference (Aeolian = natural minor), not a real disagreement.
MODE_TO_KEY_EQUIV = {
    "aeolian": "minor",
    "ionian": "major",
}


def _normalize_key_for_compare(key: Optional[str]) -> Optional[str]:
    """Map modal labels to their functional equivalents for comparison."""
    if not key:
        return key
    parts = key.strip().split()
    if len(parts) == 2 and parts[1].lower() in MODE_TO_KEY_EQUIV:
        return f"{parts[0]} {MODE_TO_KEY_EQUIV[parts[1].lower()]}"
    return key


def _resolve_alias_to_patterns(alias: str, alias_map: dict) -> list[str]:
    """pattern_tests.json uses aliases like 'pac' or 'vi-iv-i-v'. The
    alias map provides synonyms; for the verdict we keep the alias and
    just check substring against actual pattern ids."""
    return alias_map.get(alias, [alias])


# ---------------------------------------------------------------------------
# Common scenario shape
# ---------------------------------------------------------------------------


@dataclass
class TestScenario:
    """Unified shape across heterogeneous fixture schemas."""

    name: str
    source_file: str  # display path like "tests/fixtures/progressions/foo.json"
    source_kind: str  # "oracle" | "golden" | "pattern-test" | "dcml"
    attribution: str = ""  # provenance from the fixture (composer, piece, mm.)

    # Inputs (chord symbols are what callers actually send today; romans
    # would only show up for fixtures that test the romans→chords path)
    input_chords: Optional[list[str]] = None
    input_romans: Optional[list[str]] = None
    profile: str = "classical"
    key_hint: Optional[str] = None

    # Expectations (whichever the fixture spells out)
    expected_key: Optional[str] = None
    expected_romans: Optional[list[str]] = None
    expected_mode: Optional[str] = None
    forbidden_modes: list[str] = field(default_factory=list)
    expected_patterns: list[str] = field(default_factory=list)  # pattern ids/aliases

    # Free-text rationale (the music-theory comment from the fixture)
    rationale: str = ""


# ---------------------------------------------------------------------------
# Loaders — one per known fixture schema
# ---------------------------------------------------------------------------


def _rel(p: Path) -> str:
    """Display path relative to repo root."""
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def load_oracle_fixtures() -> list[TestScenario]:
    """Hand-curated oracle files: tests/fixtures/progressions/*.oracle.json."""
    out: list[TestScenario] = []
    for path in sorted(
        (REPO_ROOT / "tests" / "fixtures" / "progressions").glob("*.oracle.json")
    ):
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data.get("progressions", []):
            out.append(
                TestScenario(
                    name=case["name"],
                    source_file=_rel(path),
                    source_kind="oracle",
                    # Oracle files don't have separate attribution — the
                    # rationale comment usually says where the case came from.
                    attribution="hand-curated (see rationale)",
                    input_chords=case.get("chords"),
                    profile="classical",
                    key_hint=case.get("key_hint"),
                    expected_key=case.get("key"),
                    expected_romans=case.get("roman_numerals"),
                    expected_mode=case.get("mode_expected"),
                    forbidden_modes=list(case.get("mode_must_not_be") or []),
                    rationale=case.get("comment", ""),
                )
            )
    return out


def load_golden_fixtures() -> list[TestScenario]:
    """Pattern-matching golden files: tests/fixtures/progressions/*.golden.json.

    These are wired up via tests/patterns/test_golden_patterns.py; their
    `expected_matches` block carries pattern IDs we can list as cadence
    expectations.
    """
    out: list[TestScenario] = []
    for path in sorted(
        (REPO_ROOT / "tests" / "fixtures" / "progressions").glob("*.golden.json")
    ):
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data.get("progressions", []):
            patterns = [m["pattern_id"] for m in case.get("expected_matches", [])]
            out.append(
                TestScenario(
                    name=case["name"],
                    source_file=_rel(path),
                    source_kind="golden",
                    attribution="hand-curated golden fixture",
                    input_chords=case.get("chords"),
                    profile=case.get("profile", "classical"),
                    expected_key=case.get("key"),
                    expected_romans=case.get("roman_numerals"),
                    expected_patterns=patterns,
                )
            )
    return out


def load_pattern_tests() -> list[TestScenario]:
    """tests/data/pattern_tests.json — pattern alias tests with profiles."""
    path = REPO_ROOT / "tests" / "data" / "pattern_tests.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[TestScenario] = []
    for case in data.get("tests", []):
        out.append(
            TestScenario(
                name=case["name"],
                source_file=_rel(path),
                source_kind="pattern-test",
                attribution="hand-curated alias test",
                input_chords=case.get("chords"),
                profile=case.get("profile", "classical"),
                expected_key=case.get("expected_key"),
                expected_patterns=list(case.get("expected_patterns", [])),
            )
        )
    return out


def load_dcml_fixtures() -> list[TestScenario]:
    """Future hook: DCML-derived oracle fixtures.

    Will live at tests/data/oracles/abc/*.oracle.json once task #4 lands.
    Each case carries source_movement / source_measures / source_commit
    fields which we'll surface as attribution.
    """
    out: list[TestScenario] = []
    abc_dir = REPO_ROOT / "tests" / "data" / "oracles" / "abc"
    if not abc_dir.exists():
        return out
    for path in sorted(abc_dir.glob("*.oracle.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data.get("progressions", []):
            mvt = case.get("source_movement", "")
            mm = case.get("source_measures", "")
            sha = case.get("source_commit", "")
            attribution = f"DCML ABC {mvt}".strip()
            if mm:
                attribution += f" mm. {mm}"
            if sha:
                attribution += f" (commit {sha[:8]})"
            out.append(
                TestScenario(
                    name=case["name"],
                    source_file=_rel(path),
                    source_kind="dcml",
                    attribution=attribution,
                    input_chords=case.get("chords"),
                    profile="classical",
                    key_hint=case.get("key_hint", case.get("key")),
                    expected_key=case.get("key"),
                    expected_romans=case.get("roman_numerals"),
                    rationale=case.get("comment", ""),
                )
            )
    return out


# ---------------------------------------------------------------------------
# Run analyzer + collect actuals
# ---------------------------------------------------------------------------


@dataclass
class AnalyzerOutput:
    key: Optional[str] = None
    mode: Optional[str] = None
    romans: list[str] = field(default_factory=list)
    confidence: float = 0.0
    patterns: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


async def run_one(
    service: PatternAnalysisService,
    glossary: GlossaryProvider,
    sc: TestScenario,
) -> AnalyzerOutput:
    if not sc.input_chords:
        return AnalyzerOutput(error="no input_chords (skipped)")
    try:
        result = await service.analyze_with_patterns_async(
            sc.input_chords,
            profile=sc.profile,
            key_hint=sc.key_hint,
        )
    except Exception as exc:  # noqa: BLE001
        return AnalyzerOutput(error=f"{type(exc).__name__}: {exc}")
    primary = result.primary
    patterns = []
    for pm in primary.patterns:
        patterns.append(
            {
                "id": pm.pattern_id,
                "name": pm.name,
                "family": pm.family,
                "span": (pm.start, pm.end),
                "score": pm.score,
                "cadence_role": pm.cadence_role,
                "explanation": _explain_pattern(pm, glossary),
            }
        )
    return AnalyzerOutput(
        key=primary.key_signature,
        mode=primary.mode,
        romans=list(primary.roman_numerals),
        confidence=primary.confidence,
        patterns=patterns,
    )


def _explain_pattern(pm, glossary: GlossaryProvider) -> str:
    """Extract a short pedagogical blurb. Prefer the pattern's attached
    glossary; fall back to looking up by name; truncate to keep the
    rendered table compact."""
    # Prefer attached glossary if the analyzer populated it
    if pm.glossary:
        for key in ("summary", "short_description", "description", "definition"):
            val = pm.glossary.get(key)
            if val:
                return _truncate(val)
    # Fall back: cadence explanation by pattern name (works for "PAC...", etc.)
    cad = glossary.get_cadence_explanation(pm.name)
    if cad:
        for key in ("summary", "short_description", "description", "definition"):
            val = cad.get(key)
            if val:
                return _truncate(val)
    # Last resort: a term lookup on family or name
    for term in (pm.family, pm.name, pm.pattern_id):
        if not term:
            continue
        defn = glossary.get_term_definition(term)
        if defn:
            return _truncate(defn)
    return ""


def _truncate(text: str, n: int = 240) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= n else text[:n].rstrip() + "…"


async def run_all(scenarios: list[TestScenario]) -> list[AnalyzerOutput]:
    service = PatternAnalysisService()
    glossary = GlossaryProvider()
    return [await run_one(service, glossary, sc) for sc in scenarios]


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------


def verdict(sc: TestScenario, out: AnalyzerOutput) -> tuple[str, list[str]]:
    """Soft verdict: EXACT | DIFFERS | N/A.

    Pedagogical view, not graded. The actual test suite has its own verdict
    (and may be strictly stricter — e.g., test_minor_key_oracle.py asserts
    exact roman match without normalizing modal labels). Differences here
    are surfaced for the reader to interpret, not flagged as bugs.
    """
    if out.error:
        return ("N/A", [out.error])
    issues: list[str] = []
    if sc.expected_key:
        # Treat "X aeolian" / "X minor" as equivalent for comparison
        # (likewise "X ionian" / "X major"); see MODE_TO_KEY_EQUIV.
        if _normalize_key_for_compare(out.key) != _normalize_key_for_compare(
            sc.expected_key
        ):
            issues.append(
                f"key: fixture says {sc.expected_key!r}, " f"analyzer says {out.key!r}"
            )
    if sc.expected_romans is not None and out.romans != sc.expected_romans:
        issues.append("romans: see side-by-side diff")
    if sc.expected_mode is not None and out.mode != sc.expected_mode:
        issues.append(
            f"mode: fixture says {sc.expected_mode!r}, " f"analyzer says {out.mode!r}"
        )
    if sc.forbidden_modes and out.mode in sc.forbidden_modes:
        issues.append(f"mode: {out.mode!r} is in forbidden list")
    if sc.expected_patterns:
        # Golden fixtures' expected_patterns reference internal pattern IDs
        # that test_golden_patterns.py checks via the LOW-LEVEL matcher
        # (engine._find_pattern_matches). The analyzer's high-level result
        # may filter/arbitrate patterns, so an "expected pattern not in
        # actual" here doesn't mean the pattern engine missed it — only
        # that it didn't surface in the chosen interpretation. We surface
        # the difference but tag it as informational.
        actual_ids = {p["id"] for p in out.patterns}
        missing = [
            pid
            for pid in sc.expected_patterns
            if not any(pid in aid or aid in pid for aid in actual_ids)
        ]
        if missing:
            issues.append(
                f"expected patterns not in primary interpretation: {missing} "
                "(may still be detected by lower-level matchers — "
                "see test_golden_patterns.py for the authoritative test)"
            )
    return ("EXACT" if not issues else "DIFFERS", issues)


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def render_summary(rows: list[tuple[TestScenario, AnalyzerOutput]]) -> str:
    by_source: dict[str, dict[str, int]] = {}
    for sc, out in rows:
        bucket = by_source.setdefault(
            sc.source_file,
            {"total": 0, "exact": 0, "differs": 0, "na": 0},
        )
        bucket["total"] += 1
        v, _ = verdict(sc, out)
        if v == "EXACT":
            bucket["exact"] += 1
        elif v == "DIFFERS":
            bucket["differs"] += 1
        else:
            bucket["na"] += 1
    lines = [
        "| Source file | Cases | Exact | Differs | N/A |",
        "|---|---:|---:|---:|---:|",
    ]
    for src in sorted(by_source):
        b = by_source[src]
        lines.append(
            f"| `{src}` | {b['total']} | {b['exact']} | "
            f"{b['differs']} | {b['na']} |"
        )
    return "\n".join(lines)


def _diff_romans(expected: list[str], actual: list[str]) -> str:
    """Side-by-side roman numeral comparison as a markdown table."""
    if expected == actual:
        return ""
    lines = ["| pos | expected | actual |", "|---:|---|---|"]
    width = max(len(expected), len(actual))
    for i in range(width):
        e = expected[i] if i < len(expected) else "—"
        a = actual[i] if i < len(actual) else "—"
        marker = " " if e == a else " ← differs"
        lines.append(f"| {i} | `{e}` | `{a}`{marker} |")
    return "\n".join(lines)


def render_case(sc: TestScenario, out: AnalyzerOutput) -> str:
    v, issues = verdict(sc, out)
    badge = {
        "EXACT": "✅ exact",
        "DIFFERS": "🟡 differs",
        "N/A": "⚠️ N/A",
    }[v]

    blocks: list[str] = []
    blocks.append(f"#### `{sc.name}` — {badge}")

    blocks.append(f"**Source:** {sc.attribution}")
    if sc.key_hint:
        blocks.append(f"**Key hint passed to analyzer:** `{sc.key_hint}`")

    if sc.input_chords is not None:
        blocks.append("**Input (chords):** `" + " ".join(sc.input_chords) + "`")
    if sc.input_romans:
        blocks.append("**Input (romans):** `" + " ".join(sc.input_romans) + "`")

    # Expected
    exp_lines = []
    if sc.expected_key:
        exp_lines.append(f"- key: `{sc.expected_key}`")
    if sc.expected_romans:
        exp_lines.append("- romans: `" + " ".join(sc.expected_romans) + "`")
    if sc.expected_mode:
        exp_lines.append(f"- mode: `{sc.expected_mode}`")
    if sc.forbidden_modes:
        exp_lines.append(
            "- mode must NOT be: " + ", ".join(f"`{m}`" for m in sc.forbidden_modes)
        )
    if sc.expected_patterns:
        exp_lines.append(
            "- patterns expected: " + ", ".join(f"`{p}`" for p in sc.expected_patterns)
        )
    if exp_lines:
        blocks.append("**Expected:**\n" + "\n".join(exp_lines))

    # Actual
    if out.error:
        blocks.append(f"**Analyzer error:** `{out.error}`")
    else:
        act_lines = [
            f"- key: `{out.key}`",
            "- romans: `" + " ".join(out.romans) + "`",
            f"- mode: `{out.mode}`",
            f"- confidence: `{out.confidence:.3f}`",
        ]
        blocks.append("**Actual:**\n" + "\n".join(act_lines))

    # Side-by-side diff if romans differ
    if (
        sc.expected_romans is not None
        and not out.error
        and sc.expected_romans != out.romans
    ):
        blocks.append(
            "**Roman numeral diff:**\n" + _diff_romans(sc.expected_romans, out.romans)
        )

    # Cadences / patterns the analyzer fired, with explanation
    if out.patterns:
        cad_lines = ["**Cadences & patterns detected:**"]
        cad_lines.append("| span | family | name | role | score | explanation |")
        cad_lines.append("|---|---|---|---|---:|---|")
        for p in out.patterns:
            role = p["cadence_role"] or "—"
            expl = (p["explanation"] or "").replace("|", "\\|")
            cad_lines.append(
                f"| {p['span'][0]}–{p['span'][1]} | {p['family']} | "
                f"{p['name']} | {role} | {p['score']:.2f} | {expl} |"
            )
        blocks.append("\n".join(cad_lines))

    if v == "DIFFERS":
        blocks.append("**Differences:**\n" + "\n".join(f"- {i}" for i in issues))

    if sc.rationale:
        blocks.append("**Rationale:** " + sc.rationale)

    return "\n\n".join(blocks)


def render_markdown(rows: list[tuple[TestScenario, AnalyzerOutput]]) -> str:
    parts = [
        "# Harmonic Analysis Test Overview",
        "",
        "_Generated by `scripts/generate_test_overview.py`. Re-run after "
        "adding new fixtures._",
        "",
        f"**Total scenarios:** {len(rows)}",
        "",
        "## Summary",
        "",
        render_summary(rows),
        "",
        "## Detail",
        "",
    ]

    # Group by source file in stable order: oracle → golden → pattern-test → dcml
    kind_order = {"oracle": 0, "golden": 1, "pattern-test": 2, "dcml": 3}
    rows_sorted = sorted(
        rows,
        key=lambda r: (
            kind_order.get(r[0].source_kind, 99),
            r[0].source_file,
            r[0].name,
        ),
    )

    current_file: Optional[str] = None
    for sc, out in rows_sorted:
        if sc.source_file != current_file:
            current_file = sc.source_file
            parts.append(f"### `{current_file}`")
            parts.append("")
        parts.append(render_case(sc, out))
        parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    scenarios: list[TestScenario] = []
    scenarios += load_oracle_fixtures()
    scenarios += load_golden_fixtures()
    scenarios += load_pattern_tests()
    scenarios += load_dcml_fixtures()

    print(f"Discovered {len(scenarios)} scenarios:")
    by_kind: dict[str, int] = {}
    for sc in scenarios:
        by_kind[sc.source_kind] = by_kind.get(sc.source_kind, 0) + 1
    for k, n in sorted(by_kind.items()):
        print(f"  {k:<14} {n}")

    print("Running analyzer...")
    outputs = asyncio.run(run_all(scenarios))

    md = render_markdown(list(zip(scenarios, outputs)))
    out_path = REPO_ROOT / "docs" / "explanation" / "test-overview.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    exact_n = sum(
        1 for sc, o in zip(scenarios, outputs) if verdict(sc, o)[0] == "EXACT"
    )
    diff_n = sum(
        1 for sc, o in zip(scenarios, outputs) if verdict(sc, o)[0] == "DIFFERS"
    )
    na_n = sum(1 for sc, o in zip(scenarios, outputs) if verdict(sc, o)[0] == "N/A")
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")
    print(f"  exact: {exact_n}   differs: {diff_n}   N/A: {na_n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
