FROM python:3.12-slim AS builder

WORKDIR /app/backend

COPY backend/requirements.txt .

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .

RUN npm run build


FROM python:3.12-slim AS runtime

WORKDIR /app/backend

COPY --from=builder /install /usr/local
COPY backend/ .

# Copy the built frontend into backend/static so Flask can serve it
COPY --from=frontend-builder /app/frontend/dist/ /app/backend/static/

RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# Threads matter here: each open SSE notification stream occupies one worker
# thread until it ends, so the pool is sized for concurrent streams plus normal
# requests rather than for CPU-bound work.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "16", "app:app"]