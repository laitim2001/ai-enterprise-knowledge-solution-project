# EKP backend container — W8 D1 F2.1 (per architecture.md §4.3 + §6.1 W8 deploy).
#
# Multi-stage build:
#   1. `builder` — installs uv + project deps into a virtualenv. Build context
#      stays out of the runtime image (smaller surface area, no uv binary).
#   2. `runtime` — slim python image, copies the venv, runs as non-root
#      `ekp` user, exposes /health for ACA liveness probe.
#
# H5 security: no secret bake-in; runtime reads .env / Azure Key Vault via
# Settings (W8 D2-D3 Managed Identity wire per W08 plan §2 F2.4).

# ----------------------------------------------------------------------------
# Stage 1: builder
# ----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# uv brings its own deterministic resolver and is faster than pip on cold install.
RUN pip install --no-cache-dir uv

WORKDIR /build

# Copy only the dependency manifests first so dep layer caches across code-only changes.
COPY pyproject.toml ./
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python .

# ----------------------------------------------------------------------------
# Stage 2: runtime
# ----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Non-root user — ACA + Kubernetes best practice. UID 10001 keeps off the host
# user namespace's typical [1000, 9999] range to avoid bind-mount UID clashes.
RUN groupadd --system --gid 10001 ekp && \
    useradd --system --uid 10001 --gid ekp --home /home/ekp --create-home ekp

# `curl` only — used by the HEALTHCHECK probe; no shell, no compilers, no
# package managers in the runtime image to keep the attack surface small.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=ekp:ekp . .

USER ekp
EXPOSE 8000

# ACA + standalone Docker liveness/readiness — same endpoint /health (W1 baseline
# in api/server.py:128). interval=30s, timeout=5s, start-period=15s allow for
# lifespan init (Azure SDK clients) to complete before first probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
