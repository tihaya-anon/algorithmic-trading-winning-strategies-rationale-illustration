#!/usr/bin/env bash
set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

usage() {
  cat <<'USAGE'
Usage: scripts/shell/sync-output-formats.sh [--check]

Maintains generated Quarto output settings for section files:
  video-lesson-slides.qmd
  web-notes.qmd
  pdf-notes.qmd

Default mode rewrites each file's YAML front matter so authors only maintain
descriptive metadata such as title, subtitle, author, and date.

Options:
  --check  Fail if any section file has stale generated output settings.
USAGE
}

mode="write"
case "${1:-}" in
  "")
    ;;
  --check)
    mode="check"
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 64
    ;;
esac

repo_root="$(repo_root_from_script "${BASH_SOURCE[0]}")"
tmp_dir="$(make_temp_dir)"
check_failed=0

cleanup() {
  rm -rf -- "$tmp_dir"
}
trap cleanup EXIT

relpath() {
  relpath_from_root "$repo_root" "$1"
}

for_each_section_output() {
  find "$repo_root/chapters" -type f \( \
    -path '*/sections/[0-9][0-9]-*/video-lesson-slides.qmd' -o \
    -path '*/sections/[0-9][0-9]-*/web-notes.qmd' -o \
    -path '*/sections/[0-9][0-9]-*/pdf-notes.qmd' \
  \) | sort
}

split_qmd() {
  local file="$1"
  local metadata="$2"
  local body="$3"

  awk -v metadata="$metadata" -v body="$body" '
    NR == 1 {
      if ($0 != "---") {
        exit 10
      }
      in_yaml = 1
      next
    }
    in_yaml && $0 == "---" {
      in_yaml = 0
      found_end = 1
      next
    }
    in_yaml {
      print > metadata
      next
    }
    found_end {
      print > body
    }
    END {
      if (!found_end) {
        exit 11
      }
    }
  ' "$file" || die "sync-output-formats" "missing YAML front matter delimiters in $(relpath "$file")"
}

strip_generated_metadata() {
  local input="$1"
  local output="$2"

  awk '
    function is_top_level_key(line) {
      return line ~ /^[^[:space:]#][^:]*:[[:space:]]*/
    }
    function is_generated_key(line) {
      return line ~ /^(format|execute|filters|include-in-header|include-before-body|include-after-body):[[:space:]]*/
    }
    {
      if (skipping && is_top_level_key($0)) {
        skipping = 0
      }
      if (!skipping && is_generated_key($0)) {
        skipping = 1
        next
      }
      if (skipping) {
        next
      }
      print
    }
  ' "$input" > "$output"
}

trim_trailing_blank_lines() {
  local input="$1"

  awk '
    {
      lines[NR] = $0
      if ($0 !~ /^[[:space:]]*$/) {
        last = NR
      }
    }
    END {
      for (i = 1; i <= last; i++) {
        print lines[i]
      }
    }
  ' "$input"
}

format_block_for() {
  local filename="$1"

  case "$filename" in
    video-lesson-slides.qmd)
      cat <<'YAML'
format:
  revealjs:
    theme: default
    css: ../../../../styles/reveal.css
    slide-number: true
    controls: true
    progress: true
    menu: false
    transition: slide
    transition-speed: fast
    center: false
    auto-stretch: true
    auto-animate: true
    show-notes: false
    scrollable: true
    embed-resources: false
filters:
  - ../../../../scripts/lua/remove-reveal-notes.lua
include-before-body:
  - ../../../../styles/reveal-audience-only.html
execute:
  echo: true
YAML
      ;;
    web-notes.qmd)
      cat <<'YAML'
format:
  html:
    toc: true
    toc-depth: 3
    number-sections: true
    code-fold: show
    code-tools: false
include-after-body:
  - ../../../../styles/web-note-modal.html
YAML
      ;;
    pdf-notes.qmd)
      cat <<'YAML'
format:
  pdf:
    pdf-engine: xelatex
    mainfont: "NotoSerifCJKsc-Regular.otf"
    mainfontoptions:
      - "Path=../../../../assets/fonts/"
      - "BoldFont=NotoSerifCJKsc-Bold.otf"
    sansfont: "NotoSansCJKsc-Regular.otf"
    sansfontoptions:
      - "Path=../../../../assets/fonts/"
      - "BoldFont=NotoSansCJKsc-Bold.otf"
    monofont: "MapleMono-NF-CN-Regular.ttf"
    monofontoptions:
      - "Path=../../../../assets/fonts/"
      - "BoldFont=MapleMono-NF-CN-Bold.ttf"
      - "ItalicFont=MapleMono-NF-CN-Italic.ttf"
      - "BoldItalicFont=MapleMono-NF-CN-BoldItalic.ttf"
    mathfont: "latinmodern-math.otf"
    toc: true
    number-sections: true
    colorlinks: true
    linkcolor: blue
    urlcolor: blue
    filecolor: blue
include-in-header:
  text: |
    \addtokomafont{disposition}{\rmfamily\bfseries}
    \addtokomafont{title}{\rmfamily\bfseries}
    \addtokomafont{author}{\rmfamily}
    \addtokomafont{date}{\rmfamily}
YAML
      ;;
    *)
      die "sync-output-formats" "unsupported section output: $filename"
      ;;
  esac
}

generate_qmd() {
  local source="$1"
  local output="$2"
  local metadata="$tmp_dir/metadata.yml"
  local filtered_metadata="$tmp_dir/filtered-metadata.yml"
  local body="$tmp_dir/body.qmd"
  local filename

  filename="$(basename -- "$source")"
  : > "$metadata"
  : > "$filtered_metadata"
  : > "$body"

  split_qmd "$source" "$metadata" "$body"
  strip_generated_metadata "$metadata" "$filtered_metadata"

  {
    printf '%s\n' '---'
    trim_trailing_blank_lines "$filtered_metadata"
    printf '\n'
    format_block_for "$filename"
    printf '%s\n' '---'
    cat "$body"
  } > "$output"
}

sync_qmd() {
  local file="$1"
  local generated="$tmp_dir/$(relpath "$file" | tr '/' '__')"

  generate_qmd "$file" "$generated"

  if [[ "$mode" == "check" ]]; then
    if ! cmp -s "$generated" "$file"; then
      printf 'Generated output settings are stale: %s\n' "$(relpath "$file")" >&2
      diff -u "$file" "$generated" || true
      check_failed=1
    fi
  else
    mv -- "$generated" "$file"
  fi
}

main() {
  local file
  local file_count=0

  while IFS= read -r file; do
    file_count=$((file_count + 1))
    sync_qmd "$file"
  done < <(for_each_section_output)

  [[ "$file_count" -gt 0 ]] || die "no section output files found under chapters/chapter-*/sections/"

  if [[ "$mode" == "check" ]]; then
    exit "$check_failed"
  fi

  printf 'Synced generated Quarto output settings for section files.\n'
}

main
