#!/usr/bin/env bash
# Poke the /api/analyze/audio route with curl.
#
# Direct library calls live in scripts/try_audio.py — use that if you
# don't need the HTTP round-trip. This script is for proving the route
# works end-to-end (FastAPI multipart, JSON serialization, the whole
# stack) without firing up a browser.
#
# Usage:
#   ./scripts/try_audio_http.sh path/to/your.wav
#   ./scripts/try_audio_http.sh path/to/your.wav 0 30        # segment 0-30s
#   ./scripts/try_audio_http.sh --synth                       # generate + post /tmp/a_major.wav
#   PORT=8765 ./scripts/try_audio_http.sh path/to/your.wav    # override port
#
# Requires: backend running on $PORT (default 8000). Start it with:
#   uvicorn demo.backend.rest_api.main:app --reload --port 8000
# from the project root.

set -euo pipefail

PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
URL="http://${HOST}:${PORT}/api/analyze/audio"

# bash 3.2 — no associative arrays, no ${var^^}. macOS default ships 3.2.
synth_wav() {
  # Three-partial A-major triad. Same recipe as scripts/try_audio.py
  # so the smoke-test signal is consistent across tools.
  python3 - <<'PY'
import numpy as np, soundfile as sf
t = np.linspace(0, 5, 22050 * 5, endpoint=False)
sig = (np.sin(2*np.pi*440*t) + np.sin(2*np.pi*554.37*t) + np.sin(2*np.pi*659.25*t)) / 3
sf.write('/tmp/a_major.wav', (sig * 0.5).astype('float32'), 22050)
PY
  echo "/tmp/a_major.wav"
}

if [[ "${1:-}" == "--synth" ]]; then
  echo "(generating synthetic A-major WAV...)" >&2
  FILE="$(synth_wav)"
  START="${2:-}"
  END="${3:-}"
else
  FILE="${1:-}"
  START="${2:-}"
  END="${3:-}"
fi

if [[ -z "${FILE}" ]]; then
  echo "usage: $0 <wav-file> [start-sec] [end-sec]" >&2
  echo "       $0 --synth [start-sec] [end-sec]" >&2
  exit 2
fi

if [[ ! -f "${FILE}" ]]; then
  echo "error: no such file: ${FILE}" >&2
  exit 2
fi

# Quick liveness check so we fail loud if the server isn't up, instead
# of curl emitting an inscrutable connection-refused.
if ! curl -fsS "${URL%/api/analyze/audio}/openapi.json" -o /dev/null 2>/dev/null; then
  echo "error: backend not reachable at ${URL}" >&2
  echo "hint:  uvicorn demo.backend.rest_api.main:app --port ${PORT}  (from project root)" >&2
  exit 3
fi

# Build the form. -F repeats are the same as multiple form fields.
ARGS=(-sS -X POST -F "file=@${FILE}")
if [[ -n "${START}" ]]; then
  ARGS+=(-F "start=${START}")
fi
if [[ -n "${END}" ]]; then
  ARGS+=(-F "end=${END}")
fi

# Pretty-print if jq is around, otherwise fall back to python's json.tool.
if command -v jq >/dev/null 2>&1; then
  curl "${ARGS[@]}" "${URL}" | jq .
else
  curl "${ARGS[@]}" "${URL}" | python3 -m json.tool
fi
