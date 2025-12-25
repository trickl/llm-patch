# Docker wrapper for llm-patch (sandbox envelope)

This Docker setup is intentionally **thin**: it does not change any llm-patch logic. It only provides a safe execution envelope with:

- `/project` mounted **read-only** (your project or repo)
- `/workspace` mounted **writable** (scratch space + artifacts)
- `/app` contains the llm-patch source

## Build

From the repository root:

- `docker build -t llm-patch:local .`

## Publish to Docker Hub (docker.io)

There is a small helper script at `docker/publish_dockerhub.sh` to tag and push an already-built local image.

### Authentication (recommended)

Create a Docker Hub **access token** and export:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `DOCKERHUB_REPO` (e.g. `trickl/llm-patch`). If omitted, it defaults to `<username>/llm-patch`.

The script also accepts common CI variable names:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD` or `DOCKER_HUB_PASSWORD` or `DOCKER_HUB_ACCESS_TOKEN`
- `DOCKER_CONFIG_JSON` (Docker CLI auth config JSON)
- `DOCKER_REGISTRY` (must be `docker.io`)

### Publish a tag

Example publishing `v0.1.0` from the locally built image `llm-patch:local`:

```bash
export DOCKERHUB_USERNAME=...
export DOCKERHUB_TOKEN=...
export DOCKERHUB_REPO=trickl/llm-patch

./docker/publish_dockerhub.sh --tag v0.1.0
```

Optionally publish additional tags (e.g. also tag the same image as `latest`):

```bash
./docker/publish_dockerhub.sh --tag v0.1.0 --also latest
```

If you want the script to build the local image first:

```bash
./docker/publish_dockerhub.sh --build --tag v0.1.0
```

## Run (guided-loop wrapper)

This image exposes a single subcommand:

- `fix ...`

Today, `fix` is an outer-loop wrapper that repeatedly runs the existing guided-loop runner:

- `/app/scripts/fix.py` (orchestrator)
- `/app/scripts/run_guided_loop.py` (existing guided-loop runner)

All arguments after `fix` are passed through **unchanged**.

### Example

Assuming you have a benchmark dataset on the host at `./benchmarks/generated`:

- Mount the repo (or any project) read-only at `/project`
- Mount a writable workspace at `/workspace`
- Mount the benchmark dataset somewhere writable (recommended: under `/workspace`), because `run_guided_loop.py` writes artifacts next to the case directory.

Example:

```bash
docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)":/project:ro \
  -v /tmp/llm-patch:/workspace \
  -v "$(pwd)/benchmarks/generated":/workspace/benchmarks/generated \
  -e OLLAMA_HOST="http://127.0.0.1:11434" \
  llm-patch:local \
  fix java-qwen2.5-coder:7b-52264466 \
    --dataset-root /workspace/benchmarks/generated \
    --model qwen2.5-coder:7b \
    --temperature 0 \
    --max-iterations 1 \
    --refine-iterations 3
```

Notes:

- On Linux, `--network host` is the simplest way for the container to reach an Ollama server running on the host at `127.0.0.1:11434`.
- `--user "$(id -u):$(id -g)"` prevents the container (default root user) from creating root-owned files in your mounted `/workspace` directory.

### Output behavior

- **STDOUT**: final unified diff (from the last guided-loop cycle).
- **STDERR**: wrapper validation errors + per-cycle runner output.

## Safety checks

At runtime the entrypoint fails fast if:

- `/project` does not exist
- `/workspace` does not exist
- `/project` is not mounted read-only
- `/workspace` is not writable
- `--dataset-root` resolves under `/project` (because `/project` is read-only)

## Notes on OpenAI-compatible backends

This repository’s current guided-loop runner uses the in-repo Ollama client (`OLLAMA_HOST`).

The Docker wrapper passes through `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_MODEL`, etc., but **does not introduce** an OpenAI client or any provider-specific logic.

If you need OpenAI/Ollama(OpenAI-protocol) support, it must already exist in the underlying llm-patch command being wrapped.
