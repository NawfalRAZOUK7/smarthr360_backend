# Restore a PostgreSQL Backup

Follow these steps to restore a database dump in different environments.

## Railway

- In the PostgreSQL plugin → **Backups**, select a snapshot and click **Restore**.
- To restore from a local dump: create a new database in Railway, get its connection string, then run:
  ```bash
  psql "$DATABASE_URL" < backup.sql
  ```
- Once validated, point the app service to that database URL.

## Render

- Create a new Render PostgreSQL instance (recommended to avoid overwriting prod).
- From your machine, set `DATABASE_URL` to the new instance connection string and run:
  ```bash
  psql "$DATABASE_URL" < backup.sql
  ```
- Update the service environment variable to the restored DB after verification.

## Docker/VPS

- If using Docker Compose Postgres:
  ```bash
  docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB < backup.sql
  ```
- For an external Postgres:
  ```bash
  psql -h <host> -U <user> -d <db> < backup.sql
  ```
- If schema needs a clean slate, drop and recreate the DB first (with caution), then restore.

## Post-restore validation

- Run migrations in case code has evolved: `python manage.py migrate` (or `docker compose exec web python manage.py migrate`).
- Sanity checks: can you log in? Are admin users present? Do critical tables have rows?
- Rotate any secrets if restoring into a new environment to avoid sharing JWT signing keys across envs.
