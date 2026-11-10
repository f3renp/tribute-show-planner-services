# syntax=docker/dockerfile:1
# Image for the shows service. Build context: services/shows
FROM python:3.12-slim

# DATA_DIR is where the SQLite file lives, outside /app so a volume can be
# mounted there. PORT is read by main.py; 8000 is only the default.
ENV PORT=8000 \
    DATA_DIR=/data \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Unprivileged user. It owns /data (to write the database) but not the code.
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /data \
 && chown appuser:appuser /data

# Dependencies first: editing code does not reinstall packages (layer cache).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Only the service code. Never COPY . . (tests, .git, *.db stay out).
COPY app/ ./

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ['PORT'], timeout=2)"]

# main.py binds 0.0.0.0 and reads PORT.
CMD ["python", "main.py"]