# syntax=docker/dockerfile:1
# Convenience Dockerfile. The repo-root Dockerfile is the canonical build target.
# You can also build with:
#   docker build -f docker/Dockerfile -t llm-patch:local .

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY pyproject.toml setup.py README.md /app/
COPY src /app/src
COPY scripts /app/scripts
RUN pip install --no-cache-dir /app

COPY docker/entrypoint.sh /usr/local/bin/llm-patch-entrypoint
RUN chmod +x /usr/local/bin/llm-patch-entrypoint \
    && mkdir -p /project /workspace

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/llm-patch-entrypoint"]
