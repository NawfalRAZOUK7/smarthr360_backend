# Infrastructure Notes

A concise map of how the backend is packaged and deployed.

## Components

- **Application**: Django REST API served by gunicorn (prod) or runserver (dev).
- **Gateway**: Nginx for SSL termination, static files, and proxy to gunicorn (Docker prod).
- **Database**: SQLite for dev; PostgreSQL for production platforms (Railway, Render, VPS).
- **Workers**: None yet (no Celery); add a worker service if background jobs are introduced.

## Deployment targets

- **Docker/VPS**: `docker-compose.yml` with profiles `dev` and `prod`; Nginx config in `nginx.conf`; certs mounted from `./ssl`.
- **Railway**: `Procfile`, `railway.json`, `nixpacks.toml`; auto-migrations via `release` command.
- **Render**: `render.yaml` blueprint; pre-deploy migrations configured.

## Ports and networking

- App listens on 8000 internally; Nginx serves 80/443 in prod profile.
- Health checks: use `/api/health/` when available; otherwise root `/` returns 200.

## Config sources

- Environment variables via `.env`; template in `.env.example`.
- Django settings: `smarthr360_backend/settings.py` pulls from env.
- Logging: default Django logging to console; rely on platform log capture.

## Build artifacts

- **Dockerfile** builds the app image; `docker-compose.yml` orchestrates services.
- Static files collected into `/app/staticfiles` during prod startup.

## Backups and data

- Production should enable automated PostgreSQL backups (platform-provided on Railway/Render, manual on VPS).
- For VPS, snapshot volumes or use `pg_dump` cron.
