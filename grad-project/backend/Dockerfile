FROM python:3.9

# Install netcat (for the wait-for-it script)
RUN apt-get update && apt-get install -y netcat-traditional

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# This CMD is not used by docker-compose, but is good practice
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]