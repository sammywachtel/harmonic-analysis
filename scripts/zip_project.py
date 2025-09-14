#!/usr/bin/env python3
"""
Zip the current project into the parent directory as harmonic-analysis.zip,
excluding non-code and transient folders/files.

Usage:
  python scripts/zip_project.py [--output FILENAME] [--dry-run]

Defaults:
  - Output zip path: ../harmonic-analysis.zip (relative to repo root)

Exclusions (directories/files):
  - .git, .venv, node_modules, .claude, .junie, .idea, .vscode
  - __pycache__, .mypy_cache, .pytest_cache, .tox, .eggs, build, dist, htmlcov
  - .DS_Store, *.pyc, *.pyo, *.pyd, *.so
  - coverage artifacts (coverage.json, .coverage*)
  - test-results, demo/e2e-tests/playwright-report, playwright-report

Notes:
  - The script is conservative: it includes source (src/), tests/, scripts/ and other
    top-level files by default unless excluded above.
  - Timestamp normalization: stores files with their existing mtimes; reproducible
    builds are not strictly guaranteed, but path ordering is stabilized.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT.parent / "harmonic-analysis.zip"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".claude",
    ".junie",
    ".idea",
    ".vscode",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".eggs",
    "build",
    "dist",
    "htmlcov",
    "playwright-report",
    "test-results",
}

# path prefixes (relative to repo root) to exclude entirely
EXCLUDE_PREFIXES = [
    "demo/e2e-tests/playwright-report",
    "docs/resources",
    "tests/integration/generated",
]

EXCLUDE_FILE_GLOBS = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    ".DS_Store",
    ".coverage*",
    "coverage.json",
]

INCLUDE_TOPLEVEL = {
    # Always useful
    "src",
    "tests",
    "scripts",
    "examples",
    "demo",
    "docs",
    # Config and metadata files are included unless filtered by file globs
}


def should_exclude_path(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    # Exclude by directory names in any part
    for part in rel.parts:
        if part in EXCLUDE_DIRS:
            return True
    # Exclude path prefixes
    rel_str = rel.as_posix()
    for prefix in EXCLUDE_PREFIXES:
        if rel_str.startswith(prefix):
            return True
    # Exclude file globs
    name = rel.name
    for pattern in EXCLUDE_FILE_GLOBS:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Modify dirnames in-place to skip excluded dirs efficiently
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        # Also drop directories by prefix rules
        drop = set()
        for d in dirnames:
            rel_sub = (rel_dir / d).as_posix()
            if any(rel_sub.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
                drop.add(d)
        if drop:
            dirnames[:] = [d for d in dirnames if d not in drop]
        for fname in filenames:
            p = Path(dirpath) / fname
            if not should_exclude_path(p):
                yield p


def build_file_list() -> list[Path]:
    files = []
    # Prefer including everything under repo root but rely on exclusions above.
    # To keep ordering stable, sort paths.
    for p in iter_files(REPO_ROOT):
        files.append(p)
    files.sort(key=lambda x: x.relative_to(REPO_ROOT).as_posix())
    return files


def create_zip(output: Path, dry_run: bool = False) -> int:
    files = build_file_list()
    if dry_run:
        print(f"Would write {len(files)} files to: {output}")
        for p in files[:50]:
            print("  ", p.relative_to(REPO_ROOT))
        if len(files) > 50:
            print(f"  ... and {len(files) - 50} more")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            arcname = p.relative_to(REPO_ROOT).as_posix()
            zf.write(p, arcname)
    print(f"Created archive: {output} ({len(files)} files)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Zip project excluding non-code folders"
    )
    parser.add_argument(
        "--output", type=str, default=str(DEFAULT_OUTPUT), help="Output zip path"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="List files instead of creating archive"
    )
    args = parser.parse_args(argv)

    output = Path(args.output).expanduser().resolve()

    # Ensure output is in parent by default; allow overrides
    return create_zip(output, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
