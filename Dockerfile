FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy files
COPY pyproject.toml README.md requirements.txt ./
COPY brain_core/ ./brain_core/
COPY run_server.py ./

# Install package with API dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[api]"

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "brain_core.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
