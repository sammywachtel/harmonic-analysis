Harmonic Analysis – Developer Guidelines (Project-Specific)

Audience: Senior engineers contributing to the Python library under this repo. This is not a generic Python guide; it documents the idiosyncrasies of this codebase: how it’s built, tested, and maintained.

1. Build and Configuration

1.1 Supported runtimes
- Python: 3.10–3.12 (pyproject [project.requires-python])
- Local dev is typically on 3.11 (mypy config targets 3.11)

1.2 Packaging/build
- Build backend: hatchling (pyproject [build-system])
- Version source: src/harmonic_analysis/__init__.py (tool.hatch.version.path)
- To build wheels/sdist locally:
  - python -m pip install build
  - python -m build  # produces dist/
- Editable install for development:
  - pip install -e ".[dev]"

1.3 Project layout
- Library source: src/harmonic_analysis/
- Tests: tests/
- Quality/automation: scripts/ (see scripts/README.md)
- Examples and demo: demo/, examples/

1.4 Tooling and configuration
- Formatting: Black (line length 88) and isort (profile=black)
- Linting: flake8 (setup.cfg)
- Typing: mypy (strict-ish toggles in pyproject)
- Security scan: bandit
- Test runner: pytest (>=8, configured in pyproject)
- Make targets: see Makefile
  - make format → python scripts/quality_check.py --fix
  - make lint → python scripts/quality_check.py
  - make test → pytest tests/ -v
  - make quality → python scripts/quality_check.py

1.5 Pre-commit hooks
- Pre-commit is expected. quality_check.py verifies installation and hooks presence.
- Setup on a fresh clone:
  - pip install -e ".[dev]"
  - pre-commit install
  - Optionally run: python scripts/setup_dev_env.py (sets up extras + IDE helpers)

1.6 Coverage settings nuance
- pytest is invoked with: --cov=harmonic_analysis and writes htmlcov/ (pyproject [tool.pytest.ini_options.addopts]).
- coverage.tool section in pyproject under [tool.coverage.run] has source=["app"]. That is for legacy app integration and does not affect pytest-cov invocation. If you run coverage directly (coverage run -m pytest), adjust source to harmonic_analysis or rely on pytest-cov.

2. Testing

2.1 How tests are discovered
- Configured in pyproject:
  - testpaths = ["tests"]
  - python_files = ["test_*.py", "*_test.py"]
  - python_classes = ["Test*"]
  - python_functions = ["test_*"]
- Strict markers and strict config are enabled (addopts includes --strict-markers --strict-config). All custom markers must be declared or present in pyproject.

2.2 Custom markers available
Declared in pyproject [tool.pytest.ini_options.markers]:
- unit, integration, functional, modal, chromatic, slow, asyncio
Examples:
- Run only unit tests: pytest -m unit -q
- Exclude slow tests: pytest -m "not slow" -q

2.3 Async tests without pytest-asyncio
- tests/conftest.py implements a minimal async runner. Any test defined with async def is executed via asyncio.run automatically.
- You can still use @pytest.mark.asyncio but it’s not required here.

2.4 Running tests
- Full suite with coverage (default addopts):
  - pytest
- Verbose single file:
  - pytest tests/test_chord_parser.py -v
- Specific test/case:
  - pytest tests/test_comprehensive_multi_layer_validation.py::TestComprehensiveMultiLayerValidation::test_edge_cases -v
- Quick smoke tests (no coverage), via quality harness:
  - python scripts/quality_check.py --quick-tests

2.5 Skips, xfail, and edge-case warnings policy
- Some tests are explicitly skipped (SKIPPED) pending algorithmic refinements (see test output reasons). Treat these as non-blocking.
- Some scenarios are expected to xfail while frameworks are incomplete (XFAIL in summary). Do not “fix” by changing tests unless the underlying feature is implemented; update tests and docs together.
- Edge-case behavioral warnings are emitted via tests/edge_case_warnings.py. These are warnings (not failures) to keep pressure on calibration without blocking merges.

2.6 Adding new tests (guidelines specific to this project)
- Prefer unit-level tests close to algorithmic boundaries (parsers, scale inference, cadence detection) and add end-to-end cases only when they exercise new combinations.
- Use existing markers to categorize. If you need a new marker, add it in pyproject [tool.pytest.ini_options.markers] or the run will fail with --strict-markers.
- For async public API (e.g., analyze_chord_progression), write tests as async def and call directly; our conftest handles the event loop.
- Keep tests deterministic; do not rely on external services or time. If you need generated datasets, see scripts/generate_comprehensive_multi_layer_tests.py and put generated artifacts under tests/generated/ (already ignored in coverage and appropriate for large fixtures).
- Maintain human-readable assertions in end-to-end tests (explicit roman numerals, confidences with tolerances). Document the musical rationale in comments for future maintainers.

2.7 Demo test example (verified)
The following snippet was validated locally and can be used as a template for a minimal unit test:

```python
import pytest
from harmonic_analysis.utils.music_theory_constants import get_modal_characteristics

@pytest.mark.unit
def test_dorian_brightness_is_neutral():
    dorian = get_modal_characteristics("Dorian")
    assert dorian.brightness == "neutral"
```

Run just this file:
- pytest tests/test_demo_guidelines.py -q

Note: This demo file was created and executed to validate the process during documentation authoring and then removed to keep the repository clean, as per process standards.

2.8 Coverage and reports
- Default addopts include: --cov=harmonic_analysis --cov-report=html --cov-report=term-missing
- HTML coverage report is emitted to htmlcov/index.html
- To combine with xdist or speed up:
  - pytest -n auto  # requires pytest-xdist (installed via [project.optional-dependencies].test)

3. Development Practices & Debugging

3.1 Code style & consistency
- Black + isort are authoritative. Use make format or python scripts/quality_check.py --fix before commits.
- Flake8 rules: see setup.cfg (E203/W503 ignored to match Black). tests/ permitted long lines (E501) where necessary.
- Mypy: Strictness is elevated (no implicit optional, disallow untyped defs/decorators, etc.). Add focused type annotations in hot paths; if suppression is unavoidable, justify with a comment and prefer narrow ignore scopes.

3.2 Quality automation workflow
- One-shot setup: python scripts/setup_dev_env.py
- Daily loop:
  - python scripts/quality_check.py --quick-tests  # fast checks while iterating
  - python scripts/quality_check.py --fix          # before commits/pushes
  - pre-commit run --all-files                     # mirrors CI hooks

3.3 Known hotspots and expectations
- Functional harmony and modal analyzers are intentionally permissive with multiple interpretations; tests assert both confidence ranges and narrative explanations. When adjusting scoring, update edge-case tolerances and narrative keywords where appropriate.
- Suggestion engines (algorithmic/bidirectional) are under active development. Several tests are skipped or xfail with clear reasons. Align changes with the rationale in tests and README sections describing suggestion confidence.
- Scale/melody analysis intentionally separates “melody tonic” detection from “scale membership”. Don’t cross these concerns; tests check that scale analysis does not fabricate a tonic.

3.4 Debugging tips
- Re-run only the failing class/method with -vv and -k filters for faster cycles.
- Inspect evidence collections in results (cadential/structural/intervallic) to understand confidence deltas.
- When a reasoning string mismatch occurs, prefer improving the generation logic rather than relaxing tests; the narrative is part of the UX contract.

3.5 Performance
- The comprehensive test suite is sizeable. Use pytest -k to slice by feature or marker (e.g., -k "chromatic and not slow").
- Quick checks via scripts/quality_check.py --quick-tests skip coverage and stop early on first failure to shorten the loop.

Appendix A — Commands Cheat Sheet
- Setup dev env: pip install -e ".[dev]" && pre-commit install
- Full suite: pytest
- Subset by marker: pytest -m modal -q
- Format + imports: python scripts/quality_check.py --fix
- Lint/type/security + quick tests: python scripts/quality_check.py --quick-tests
- Build dist: python -m build
- Make targets: make [format|lint|test|quality]

Status of this document
- Verified date/time: 2025-08-29 08:56 local
- A demo test was created, executed successfully, and removed after verification, per the instructions. Only this .junie/guidelines.md file remains as an artifact of the documentation task.
