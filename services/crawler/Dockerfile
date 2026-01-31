FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY services/crawler /app/services/crawler

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "services.crawler.worker"]
