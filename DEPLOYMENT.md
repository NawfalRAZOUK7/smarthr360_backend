# SmartHR360 Backend - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the SmartHR360 Backend to three production platforms:

1. **Railway** - Fastest deployment with automatic HTTPS
2. **Render** - Free tier available with PostgreSQL
3. **VPS/Docker** - Full control with Docker + Nginx + PostgreSQL

---

## Platform Comparison

| Feature        | Railway             | Render              | VPS/Docker             |
| -------------- | ------------------- | ------------------- | ---------------------- |
| **Setup Time** | 5-10 minutes        | 10-15 minutes       | 30-60 minutes          |
| **Free Tier**  | $5/month credit     | Yes (limited)       | Depends on provider    |
| **HTTPS**      | Automatic           | Automatic           | Manual (Let's Encrypt) |
| **Database**   | PostgreSQL included | PostgreSQL included | Self-hosted            |
| **Scaling**    | Easy                | Easy                | Manual                 |
| **Control**    | Limited             | Limited             | Full                   |
| **Best For**   | Quick deployment    | Free hosting        | Production apps        |

---

## Prerequisites

All platforms require:

- Git repository with your code
- `.env.example` file configured
- `requirements.txt` with all dependencies

Platform-specific files (already created):

- **Railway**: `Procfile`, `railway.json`, `nixpacks.toml`
- **Render**: `render.yaml`
- **VPS**: `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `.dockerignore`

---

## Quick Start by Platform

### Railway (Recommended for Speed)

**See: [DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md) for detailed instructions**

1. Push code to GitHub
2. Visit [railway.app](https://railway.app)
3. Connect GitHub repo
4. Add PostgreSQL database
5. Configure environment variables
6. Deploy automatically

**Deployment time: ~5 minutes**

---

### Render (Best for Free Tier)

**See: [DEPLOY_RENDER.md](./DEPLOY_RENDER.md) for detailed instructions**

1. Push code to GitHub
2. Visit [render.com](https://render.com)
3. Create new Web Service from repo
4. Render reads `render.yaml` automatically
5. Configure environment variables
6. Deploy

**Deployment time: ~10 minutes**

---

### VPS/Docker (Best for Production)

**See: [DEPLOY_DOCKER.md](./DEPLOY_DOCKER.md) for detailed instructions**

1. Provision VPS (DigitalOcean, AWS EC2, etc.)
2. Install Docker and Docker Compose
3. Clone repository
4. Configure `.env` file
5. Run `docker-compose up -d`
6. Configure SSL with Let's Encrypt

**Deployment time: ~30-60 minutes**

---

## Environment Variables

All platforms require these essential environment variables:

### Core Settings

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### CORS Configuration

```bash
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

### JWT Settings

```bash
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True
```

### Security (Production)

```bash
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Email Configuration

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@smarthr360.com
```

### Admin Panel

```bash
ADMIN_ENABLED=True
ADMIN_IP_WHITELIST=203.0.113.0,198.51.100.0
```

**Tip**: Copy `.env.example` and fill in your production values.

---

## Post-Deployment Checklist

After deploying to any platform:

- [ ] **Run migrations**: `python manage.py migrate`
- [ ] **Create superuser**: `python manage.py createsuperuser`
- [ ] **Collect static files**: `python manage.py collectstatic --no-input`
- [ ] **Test API endpoints**: Visit `/api/schema/swagger-ui/`
- [ ] **Test authentication**: Login, logout, token refresh
- [ ] **Verify CORS**: Test from your frontend domain
- [ ] **Check logs**: Monitor for errors
- [ ] **Configure domain**: Point DNS to your deployment
- [ ] **Enable HTTPS**: Ensure SSL certificate is active
- [ ] **Set up monitoring**: Configure error tracking (Sentry, etc.)
- [ ] **Backup database**: Set up automated backups

---

## Database Migrations

### Automatic (Railway/Render)

Migrations run automatically via:

- **Railway**: `release` command in `Procfile`
- **Render**: `preDeployCommand` in `render.yaml`

### Manual (VPS/Docker)

```bash
# Enter container
docker-compose exec web bash

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Exit container
exit
```

---

## Static Files

Static files are served by **WhiteNoise** (no separate static server needed):

1. **Collect static files**: `python manage.py collectstatic --no-input`
2. **WhiteNoise serves them** automatically in production
3. **Compression enabled** for faster loading

Optional: Use AWS S3 or Backblaze B2 for static/media files (see settings.py).

---

## Monitoring & Logs

### Railway

```bash
railway logs
```

Or view in Railway dashboard.

### Render

View logs in Render dashboard (Logs tab).

### VPS/Docker

```bash
# Web container logs
docker-compose logs -f web

# Nginx logs
docker-compose logs -f nginx

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f
```

---

## Scaling

### Railway

- Vertical scaling: Upgrade plan
- Horizontal scaling: Add replicas in dashboard

### Render

- Vertical scaling: Upgrade instance type
- Horizontal scaling: Increase instance count

### VPS/Docker

- Vertical scaling: Upgrade VPS
- Horizontal scaling:

  ```bash
  # Increase gunicorn workers in docker-compose.yml
  --workers 8  # (2-4 x CPU cores)

  # Scale web containers
  docker-compose up -d --scale web=3
  ```

---

## Troubleshooting

### Common Issues

**1. "DisallowedHost" error**

- Add your domain to `ALLOWED_HOSTS` in `.env`

**2. "Static files not found"**

- Run `python manage.py collectstatic --no-input`
- Verify `STATIC_ROOT` in settings.py

**3. "CORS errors"**

- Add frontend URL to `CORS_ALLOWED_ORIGINS`
- Ensure `corsheaders.middleware.CorsMiddleware` is in MIDDLEWARE

**4. "Database connection failed"**

- Verify `DATABASE_URL` format: `postgresql://user:pass@host:5432/dbname`
- Check database is running

**5. "Admin panel not accessible"**

- Check `ADMIN_ENABLED=True`
- Verify your IP in `ADMIN_IP_WHITELIST`

**6. "502 Bad Gateway" (Docker)**

- Check if web container is running: `docker-compose ps`
- View logs: `docker-compose logs web`

---

## Security Best Practices

1. **Never commit `.env` file** - Always use `.env.example` as template
2. **Use strong SECRET_KEY** - Generate with `python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
3. **Enable HTTPS** - Set all SECURE\_\* settings to True in production
4. **Restrict admin access** - Use IP whitelist or VPN
5. **Regular backups** - Automated database backups
6. **Monitor logs** - Set up error tracking (Sentry, etc.)
7. **Update dependencies** - Regular security updates

---

## Next Steps

After successful deployment:

1. **Configure custom domain** - Point DNS to your deployment
2. **Set up CI/CD** - Automated deployments on git push
3. **Add monitoring** - Sentry, New Relic, DataDog
4. **Database backups** - Automated daily backups
5. **Load testing** - Test with expected traffic
6. **Documentation** - Document your deployment process

---

## Support & Resources

- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Railway Docs**: https://docs.railway.app/
- **Render Docs**: https://render.com/docs
- **Docker Docs**: https://docs.docker.com/
- **Let's Encrypt**: https://letsencrypt.org/

For platform-specific guides, see:

- [DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md)
- [DEPLOY_RENDER.md](./DEPLOY_RENDER.md)
- [DEPLOY_DOCKER.md](./DEPLOY_DOCKER.md)
