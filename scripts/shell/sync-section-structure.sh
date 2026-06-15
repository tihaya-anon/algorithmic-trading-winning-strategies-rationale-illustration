#!/usr/bin/env bash
set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

usage() {
  cat <<'USAGE'
Usage: scripts/shell/sync-section-structure.sh [--check|--verify-rendered]

Maintains the section-as-router structure:
  chapters/chapter-NN/sections/NN-section-slug/
    video-lesson-slides.qmd
    web-notes.qmd
    pdf-notes.qmd

Default mode rewrites generated routing files from the directory tree:
  _quarto.yml
  chapters/index.qmd
  .github/workflows/publish.yml

Options:
  --check            Fail if generated files are stale.
  --verify-rendered  Check rendered artifacts under _site/ without rendering.
USAGE
}

mode="write"
case "${1:-}" in
  "")
    ;;
  --check)
    mode="check"
    ;;
  --verify-rendered)
    mode="verify"
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
site_url_placeholder='{{< meta site-url >}}'

cleanup() {
  rm -rf -- "$tmp_dir"
}
trap cleanup EXIT

relpath() {
  relpath_from_root "$repo_root" "$1"
}

yaml_quote() {
  local value="${1//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '"%s"' "$value"
}

front_matter_title() {
  local file="$1"
  local fallback="$2"
  local title
  title="$(
    awk '
      NR == 1 && $0 == "---" { in_yaml = 1; next }
      in_yaml && $0 == "---" { exit }
      in_yaml && $0 ~ /^title:[[:space:]]*/ {
        sub(/^title:[[:space:]]*/, "", $0)
        gsub(/^"|"$/, "", $0)
        print
        exit
      }
    ' "$file"
  )"
  if [[ -n "$title" ]]; then
    printf '%s\n' "$title"
  else
    printf '%s\n' "$fallback"
  fi
}

section_label() {
  local chapter_dir="$1"
  local section_dir="$2"
  local chapter_base section_base chapter_num section_num
  chapter_base="$(basename -- "$chapter_dir")"
  section_base="$(basename -- "$section_dir")"
  chapter_num="${chapter_base#chapter-}"
  section_num="${section_base%%-*}"
  printf '%d.%d\n' "$((10#$chapter_num))" "$((10#$section_num))"
}

validate_tree() {
  local chapter_count=0
  local section_count=0
  local chapter_dir section_dir required

  shopt -s nullglob
  for chapter_dir in "$repo_root"/chapters/chapter-*; do
    [[ -d "$chapter_dir" ]] || continue
    chapter_count=$((chapter_count + 1))
    [[ -f "$chapter_dir/index.qmd" ]] || die "sync-section-structure" "missing chapter index: $(relpath "$chapter_dir")/index.qmd"
    [[ -d "$chapter_dir/sections" ]] || die "sync-section-structure" "missing sections directory: $(relpath "$chapter_dir")/sections"

    for section_dir in "$chapter_dir"/sections/[0-9][0-9]-*; do
      [[ -d "$section_dir" ]] || continue
      section_count=$((section_count + 1))
      for required in video-lesson-slides.qmd web-notes.qmd pdf-notes.qmd; do
        [[ -f "$section_dir/$required" ]] || die "sync-section-structure" "missing $required in $(relpath "$section_dir")"
      done
    done
  done
  shopt -u nullglob

  [[ "$chapter_count" -gt 0 ]] || die "sync-section-structure" "no chapters found under chapters/chapter-*"
  [[ "$section_count" -gt 0 ]] || die "sync-section-structure" "no sections found under chapters/chapter-*/sections/"
}

for_each_chapter() {
  find "$repo_root/chapters" -mindepth 1 -maxdepth 1 -type d -name 'chapter-*' | sort
}

for_each_section() {
  local chapter_dir="$1"
  find "$chapter_dir/sections" -mindepth 1 -maxdepth 1 -type d -name '[0-9][0-9]-*' | sort
}

for_each_section_file() {
  find "$repo_root/chapters" -type f \
    \( -path '*/sections/[0-9][0-9]-*/web-notes.qmd' -o -path '*/sections/[0-9][0-9]-*/pdf-notes.qmd' \) \
    | sort
}

strip_reading_path_block() {
  local input="$1"
  local output="$2"
  perl -0pe 's/\n*# Reading Path\n(?:.*\n?)*\z/\n/s' "$input" > "$output"
}

render_reading_path_block() {
  local prev_label="$1"
  local prev_url="$2"
  local next_label="$3"
  local next_url="$4"

  {
    printf '\n# Reading Path\n\n'
    printf -- '- Previous: [%s](%s)\n' "$prev_label" "$prev_url"
    printf -- '- Next: [%s](%s)\n' "$next_label" "$next_url"
  }
}

sync_reading_paths() {
  local -a sections=()
  local -a section_titles=()
  local chapter_dir section_dir section_rel section_title
  local i prev_label prev_url next_label next_url base_output generated_file target_file tmp_body

  while IFS= read -r chapter_dir; do
    while IFS= read -r section_dir; do
      sections+=("$section_dir")
      section_titles+=("$(front_matter_title "$section_dir/web-notes.qmd" "$(basename -- "$section_dir")")")
    done < <(for_each_section "$chapter_dir")
  done < <(for_each_chapter)

  for i in "${!sections[@]}"; do
    section_dir="${sections[$i]}"
    section_rel="$(relpath "$section_dir")"
    base_output="$tmp_dir/reading-path-$i"

    if (( i == 0 )); then
      prev_label="Chapter overview"
      prev_url="$site_url_placeholder/chapters/"
    else
      prev_label="${section_titles[$((i - 1))]}"
      prev_url="$site_url_placeholder/${sections[$((i - 1))]#"$repo_root"/}/"
    fi

    if (( i == ${#sections[@]} - 1 )); then
      next_label="Chapter overview"
      next_url="$site_url_placeholder/chapters/"
    else
      next_label="${section_titles[$((i + 1))]}"
      next_url="$site_url_placeholder/${sections[$((i + 1))]#"$repo_root"/}/"
    fi

    for target_file in "$section_dir/web-notes.qmd" "$section_dir/pdf-notes.qmd"; do
      generated_file="$base_output-$(basename "$target_file")"
      tmp_body="$generated_file.tmp"
      strip_reading_path_block "$target_file" "$tmp_body"
      cat "$tmp_body" > "$generated_file"
      render_reading_path_block "$prev_label" "$prev_url" "$next_label" "$next_url" >> "$generated_file"
      sync_generated_file "$generated_file" "$target_file"
    done
  done
}

generate_quarto_yml() {
  local out="$1"
  local chapter_dir section_dir chapter_title section_title label section_rel

  {
    cat <<'YAML'
# Generated by scripts/shell/sync-section-structure.sh.
# Edit chapter/section directories, then rerun the script.
project:
  type: website
  output-dir: _site

website:
  title: "Algorithmic Trading: Winning Strategies and Their Rationale"
  site-url: "https://tihaya-anon.github.io/algorithmic-trading-winning-strategies-rationale-illustration"
  navbar:
    left:
      - href: index.qmd
        text: Home
      - href: chapters/index.qmd
        text: Chapters
  sidebar:
    style: docked
    search: true
    contents:
      - href: index.qmd
        text: Home
      - href: chapters/index.qmd
        text: All Chapters
YAML

    while IFS= read -r chapter_dir; do
      chapter_title="$(front_matter_title "$chapter_dir/index.qmd" "$(basename -- "$chapter_dir")")"
      printf '      - section: %s\n' "$(yaml_quote "$chapter_title")"
      printf '        contents:\n'
      while IFS= read -r section_dir; do
        section_title="$(front_matter_title "$section_dir/web-notes.qmd" "$(basename -- "$section_dir")")"
        section_rel="$(relpath "$section_dir")"
        printf '          - href: %s/web-notes.qmd\n' "$section_rel"
        printf '            text: %s\n' "$(yaml_quote "$section_title")"
      done < <(for_each_section "$chapter_dir")
    done < <(for_each_chapter)

    cat <<'YAML'

format:
  html:
    theme: cosmo
    css: styles/web.css
    toc: true
    code-overflow: wrap
    smooth-scroll: true

execute:
  echo: true
  warning: false
  message: false
YAML
  } > "$out"
}

generate_chapters_index() {
  local out="$1"
  local chapter_dir section_dir chapter_title section_title chapter_rel section_rel

  {
    cat <<'QMD'
---
title: "Course Chapters"
subtitle: "Generated chapter and section index"
---

# Chapter Map

Use `chapters/` as the canonical content source. Each section owns three
outputs:

```text
chapters/
  chapter-NN/
    index.qmd
    sections/
      NN-section-slug/
        video-lesson-slides.qmd
        web-notes.qmd
        pdf-notes.qmd
```

The directory tree is the router. Run `scripts/shell/sync-section-structure.sh` after
adding, renaming, or removing section folders.
Run `scripts/shell/sync-output-formats.sh` after editing section front matter so
generated output settings stay aligned with each file type.

# Chapters

QMD

    while IFS= read -r chapter_dir; do
      chapter_title="$(front_matter_title "$chapter_dir/index.qmd" "$(basename -- "$chapter_dir")")"
      printf '## %s\n\n' "$chapter_title"
      while IFS= read -r section_dir; do
        section_title="$(front_matter_title "$section_dir/web-notes.qmd" "$(basename -- "$section_dir")")"
        section_rel="$(relpath "$section_dir")"
        section_rel="${section_rel#chapters/}"
        printf -- '- [%s](%s/web-notes.qmd)  \n' "$section_title" "$section_rel"
        printf -- '  Alternate formats: [video](%s/video-lesson-slides.qmd), [PDF](%s/pdf-notes.qmd)\n' \
          "$section_rel" "$section_rel"
      done < <(for_each_section "$chapter_dir")
      printf '\n'
    done < <(for_each_chapter)

    cat <<'QMD'
# Authoring Convention

- Create one folder per chapter: `chapters/chapter-02/`.
- Put the chapter landing page at `chapters/chapter-02/index.qmd`.
- Put each section under `chapters/chapter-02/sections/NN-section-slug/`.
- Include `video-lesson-slides.qmd`, `web-notes.qmd`, and `pdf-notes.qmd` in
  every section folder.
- Keep section front matter focused on descriptive metadata such as `title` and
  `subtitle`; run `scripts/shell/sync-output-formats.sh` to add generated formats.
- Run `scripts/shell/sync-section-structure.sh`; do not hand-edit generated routing.
QMD
  } > "$out"
}

generate_workflow() {
  local out="$1"
  cat > "$out" <<'YAML'
name: Publish Quarto Site

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    name: Render Quarto project
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Install system fonts
        run: |
          sudo apt-get update
          sudo apt-get install -y fonts-noto-core fonts-noto-cjk fonts-noto-mono

      - name: Check generated output settings
        run: scripts/shell/sync-output-formats.sh --check

      - name: Check generated section routing
        run: scripts/shell/sync-section-structure.sh --check

      - name: Build generated Markdown downloads
        run: bash scripts/shell/build-markdown-downloads.sh

      - name: Set up Quarto and TinyTeX
        uses: quarto-dev/quarto-actions/setup@v2
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tinytex: true

      - name: Render site and section outputs
        run: quarto render

      - name: Verify rendered section artifacts
        run: scripts/shell/sync-section-structure.sh --verify-rendered

      - name: Configure GitHub Pages
        uses: actions/configure-pages@v5

      - name: Upload static site
        uses: actions/upload-pages-artifact@v4
        with:
          path: _site

  deploy:
    name: Deploy GitHub Pages
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: ${{ vars.PAGES_ENVIRONMENT || 'github-pages' }}
      url: ${{ steps.deployment.outputs.page_url }}

    steps:
      - name: Deploy static site
        id: deployment
        uses: actions/deploy-pages@v5
YAML
}

sync_generated_file() {
  local generated="$1"
  local target="$2"

  if [[ "$mode" == "check" ]]; then
    if ! cmp -s "$generated" "$target"; then
      printf 'Generated file is stale: %s\n' "$(relpath "$target")" >&2
      diff -u "$target" "$generated" || true
      check_failed=1
    fi
  else
    mkdir -p -- "$(dirname -- "$target")"
    mv -- "$generated" "$target"
  fi
}

verify_rendered() {
  local missing=0
  local chapter_dir section_dir section_rel expected
  while IFS= read -r chapter_dir; do
    while IFS= read -r section_dir; do
      section_rel="$(relpath "$section_dir")"
      for expected in \
        "_site/$section_rel/video-lesson-slides.html" \
        "_site/$section_rel/web-notes.html" \
        "_site/$section_rel/pdf-notes.pdf"; do
        if [[ ! -f "$repo_root/$expected" ]]; then
          printf 'Missing rendered artifact: %s\n' "$expected" >&2
          missing=1
        fi
      done
    done < <(for_each_section "$chapter_dir")
  done < <(for_each_chapter)
  return "$missing"
}

validate_tree

if [[ "$mode" == "verify" ]]; then
  verify_rendered
  exit $?
fi

generate_quarto_yml "$tmp_dir/_quarto.yml"
generate_chapters_index "$tmp_dir/chapters-index.qmd"
generate_workflow "$tmp_dir/publish.yml"

sync_generated_file "$tmp_dir/_quarto.yml" "$repo_root/_quarto.yml"
sync_generated_file "$tmp_dir/chapters-index.qmd" "$repo_root/chapters/index.qmd"
sync_generated_file "$tmp_dir/publish.yml" "$repo_root/.github/workflows/publish.yml"
sync_reading_paths

if [[ "$mode" == "check" ]]; then
  exit "$check_failed"
fi

printf 'Synced section routing from chapters/*/sections/*.\n'
