# Production Dockerfile for ResearchPilot FastAPI Backend
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for compiling C extensions (ChromaDB / SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications first to leverage Docker caching
COPY pyproject.toml requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy application source code
COPY src/ ./src/
RUN mkdir -p ./data

# Install package in editable mode
RUN pip install --no-cache-dir -e .


# Expose backend port
EXPOSE 8000

# Run FastAPI backend with Uvicorn on 0.0.0.0 and PORT environment variable
CMD ["sh", "-c", "uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
