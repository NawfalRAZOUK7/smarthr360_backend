# How-To Guides

Quick, task-focused guides for common workflows.

## Local development (bare metal)

- `make install` then `cp .env.example .env` and adjust values.
- Start API: `make runserver` (http://localhost:8000).
- Create admin user: `python manage.py createsuperuser`.
- Run tests: `make test`; type checks: `make type`; lint: `make lint`.

## Local development (Docker dev profile)

- `make dev-up` to build and start with live reload at http://localhost:8000.
- Stop containers: `make dev-down`.
- Shell into web container: `docker compose exec web bash`.

## Production-like run (Docker prod profile)

- Ensure `.env` has production settings (`DEBUG=False`, HTTPS flags as needed).
- `make prod-up` builds, runs migrations, collects static, serves via gunicorn+nginx.
- Tail logs: `make prod-logs`; stop: `make prod-down`.

## Migrations

- Create migrations: `python manage.py makemigrations` (or `make makemigrations`).
- Apply migrations: `python manage.py migrate` (or `make migrate`).
- Check drift: `make makemigrations-check` and `make migrate-check`.

## Environment secrets

- Generate Django secret key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`.
- Never commit `.env`; keep `.env.example` updated when variables change.

## Resetting local data

- Stop the server, delete `db.sqlite3`, then run `python manage.py migrate` and recreate users.
- With Docker: `docker compose --profile dev down -v` to drop volumes, then `make dev-up`.

## API docs and Postman

- Swagger UI: http://localhost:8000/docs/
- ReDoc: http://localhost:8000/redoc/
- Postman: import `docs/api/SmartHR360_API.postman_collection.json` and follow `docs/api/POSTMAN_GUIDE.md`.

## Backups

- Create backup: see `create_postgres_backup.md`.
- Restore backup: see `restore_postgres_backup.md`.
