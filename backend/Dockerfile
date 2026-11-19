FROM ghcr.io/astral-sh/uv:0.13.9 AS uv
FROM python:3.12.16-slim

COPY --from=uv /uv /uvx /bin/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
ARG EVIDENCE_STORAGE_DIR=/var/lib/chainscope/evidences
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app app \
    && mkdir -p -- "$EVIDENCE_STORAGE_DIR" \
    && chown app:app "$EVIDENCE_STORAGE_DIR" \
    && chmod 0700 "$EVIDENCE_STORAGE_DIR"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini docker-entrypoint.sh ./
USER app
ENTRYPOINT ["/bin/sh", "/app/docker-entrypoint.sh"]
