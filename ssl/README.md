# SSL Certificates

Use this folder to store TLS certificates when running the prod Docker profile with Nginx.

## Expected files

- `fullchain.pem` — certificate chain
- `privkey.pem` — private key

These paths are referenced by `nginx.conf`:

```
ssl_certificate /etc/nginx/ssl/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/privkey.pem;
```

## Enabling SSL in Docker

1. Place `fullchain.pem` and `privkey.pem` in `./ssl/` (this folder).
2. Ensure `docker-compose.yml` keeps the `443:443` port mapping and the `./ssl:/etc/nginx/ssl:ro` volume on the `nginx` service.
3. Run `make prod-up` (or `docker compose --profile prod up --build -d`).
4. Verify: `curl -I https://your-domain` should return 200/301.

## Obtaining certificates (options)

- **Let’s Encrypt on the host**: Use `certbot certonly --standalone -d your-domain` on the VPS, then copy the issued `fullchain.pem` and `privkey.pem` into `ssl/`.
- **Let’s Encrypt via nginx challenge**: Temporarily open port 80, map `/.well-known/acme-challenge` in nginx, run certbot, then place the certs here.
- **Self-signed for testing** (not for production):
  ```bash
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout privkey.pem -out fullchain.pem \
    -subj "/CN=localhost"
  ```
  Place both files in `ssl/` and trust the cert in your browser.

## Disabling SSL temporarily

- Comment out the `443:443` mapping and `./ssl` volume in `docker-compose.yml` if you are not ready for HTTPS.
- Keep `SECURE_SSL_REDIRECT=False` in `.env` for local/dev to avoid redirect loops.
