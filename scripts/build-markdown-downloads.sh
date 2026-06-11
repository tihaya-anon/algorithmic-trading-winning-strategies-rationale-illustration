#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/build-markdown-downloads.sh [--check]

Generate downloadable Markdown artifacts for each web-notes section:
  downloads/section.md
  downloads/section.json
  downloads/section-bundle.zip

The Markdown export strips QMD front matter and local web-only link blocks.
The bundle zip contains the generated Markdown plus any locally referenced image
assets used by that section.

Options:
  --check  Fail if generated downloads are stale.
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

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
tmp_dir="$(mktemp -d)"
check_failed=0

cleanup() {
  rm -rf -- "$tmp_dir"
}
trap cleanup EXIT

die() {
  printf 'build-markdown-downloads: %s\n' "$*" >&2
  exit 1
}

relpath() {
  local path="$1"
  printf '%s\n' "${path#"$repo_root"/}"
}

for_each_web_notes() {
  find "$repo_root/chapters" -type f -path '*/sections/[0-9][0-9]-*/web-notes.qmd' | sort
}

split_qmd() {
  local file="$1"
  local body="$2"

  awk -v body="$body" '
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
    !in_yaml && found_end {
      print > body
    }
    END {
      if (!found_end) {
        exit 11
      }
    }
  ' "$file" || die "missing YAML front matter delimiters in $(relpath "$file")"
}

render_markdown_body() {
  local source="$1"
  local output="$2"
  local body="$tmp_dir/body.qmd"

  : > "$body"
  split_qmd "$source" "$body"

  awk '
    /^:::[[:space:]]+\{\.section-output-links\}[[:space:]]*$/ { skip = 1; next }
    skip && /^:::[[:space:]]*$/ { skip = 0; next }
    !skip { print }
  ' "$body" > "$output"

  perl -0pi -e 's/\n# Reading Path\n.*\z/\n/s' "$output"
  perl -0pi -e 's/([[(][^)\n]*)video-lesson-slides\.qmd([)\]])/${1}video-lesson-slides.html$2/g; s/([[(][^)\n]*)pdf-notes\.qmd([)\]])/${1}pdf-notes.pdf$2/g; s/([[(][^)\n]*)web-notes\.qmd([)\]])/${1}web-notes.md$2/g' "$output"
}

escape_for_json_string() {
  local file="$1"
  node -e 'const fs=require("fs"); const text=fs.readFileSync(process.argv[1], "utf8"); process.stdout.write(JSON.stringify(text));' "$file"
}

collect_local_assets() {
  local markdown_file="$1"
  awk '
    {
      line = $0
      while (match(line, /!\[[^]]*\]\(([^)]+)\)/, m)) {
        path = m[1]
        sub(/[[:space:]]+".*$/, "", path)
        if (path !~ /^(https?:|mailto:|#|data:)/) {
          print path
        }
        line = substr(line, RSTART + RLENGTH)
      }
    }
  ' "$markdown_file" | sort -u
}

build_bundle_zip() {
  local section_dir="$1"
  local markdown_file="$2"
  local zip_file="$3"
  local bundle_dir="$tmp_dir/bundle"
  local asset_rel asset_src asset_dir

  rm -rf -- "$bundle_dir"
  mkdir -p "$bundle_dir"
  cp -- "$markdown_file" "$bundle_dir/section.md"

  while IFS= read -r asset_rel; do
    [[ -n "$asset_rel" ]] || continue
    asset_src="$section_dir/$asset_rel"
    [[ -f "$asset_src" ]] || continue
    asset_dir="$bundle_dir/$(dirname -- "$asset_rel")"
    mkdir -p "$asset_dir"
    cp -- "$asset_src" "$asset_dir/"
  done < <(collect_local_assets "$markdown_file")

  (
    cd "$bundle_dir"
    zip -qr "$zip_file" .
  )
}

compare_zip_contents() {
  local expected_zip="$1"
  local actual_zip="$2"
  local expected_list="$tmp_dir/expected-zip.txt"
  local actual_list="$tmp_dir/actual-zip.txt"
  local extract_expected="$tmp_dir/extract-expected"
  local extract_actual="$tmp_dir/extract-actual"

  unzip -Z1 "$expected_zip" | sort > "$expected_list"
  unzip -Z1 "$actual_zip" | sort > "$actual_list"
  cmp -s "$expected_list" "$actual_list" || return 1

  rm -rf -- "$extract_expected" "$extract_actual"
  mkdir -p "$extract_expected" "$extract_actual"
  unzip -qq "$expected_zip" -d "$extract_expected"
  unzip -qq "$actual_zip" -d "$extract_actual"

  diff -qr "$extract_expected" "$extract_actual" >/dev/null
}

sync_one() {
  local source="$1"
  local section_dir downloads_dir markdown_target json_target zip_target
  local markdown_generated json_generated zip_generated markdown_json

  section_dir="$(dirname -- "$source")"
  downloads_dir="$section_dir/downloads"
  markdown_target="$downloads_dir/section.md"
  json_target="$downloads_dir/section.json"
  zip_target="$downloads_dir/section-bundle.zip"
  markdown_generated="$tmp_dir/$(basename -- "$section_dir").md"
  json_generated="$tmp_dir/$(basename -- "$section_dir").json"
  zip_generated="$tmp_dir/$(basename -- "$section_dir").zip"

  mkdir -p "$downloads_dir"
  render_markdown_body "$source" "$markdown_generated"
  markdown_json="$(escape_for_json_string "$markdown_generated")"
  printf '{\n  "markdown": %s\n}\n' "$markdown_json" > "$json_generated"

  build_bundle_zip "$section_dir" "$markdown_generated" "$zip_generated"

  if [[ "$mode" == "check" ]]; then
    if [[ ! -f "$markdown_target" ]] || ! cmp -s "$markdown_generated" "$markdown_target"; then
      printf 'Generated Markdown export is stale: %s\n' "$(relpath "$markdown_target")" >&2
      check_failed=1
    fi
    if [[ ! -f "$json_target" ]] || ! cmp -s "$json_generated" "$json_target"; then
      printf 'Generated Markdown JSON is stale: %s\n' "$(relpath "$json_target")" >&2
      check_failed=1
    fi
    if [[ ! -f "$zip_target" ]] || ! compare_zip_contents "$zip_generated" "$zip_target"; then
      printf 'Generated Markdown bundle is stale: %s\n' "$(relpath "$zip_target")" >&2
      check_failed=1
    fi
  else
    mv -- "$markdown_generated" "$markdown_target"
    mv -- "$json_generated" "$json_target"
    mv -- "$zip_generated" "$zip_target"
  fi
}

main() {
  local file
  local file_count=0

  while IFS= read -r file; do
    file_count=$((file_count + 1))
    sync_one "$file"
  done < <(for_each_web_notes)

  [[ "$file_count" -gt 0 ]] || die "no web-notes.qmd files found under chapters/chapter-*/sections/"

  if [[ "$mode" == "check" ]]; then
    exit "$check_failed"
  fi

  printf 'Built Markdown downloads for section web notes.\n'
}

main
