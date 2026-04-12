# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run database migrations and start application
CMD bash -c "
    echo 'Waiting for database...' &&
    sleep 10 &&
    echo 'Running database migrations...' &&
    alembic upgrade head &&
    echo 'Starting FastAPI application...' &&
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"
