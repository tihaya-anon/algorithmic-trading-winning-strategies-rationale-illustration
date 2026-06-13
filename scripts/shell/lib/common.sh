#!/usr/bin/env bash

repo_root_from_script() {
  local script_path="$1"
  cd -- "$(dirname -- "$script_path")/../.." && pwd -P
}

die() {
  local prefix="$1"
  shift
  printf '%s: %s\n' "$prefix" "$*" >&2
  exit 1
}

relpath_from_root() {
  local repo_root="$1"
  local path="$2"
  printf '%s\n' "${path#"$repo_root"/}"
}

make_temp_dir() {
  mktemp -d
}
