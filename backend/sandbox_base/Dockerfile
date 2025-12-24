FROM python:3.9-slim

WORKDIR /app

# 1. Install system tools (including dos2unix to fix Windows line endings)
RUN apt-get update && apt-get install -y dos2unix

# 2. Pre-install ALL requirements for SQLi and XSS challenges
# We list them manually here to ensure they are cached
RUN pip install --no-cache-dir \
    Flask==2.3.2 \
    mysql-connector-python==8.0.33 \
    requests \
    gunicorn \
    bleach

# This image is now ready to run scripts immediately