# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Layout:
# /project   -> mounted read-only (user code)
# /workspace -> writable scratch space
# /app       -> llm-patch source

WORKDIR /app

# Install runtime dependencies.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install llm-patch itself.
COPY pyproject.toml setup.py README.md /app/
COPY src /app/src
COPY scripts /app/scripts
RUN pip install --no-cache-dir /app

# Add Docker wrapper scripts.
COPY docker/entrypoint.sh /usr/local/bin/llm-patch-entrypoint
RUN chmod +x /usr/local/bin/llm-patch-entrypoint \
    && mkdir -p /project /workspace

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/llm-patch-entrypoint"]
