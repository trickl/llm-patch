# Docker wrapper for llm-patch (sandbox envelope)

This Docker setup is intentionally **thin**: it does not change any llm-patch logic. It only provides a safe execution envelope with:

- `/project` mounted **read-only** (your project or repo)
- `/workspace` mounted **writable** (scratch space + artifacts)
- `/app` contains the llm-patch source

## Build

From the repository root:

- `docker build -t llm-patch:local .`

## Pull (recommended)

Most users should pull the prebuilt image from Docker Hub:

```bash
docker pull docker.io/trickl/llm-patch:latest
```

For reproducible runs, pin to a version tag:

```bash
docker pull docker.io/trickl/llm-patch:0.1.0
```

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

This image exposes two subcommands:

- `fix ...`
- `inspect ...`

Today, `fix` is an outer-loop wrapper that repeatedly runs the existing guided-loop runner:

- `/app/scripts/fix.py` (orchestrator)
- `/app/scripts/run_guided_loop.py` (existing guided-loop runner)

All arguments after `fix` are passed through **unchanged**.

`fix` takes a required `<target>` positional argument. `<target>` can be either:

- a single source file path (or just a filename under `/project` in Docker), or
- a benchmark run directory under `--dataset-root` (advanced / benchmarking only).

### Example

Assuming you have a benchmark dataset on the host at `./benchmarks/generated`:

- Mount the repo (or any project) read-only at `/project`
- Mount a writable workspace at `/workspace`
- Mount the benchmark dataset somewhere writable (recommended: under `/workspace`), because `run_guided_loop.py` writes artifacts next to the benchmark directory.

Example:

```bash
docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)":/project:ro \
  -v /tmp/llm-patch:/workspace \
  -v "$(pwd)/benchmarks/generated":/workspace/benchmarks/generated \
  -e OLLAMA_HOST="http://127.0.0.1:11434" \
  docker.io/trickl/llm-patch:latest \
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
- `--outer-cycles` is optional. It caps how many outer guided-loop cycles to attempt; the run still stops early if it stops making progress.

### Production-style single file example

If you want to run against your own file, mount your repo at `/project:ro` and pass a filename:

```bash
docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)":/project:ro \
  -v /tmp/llm-patch:/workspace \
  -e OLLAMA_HOST="http://127.0.0.1:11434" \
  docker.io/trickl/llm-patch:latest \
  fix MyFile.java --keep-workdir
```

If the tool can’t infer the compile/check command for your file type, provide one:

```bash
docker.io/trickl/llm-patch:latest fix MyFile.java \
  --compile "javac MyFile.java" \
  --keep-workdir
```

### Output behavior

- **STDOUT**: final unified diff (from the last guided-loop cycle).
- **STDERR**: wrapper validation errors + per-cycle runner output.

## Run (inspect mode / reviewer UI)

`inspect` starts the built-in reviewer UI web service inside the container and points it at the most recent preserved `fix` run.

### Basic flow

1) Run `fix` **with** `--keep-workdir` so artifacts are preserved under `/workspace/llm-patch/fix-*/dataset`.

2) Run `inspect` using the **same** `/workspace` mount and publish the UI port:

```bash
docker run --rm \
  -p 4173:4173 \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)":/project:ro \
  -v /tmp/llm-patch:/workspace \
  docker.io/trickl/llm-patch:latest \
  inspect
```

Then open: `http://127.0.0.1:4173`

Tip: if you built locally, you can replace `docker.io/trickl/llm-patch:latest` with `llm-patch:local`.

### What you should see

The UI will list multiple entries for the run, including one per outer cycle:

- `guided-loop-cycle-001`
- `guided-loop-cycle-002`
- ...

These are created by the `fix` wrapper as per-cycle snapshots so you can review every cycle.

### Options

- `inspect --port 4173` (default: 4173)
- `inspect --dataset-root /some/path` (override auto-discovery)

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
