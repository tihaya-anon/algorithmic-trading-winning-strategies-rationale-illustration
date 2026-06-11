#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/sync-template.sh <target-dir> [infra|full] [--dry-run] [--overwrite-quarto-config]

Modes:
  infra  Sync reusable Quarto infrastructure only:
         .github/, .vscode/, styles/, assets/fonts/, and _quarto.yml when missing.
  full   Sync this whole template, excluding .git, render caches, and outputs.

Examples:
  scripts/sync-template.sh ../my-course --dry-run
  scripts/sync-template.sh ../my-course
  scripts/sync-template.sh ../my-course --overwrite-quarto-config
  scripts/sync-template.sh ../new-course full
USAGE
}

die() {
  printf 'sync-template: %s\n' "$*" >&2
  exit 1
}

command -v rsync >/dev/null 2>&1 || die "rsync is required"

mode="infra"
target_input=""
dry_run=()
overwrite_quarto_config=0

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --dry-run)
      dry_run=(--dry-run)
      ;;
    --overwrite-quarto-config)
      overwrite_quarto_config=1
      ;;
    infra|full)
      mode="$arg"
      ;;
    -*)
      die "unknown option: $arg"
      ;;
    *)
      if [[ -n "$target_input" ]]; then
        die "only one target directory is allowed"
      fi
      target_input="$arg"
      ;;
  esac
done

[[ -n "$target_input" ]] || {
  usage >&2
  exit 64
}

source_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
mkdir -p -- "$target_input"
target_root="$(cd -- "$target_input" && pwd -P)"

[[ "$source_root" != "$target_root" ]] || die "target must be different from the template repo"

case "$target_root/" in
  "$source_root"/*)
    die "target must not be inside the template repo"
    ;;
esac

rsync_common=(-a "${dry_run[@]}")

sync_dir() {
  local rel="$1"
  mkdir -p -- "$target_root/$rel"
  rsync "${rsync_common[@]}" "$source_root/$rel/" "$target_root/$rel/"
}

sync_file() {
  local rel="$1"
  mkdir -p -- "$target_root/$(dirname -- "$rel")"
  rsync "${rsync_common[@]}" "$source_root/$rel" "$target_root/$rel"
}

case "$mode" in
  infra)
    sync_dir ".github"
    sync_dir ".vscode"
    sync_dir "styles"
    sync_dir "assets/fonts"
    if [[ -e "$target_root/_quarto.yml" && "$overwrite_quarto_config" -eq 0 ]]; then
      printf 'Skipped existing _quarto.yml; pass --overwrite-quarto-config to replace it.\n'
    else
      sync_file "_quarto.yml"
    fi
    ;;
  full)
    rsync -a --delete "${dry_run[@]}" \
      --exclude '/.git/' \
      --exclude '/.agents/' \
      --exclude '/.codex/' \
      --exclude '/.quarto/' \
      --exclude '/_site/' \
      --exclude '/.DS_Store' \
      --exclude '/Thumbs.db' \
      "$source_root/" "$target_root/"
    ;;
  *)
    die "unknown mode: $mode"
    ;;
esac

if [[ ${#dry_run[@]} -gt 0 ]]; then
  printf 'Dry run complete for %s sync into %s\n' "$mode" "$target_root"
else
  printf 'Synced %s template files into %s\n' "$mode" "$target_root"
fi
