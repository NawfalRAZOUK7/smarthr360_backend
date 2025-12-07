# Create a PostgreSQL Backup

Use these steps to capture a database backup across deployment targets.

## Railway

- Open the Railway project → PostgreSQL plugin → **Backups** → click **Create Backup**. Railway stores snapshots for you.
- To export locally: open the database → **Connect** → copy the `psql` connection string → run `pg_dump "$DATABASE_URL" > backup.sql` from your machine.

## Render

- From your Render PostgreSQL instance: go to **Connections** and copy the external connection string.
- Run `pg_dump "$DATABASE_URL" > backup.sql` locally. Set `DATABASE_URL` to the copied string.
- Store the `backup.sql` in a safe location (not in git).

## Docker/VPS

- SSH to the host where PostgreSQL runs.
- If using Docker with the bundled Postgres:
  ```bash
  docker compose exec db pg_dump -U $POSTGRES_USER -d $POSTGRES_DB > backup.sql
  ```
- If using a managed Postgres (outside Compose), run from the host that can reach it:
  ```bash
  pg_dump -h <host> -U <user> -d <db> > backup.sql
  ```

## Tips

- Compress if large: `pg_dump ... | gzip > backup.sql.gz`.
- Do not commit backups to the repo.
- Automate on VPS via cron + `pg_dump` + upload to object storage.
