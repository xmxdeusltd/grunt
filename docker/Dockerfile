# Use multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Final stage
FROM python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ src/
COPY config.yaml ./

# Create non-root user
RUN useradd -m -u 1000 bot
USER bot

# Run the application
CMD ["python", "-m", "src.main", "config.yaml"] 