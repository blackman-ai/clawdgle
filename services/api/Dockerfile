FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY services/api /app/services/api

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
