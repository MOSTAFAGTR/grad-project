FROM python:3.9

# Install netcat (for the wait-for-it script) and git (repository cloning)
RUN apt-get update && apt-get install -y netcat-traditional git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    (pip install semgrep --break-system-packages 2>/dev/null || pip install semgrep || true)

COPY . .

# This CMD is not used by docker-compose, but is good practice
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]