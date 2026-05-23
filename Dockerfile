FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    find /ms-playwright -mindepth 1 -maxdepth 1 -type d ! -name 'chromium*' -exec rm -rf {} +

COPY main.py .
COPY app/ ./app/

CMD ["python", "main.py"]
