FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.22 /uv /uvx /bin/

RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /home/app app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN uv sync --frozen --no-dev
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
