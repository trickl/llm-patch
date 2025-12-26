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
  fail "missing subcommand (expected: fix | inspect)"
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

  inspect)
    shift

    # Required mounts.
    require_dir /workspace "/workspace"
    assert_writable_dir /workspace

    dataset_root=""
    port="4173"
    orig_args=("$@")
    for ((i=0; i<${#orig_args[@]}; i++)); do
      arg="${orig_args[$i]}"
      if [[ "$arg" == "--dataset-root" ]]; then
        if (( i + 1 < ${#orig_args[@]} )); then
          dataset_root="${orig_args[$((i+1))]}"
        fi
      elif [[ "$arg" == --dataset-root=* ]]; then
        dataset_root="${arg#*=}"
      elif [[ "$arg" == "--port" ]]; then
        if (( i + 1 < ${#orig_args[@]} )); then
          port="${orig_args[$((i+1))]}"
        fi
      elif [[ "$arg" == --port=* ]]; then
        port="${arg#*=}"
      fi
    done

    if [[ -z "$dataset_root" ]]; then
      # Prefer explicit pointer written by the fix wrapper.
      if [[ -f /workspace/llm-patch/last_dataset_root.txt ]]; then
        dataset_root="$(cat /workspace/llm-patch/last_dataset_root.txt 2>/dev/null || true)"
      fi
    fi

    if [[ -z "$dataset_root" ]]; then
      # Fall back to the newest preserved scratch dataset.
      dataset_root="$(ls -td /workspace/llm-patch/fix-*/dataset 2>/dev/null | head -n 1 || true)"
    fi

    if [[ -z "$dataset_root" ]]; then
      fail "could not find a recent run to inspect. Run 'fix ... --keep-workdir' first, or pass --dataset-root"
    fi

    resolved_dataset_root="$(resolve_path "$dataset_root")"
    if [[ -z "$resolved_dataset_root" || ! -d "$resolved_dataset_root" ]]; then
      fail "dataset root does not exist: $dataset_root"
    fi

    export REVIEWER_DATASET_ROOT="$resolved_dataset_root"
    export PORT="$port"

    # Run the reviewer UI server.
    # Note: this subcommand is interactive; it may log to STDOUT.
    cd /app/ui/reviewer-ui
    exec ./node_modules/.bin/tsx server/index.ts
    ;;

  *)
    fail "unknown subcommand: $cmd (expected: fix | inspect)"
    ;;
esac
