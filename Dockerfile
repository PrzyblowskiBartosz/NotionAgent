FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

COPY main.py .
COPY app/ ./app/

CMD ["python", "main.py"]
