# ============================================================================
# Multi-stage Dockerfile for Backend Service
# ============================================================================
# Features:
# - Multi-stage build for smaller final image
# - Non-root user for security
# - Layer caching optimization
# - Health check support
# - Production-ready configuration

# ============================================================================
# Stage 1: Python Dependencies Builder
# ============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG POETRY_VERSION=1.7.1

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install dependencies
RUN poetry install --no-root --only main && rm -rf $POETRY_CACHE_DIR

# ============================================================================
# Stage 2: Production Image
# ============================================================================
FROM python:3.11-slim as runtime

# Labels for image metadata
LABEL maintainer="Lambda.hu Development Team"
LABEL version="1.0.0"
LABEL description="Lambda.hu Backend Service"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PORT=8000

# Create necessary directories with correct permissions
RUN mkdir -p /app/logs /app/data /app/downloads && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# Stage 3: Development Image (optional, for development use)
# ============================================================================
FROM runtime as development

# Switch back to root for installing dev tools
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy development dependencies
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Install development dependencies
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && \
    poetry install --no-root && \
    rm -rf ~/.cache/pip

# Switch back to non-root user
USER appuser

# Development command with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]