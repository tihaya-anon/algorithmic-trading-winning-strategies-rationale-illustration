#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root="$(cd -- "$script_dir/../.." && pwd -P)"
theme_config="$repo_root/scripts/mermaid-theme.json"
puppeteer_config="$repo_root/scripts/puppeteer-config.json"

runner=()
if command -v mmdc >/dev/null 2>&1; then
  runner=("mmdc")
elif command -v npx >/dev/null 2>&1; then
  runner=("npx" "-y" "@mermaid-js/mermaid-cli")
else
  echo "Need 'mmdc' or 'npx' in PATH to render Mermaid diagrams." >&2
  exit 1
fi

render_one() {
  local input_path=$1
  local output_path=$2

  "${runner[@]}" \
    -i "$input_path" \
    -o "$output_path" \
    -e svg \
    -b transparent \
    -t default \
    -c "$theme_config" \
    --puppeteerConfigFile "$puppeteer_config" \
    -w 1600 \
    -s 2
}

render_all() {
  local -a files=()
  mapfile -d '' files < <(find chapters -type f \( -name '*.mmd' -o -name '*.mermaid' \) -path '*/figures/*' -print0 | sort -z)

  if [[ ${#files[@]} -eq 0 ]]; then
    echo "No Mermaid source files found under chapters/**/figures." >&2
    exit 1
  fi

  local input_path
  for input_path in "${files[@]}"; do
    local output_path=${input_path%.*}.svg
    echo "Rendering $input_path -> $output_path"
    render_one "$input_path" "$output_path"
  done
}

if [[ $# -eq 0 ]]; then
  render_all
  exit 0
fi

if [[ $# -gt 2 ]]; then
  echo "Usage: $0 [INPUT.mmd [OUTPUT.svg]]" >&2
  echo "Default with no args: render all Mermaid files under chapters/**/figures." >&2
  exit 1
fi

input_path=$1
output_path=${2:-${input_path%.*}.svg}

if [[ ! -f "$input_path" ]]; then
  echo "Input file not found: $input_path" >&2
  exit 1
fi

render_one "$input_path" "$output_path"
