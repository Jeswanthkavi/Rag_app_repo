FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential etc. if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose port (default 8000, overridable by $PORT)
EXPOSE 8000

ENV PORT=8000
ENV PYTHONPATH=/app

CMD ["python", "run_server.py"]

