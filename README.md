# Job Application Tracker

A full-featured Flask REST API for tracking job applications, with PostgreSQL, Redis caching, Celery background tasks, and Flower monitoring.

---

## Tech Stack

- **Flask** — REST API (Day 1–18 features)
- **PostgreSQL** — Relational database
- **Redis** — Caching & Celery broker/backend
- **Celery** — Async background task processing
- **Flower** — Celery monitoring UI
- **Gunicorn** — WSGI server (production)

---

## Docker / Environment Setup (Day 19)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Docker Compose v2 (`docker compose` command)

### Environment Configuration

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

> **Important**: `.env` is **never** committed to Git. It contains secrets.

Key environment variables:

| Variable | Description | Docker Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://job_tracker:...@postgres:5432/job_tracker` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `JWT_SECRET_KEY` | JWT signing secret | *(required — set a strong value)* |
| `POSTGRES_PASSWORD` | PostgreSQL password | `job_tracker_dev_only` |
| `ADZUNA_APP_ID` | Adzuna job search API ID | *(optional)* |
| `ADZUNA_APP_KEY` | Adzuna job search API key | *(optional)* |
| `MAIL_SERVER` | SMTP server | *(optional)* |
| `SCHEDULER_ENABLED` | Enable reminder scheduler | `false` in Docker |

---

## Running with Docker Compose

### Start all services

```bash
docker compose up -d
```

### Run database migrations (first time or after schema changes)

```bash
docker compose exec flask flask db upgrade
```

### Service URLs

| Service | URL |
|---|---|
| Flask API | http://localhost:5000 |
| Swagger UI | http://localhost:5000/swagger |
| Health check | http://localhost:5000/api/health |
| Flower (Celery) | http://localhost:5555 |

---

## Docker Architecture

```
Browser / API Client
        │
        ▼
     Flask (port 5000)
        │
   ┌────┴────┐
   │         │
PostgreSQL  Redis
(port 5432)  │
             │
          Celery Worker
             │
           Flower (port 5555)
```

All services communicate over the internal Docker Compose network. Docker service names (`postgres`, `redis`) are used — never `localhost`.

---

## Useful Docker Commands

```bash
# View all container statuses
docker compose ps

# View logs for a service
docker compose logs flask
docker compose logs celery
docker compose logs flower

# Follow live logs
docker compose logs -f flask

# Execute a command inside a container
docker compose exec flask python -c "..."

# Run database migrations
docker compose exec flask flask db upgrade

# Stop all services (preserves volumes/data)
docker compose down

# Stop and remove volumes (DESTROYS DATA)
docker compose down -v

# Rebuild and restart a specific service
docker compose up -d --build flask

# Rebuild all
docker compose up -d --build
```

---

## Running Tests

```bash
# Using local venv
python -m pytest tests/ -v

# Inside Docker
docker compose exec flask python -m pytest tests/ -v
```

---

## Security Notes

- `.env` is excluded from Git via `.gitignore`
- No secrets are hardcoded in `Dockerfile` or `docker-compose.yml`
- All secrets are supplied via environment variables
- Docker Compose uses `${VAR:-default}` syntax with safe defaults only for development
- Rotate credentials if they were ever committed or exposed
