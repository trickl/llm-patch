#!/usr/bin/env bash
set -euo pipefail

# Publish llm-patch Docker images to Docker Hub.
#
# This is intentionally a thin deployment helper:
# - No automatic versioning (you provide the tag).
# - No registry hardcoding beyond docker.io (Docker Hub).
# - Uses env vars for auth.
#
# Authentication env vars (the script supports multiple common names):
#
# Preferred (simple):
#   DOCKERHUB_USERNAME   Docker Hub username
#   DOCKERHUB_TOKEN      Docker Hub access token (recommended) OR password
#   DOCKERHUB_REPO       Repository name, e.g. "trickl/llm-patch"
#
# Also supported (common CI names):
#   DOCKER_USERNAME
#   DOCKER_PASSWORD
#   DOCKER_HUB_PASSWORD
#   DOCKER_HUB_ACCESS_TOKEN
#   DOCKER_CONFIG_JSON   JSON payload for Docker CLI config (contains auths)
#   DOCKER_REGISTRY      Optional (default: docker.io)
#
# Usage:
#   DOCKERHUB_USERNAME=... DOCKERHUB_TOKEN=... DOCKERHUB_REPO=trickl/llm-patch \
#     ./docker/publish_dockerhub.sh --tag v0.1.0
#
# Options:
#   --tag TAG            Required. Tag to publish (e.g. v0.1.0, latest, dev)
#   --also TAG           Optional. Extra tag to apply+push (repeatable)
#   --local-image NAME   Optional. Local image name to publish (default: llm-patch:local)
#   --build              Optional. Build the local image before tagging (docker build -t <local> .)

fail() {
  echo "ERROR: $*" >&2
  exit 2
}

resolve_env() {
  # Print the first non-empty value from a list of env var names.
  local name
  for name in "$@"; do
    if [[ -n "${!name:-}" ]]; then
      printf '%s' "${!name}"
      return 0
    fi
  done
  return 1
}

tag=""
local_image="llm-patch:local"
extra_tags=()
do_build=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      tag="${2:-}"; shift 2 ;;
    --also)
      extra_tags+=("${2:-}"); shift 2 ;;
    --local-image)
      local_image="${2:-}"; shift 2 ;;
    --build)
      do_build=true; shift 1 ;;
    -h|--help)
      sed -n '1,120p' "$0"
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "$tag" ]] || fail "--tag is required"

registry="${DOCKER_REGISTRY:-docker.io}"
if [[ "$registry" != "docker.io" ]]; then
  fail "DOCKER_REGISTRY must be docker.io (got: $registry)"
fi

dockerhub_username="$(resolve_env DOCKERHUB_USERNAME DOCKER_USERNAME || true)"
dockerhub_token="$(resolve_env DOCKERHUB_TOKEN DOCKER_HUB_ACCESS_TOKEN DOCKERHUB_ACCESS_TOKEN DOCKER_HUB_PASSWORD DOCKER_PASSWORD || true)"

# Artifact id is fixed as llm-patch; default remote repo is <username>/llm-patch.
dockerhub_repo="${DOCKERHUB_REPO:-}"
if [[ -z "$dockerhub_repo" ]]; then
  [[ -n "$dockerhub_username" ]] || fail "missing DOCKERHUB_USERNAME/DOCKER_USERNAME (needed to default DOCKERHUB_REPO)"
  dockerhub_repo="${dockerhub_username}/llm-patch"
fi

# Auth strategy:
# - If DOCKER_CONFIG_JSON is provided, write it to a temporary Docker config dir.
# - Otherwise, login using username+token.
docker_config_tmp=""
if [[ -n "${DOCKER_CONFIG_JSON:-}" ]]; then
  docker_config_tmp="$(mktemp -d)"
  mkdir -p "$docker_config_tmp"
  printf '%s' "$DOCKER_CONFIG_JSON" >"$docker_config_tmp/config.json"
  export DOCKER_CONFIG="$docker_config_tmp"
else
  [[ -n "$dockerhub_username" ]] || fail "missing DOCKERHUB_USERNAME/DOCKER_USERNAME"
  [[ -n "$dockerhub_token" ]] || fail "missing token/password (set DOCKERHUB_TOKEN, DOCKER_HUB_ACCESS_TOKEN, DOCKER_PASSWORD, etc.)"
  printf '%s' "$dockerhub_token" | docker login -u "$dockerhub_username" --password-stdin
fi

if [[ "$do_build" == "true" ]]; then
  docker build -t "$local_image" .
fi

docker image inspect "$local_image" >/dev/null 2>&1 || fail "local image not found: $local_image"

remote_base="${registry}/${dockerhub_repo}"

# Tag+push primary tag.
docker tag "$local_image" "${remote_base}:${tag}"
docker push "${remote_base}:${tag}"

# Tag+push any additional tags.
for t in "${extra_tags[@]}"; do
  [[ -n "$t" ]] || continue
  docker tag "$local_image" "${remote_base}:${t}"
  docker push "${remote_base}:${t}"
done

# Logout is optional; keeping session can be convenient in CI runners.

if [[ -n "$docker_config_tmp" ]]; then
  rm -rf "$docker_config_tmp" || true
fi
