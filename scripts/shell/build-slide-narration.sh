#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/shell/build-slide-narration.sh [options]

Extract slide notes from `video-lesson-slides.qmd`, call the adjacent `../tts`
repository, generate section narration audio, and write `narration/manifest.json`.

Options:
  --section PATH      Specific section directory or video-lesson-slides.qmd file
  --check             Validate manifest and audio files without calling TTS
  --voice NAME        TTS voice name (default: course-narrator-v1)
  --model NAME        TTS model id (default: hexgrad/Kokoro-82M)
  --format wav|mp3    Output format (default: mp3)
  --engine NAME       Forwarded to `tts-synthesize` (default: auto)
  --padding-ms N      Reveal auto-slide padding in milliseconds (default: 800)
  --tts-dir PATH      Adjacent TTS repo path (default: ../tts)
  -h, --help          Show this help
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$repo_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"

exec uv run --no-project python scripts/python/build_slide_narration.py "$@"
