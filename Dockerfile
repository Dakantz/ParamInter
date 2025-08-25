FROM ghcr.io/astral-sh/uv:python3.13-bookworm

WORKDIR /app
ADD pyproject.toml /app
ADD uv.lock /app
RUN uv sync

WORKDIR /app

ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/src

CMD [ "python", "-m", "uvicorn", "backend:app", "--port", "8000" ]