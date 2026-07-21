FROM python:3.11-slim AS base

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
COPY src ./src

# Install first so the normal and optional images are deterministic from uv.lock.
RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 10001 infoservice \
    && chown -R infoservice:infoservice /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER infoservice
ENTRYPOINT ["uv", "run", "--no-sync"]


FROM base AS runtime


FROM base AS runtime-full

USER root
RUN uv sync --frozen --no-dev --extra twitter --extra openbb \
    && chown -R infoservice:infoservice /app
USER infoservice
