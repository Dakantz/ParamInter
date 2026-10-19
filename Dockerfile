FROM ubuntu:26.10

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /uv
# Download the latest installer
ADD https://astral.sh/uv/install.sh uv-installer.sh

# Run the installer then remove it
RUN sh uv-installer.sh && rm uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app
ADD pyproject.toml /app
ADD uv.lock /app
ADD .python-version /app
RUN CMAKE_ARGS="-DGGML_CUDA=on  -DLLAVA_BUILD=off" uv sync


ADD ./backend /app/backend

# Sync the project into a new environment, asserting the lockfile is up to date
ENV PATH="/app/.venv/bin:$PATH"

ENV DATA_DIR=/app/data

CMD [ "python", "-m", "uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000" ]
