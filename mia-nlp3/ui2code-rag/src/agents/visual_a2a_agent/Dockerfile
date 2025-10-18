# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Default port
ENV PORT=10000

# Python
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=2.1.2

# Use bash as the default shell
SHELL ["/bin/bash", "-c"]

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Build app
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-ansi --no-root
COPY . /app

# Permisos
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
RUN chmod +x /app/entrypoint.sh
USER root

# App
EXPOSE ${PORT}
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://0.0.0.0:${PORT}/.well-known/agent-card.json || exit 1
ENTRYPOINT ["/app/entrypoint.sh"]
