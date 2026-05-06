#!/usr/bin/env bash
# Validate that every script referenced inside .github/workflows/*.yml still
# exists on disk. Pre-commit invokes this whenever a workflow YAML or a script
# under scripts/ changes, so we catch orphaned references before they hit CI.
#
# Catches references like:
#   python scripts/foo.py
#   bash scripts/foo.sh
#   ./scripts/foo.sh
#   sh scripts/foo.sh
#   chmod +x ./scripts/foo.sh
#
# Skips comment lines (^\s*#). Quoting is best-effort — false positives just
# mean we re-verify a file that exists (cheap).
#
# Bash compat: avoids mapfile (not in macOS's stock Bash 3.2). Uses a while-
# read loop into a regular array instead.
#
# Exit codes:
#   0 — every referenced script exists.
#   1 — at least one reference is broken; offending refs printed to stderr.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

WORKFLOW_DIR=".github/workflows"
if [[ ! -d "$WORKFLOW_DIR" ]]; then
    # No workflows in this repo — nothing to check.
    exit 0
fi

# Pull every "scripts/*.py" / "scripts/*.sh" token from non-comment YAML
# lines that are likely to be REAL invocations.
#
# We deliberately skip these soft references because they don't crash CI:
#   - lines starting with `echo` (fix-instruction strings)
#   - lines containing `[[ -f ` or `[[ -e ` (guarded "run only if present")
#   - lines containing `test -f` / `test -e`
#   - comment lines (already excluded by the # filter)
#
# What's left is the set of unguarded `python scripts/x.py` / `bash scripts/x.sh`
# / `./scripts/x.sh` invocations — the kind that hard-fail when the script
# disappears.
extract_refs() {
    grep -hE '\b(scripts/[A-Za-z0-9_./-]+\.(py|sh|js|ts))\b' \
        "$WORKFLOW_DIR"/*.yml "$WORKFLOW_DIR"/*.yaml 2>/dev/null \
        | grep -vE '^[[:space:]]*#' \
        | grep -vE '(^|[[:space:]])echo[[:space:]]' \
        | grep -vE '\[\[[[:space:]]*-[fe][[:space:]]' \
        | grep -vE '(^|[[:space:]])test[[:space:]]+-[fe][[:space:]]' \
        | grep -vE '(^|[[:space:]])chmod[[:space:]]' \
        | grep -vE '\$\([^)]*scripts/' \
        | sed -E 's#.*[^A-Za-z0-9_./-]?(scripts/[A-Za-z0-9_./-]+\.(py|sh|js|ts)).*#\1#' \
        | sort -u
}

MISSING=()
while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    # Strip shell artifacts (trailing punctuation if the regex was greedy).
    cleaned="${ref%%[\"\'\\\)\}\,\;]*}"
    [[ -z "$cleaned" ]] && continue
    if [[ ! -e "$cleaned" ]]; then
        MISSING+=("$cleaned")
    fi
done < <(extract_refs)

if (( ${#MISSING[@]} > 0 )); then
    echo "❌ Workflow files reference scripts that don't exist:" >&2
    for m in "${MISSING[@]}"; do
        matches=$(grep -l -E "${m//./\\.}" "$WORKFLOW_DIR"/*.yml "$WORKFLOW_DIR"/*.yaml 2>/dev/null \
            | sed 's#^#    - #')
        echo "  $m" >&2
        [[ -n "$matches" ]] && echo "$matches" >&2
    done
    echo "" >&2
    echo "Either restore the script or remove the workflow step that calls it." >&2
    exit 1
fi

exit 0
