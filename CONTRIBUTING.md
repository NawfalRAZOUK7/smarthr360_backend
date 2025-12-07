# Contributing

Thanks for helping improve SmartHR360! This guide covers local setup, quality checks, and the Docker workflows used in CI/production.

## Prerequisites
- Python 3.12+
- Docker + Docker Compose (for container flows)
- A virtualenv (`python -m venv .venv && source .venv/bin/activate`)

## Local setup
1) Install deps:
```bash
make install
```
2) Copy env template and adjust secrets/DB:
```bash
cp .env.example .env
```
3) (Optional) ensure the settings module you want is set; defaults to local:
```bash
export DJANGO_SETTINGS_MODULE=smarthr360_backend.config.local
```

## Quality + tests
- Lint: `make lint` (ruff)
- Type check: `make type` (mypy, ignores missing imports by default)
- Migration drift: `make makemigrations-check`
- Migrate (and verify): `make migrate && make migrate-check`
- Tests: `make test`
- Coverage: `make coverage`

## Run locally
- Dev server: `make runserver` (uses local settings)
- Django shell: `make shell`

## Docker profiles
- Dev (runserver + bind mount):
```bash
make dev-up    # docker compose --profile dev up --build
make dev-down
```
- Prod (gunicorn + collectstatic + nginx):
```bash
make prod-up   # docker compose --profile prod up --build -d
make prod-logs
make prod-down
```
- SSL optionality: nginx maps 80/443 by default; if you don’t have certs yet, remove/comment the `443:443` port and `./ssl` volume in `docker-compose.yml` until you add certs.

## CI expectations
CI runs migration checks, Django deploy checks, tests with coverage, plus ruff and mypy. Please run `make makemigrations-check`, `make migrate-check`, `make lint`, `make type`, and `make test` before opening a PR.

## Git hygiene
- Keep changes focused and small; include tests when possible.
- Avoid committing `.venv`, `db.sqlite3`, or other generated assets; `.gitignore` already covers common cases.
