#!/usr/bin/env bash
set -euo pipefail

# Docker execution envelope for llm-patch.
#
# IMPORTANT:
# - This wrapper must not write anything to STDOUT.
# - Any validation errors must go to STDERR.
# - All args after the subcommand are forwarded unchanged.

fail() {
  echo "ERROR: $*" >&2
  exit 2
}

require_dir() {
  local path="$1"
  local label="$2"
  [[ -d "$path" ]] || fail "$label must be mounted at $path"
}

assert_read_only_dir() {
  local path="$1"
  local probe="$path/.llm_patch_ro_check.$$"

  # If we can write, it's not read-only.
  if ( : >"$probe" ) 2>/dev/null; then
    rm -f "$probe" 2>/dev/null || true
    fail "$path must be mounted read-only"
  fi
}

assert_writable_dir() {
  local path="$1"
  local probe="$path/.llm_patch_rw_check.$$"

  if ! ( : >"$probe" ) 2>/dev/null; then
    fail "$path must be writable"
  fi
  rm -f "$probe" 2>/dev/null || true
}

resolve_path() {
  # Canonicalize an existing path (absolute). If it does not exist, print empty.
  local p="$1"
  if [[ -z "$p" ]]; then
    return 0
  fi
  if command -v realpath >/dev/null 2>&1; then
    realpath "$p" 2>/dev/null || true
  else
    python - <<'PY' "$p" 2>/dev/null || true
import os, sys
p = sys.argv[1]
try:
    print(os.path.realpath(p))
except Exception:
    pass
PY
  fi
}

cmd="${1:-}"
if [[ -z "$cmd" ]]; then
  fail "missing subcommand (expected: fix)"
fi

case "$cmd" in
  fix)
    shift

    # Required mounts.
    require_dir /project "/project"
    require_dir /workspace "/workspace"

    # Safety checks.
    assert_read_only_dir /project
    assert_writable_dir /workspace

    # Lightweight validation of dataset location (guided-loop writes artifacts next to case_dir).
    # We do not modify arguments; we only inspect them to fail fast on unsafe mounts.
    orig_args=("$@")
    dataset_root=""
    for ((i=0; i<${#orig_args[@]}; i++)); do
      arg="${orig_args[$i]}"
      if [[ "$arg" == "--dataset-root" ]]; then
        if (( i + 1 < ${#orig_args[@]} )); then
          dataset_root="${orig_args[$((i+1))]}"
        fi
      elif [[ "$arg" == --dataset-root=* ]]; then
        dataset_root="${arg#*=}"
      fi
    done

    if [[ -n "$dataset_root" ]]; then
      resolved_dataset_root="$(resolve_path "$dataset_root")"
      if [[ -z "$resolved_dataset_root" ]]; then
        fail "--dataset-root path does not exist: $dataset_root"
      fi
      resolved_project="$(resolve_path /project)"
      if [[ -n "$resolved_project" && "$resolved_dataset_root" == "$resolved_project"* ]]; then
        fail "--dataset-root must not be under /project (which is read-only); mount it under /workspace"
      fi
    fi

    # Execute the outer-loop wrapper (which invokes guided-loop internally).
    # The wrapper is responsible for keeping STDOUT as unified diff only.
    exec python /app/scripts/fix.py "${orig_args[@]}"
    ;;

  *)
    fail "unknown subcommand: $cmd (expected: fix)"
    ;;
esac
