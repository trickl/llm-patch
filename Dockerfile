# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Layout:
# /project   -> mounted read-only (user code)
# /workspace -> writable scratch space
# /app       -> llm-patch source

WORKDIR /app

# Toolchains used by benchmark cases (guided-loop compile/test step).
# Keep this minimal; we only install what the wrapped workflow needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        nodejs \
        npm \
    && (apt-get install -y --no-install-recommends openjdk-21-jdk-headless \
        || apt-get install -y --no-install-recommends openjdk-17-jdk-headless) \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install llm-patch itself.
COPY pyproject.toml setup.py README.md /app/
COPY src /app/src
COPY scripts /app/scripts
RUN pip install --no-cache-dir /app

# Reviewer UI (for inspect mode)
COPY ui/reviewer-ui/package.json ui/reviewer-ui/package-lock.json /app/ui/reviewer-ui/
WORKDIR /app/ui/reviewer-ui
RUN npm ci
COPY ui/reviewer-ui /app/ui/reviewer-ui
RUN npm run build

# Add Docker wrapper scripts.
COPY docker/entrypoint.sh /usr/local/bin/llm-patch-entrypoint
RUN chmod +x /usr/local/bin/llm-patch-entrypoint \
    && mkdir -p /project /workspace

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/llm-patch-entrypoint"]

EXPOSE 4173
