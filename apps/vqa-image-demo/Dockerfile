FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# curl: HEALTHCHECK용
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the app directory
COPY . .

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8002/internal/ai/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
