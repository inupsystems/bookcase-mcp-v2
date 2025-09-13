FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ src/
COPY tests/ tests/
COPY README.md .

# Create non-root user
RUN groupadd -r apiagent && useradd -r -g apiagent apiagent
RUN chown -R apiagent:apiagent /app
USER apiagent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["api-agent", "serve", "--host", "0.0.0.0", "--port", "8000"]
