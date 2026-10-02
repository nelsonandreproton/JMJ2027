FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY monitor/ ./monitor/

RUN useradd -u 1000 -m appuser \
    && mkdir -p /app/data /app/heartbeats \
    && chown appuser:appuser /app/data /app/heartbeats

USER appuser

CMD ["python", "-m", "monitor.main"]
