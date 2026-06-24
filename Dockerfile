# AITest Platform v1.0
# Multi-stage build: slim runtime, no dev deps in final image.

# AITest Platform v1.0

FROM python:3.12-slim

LABEL org.aitest.version="1.0.0"
LABEL org.aitest.description="AI Test Automation Platform"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps from pyproject.toml
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn pydantic sqlalchemy chromadb \
    langgraph anthropic openai pyyaml python-dotenv httpx

# Copy platform source
COPY aitest/ aitest/
COPY governance/ governance/
COPY docs/ docs/

# Runtime config
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "aitest.server.main"]
