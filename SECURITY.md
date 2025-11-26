# 🔒 Security & Production Hardening Guide

This document outlines the security measures implemented in SmartHR360 and provides a production deployment checklist.

---

## 🛡️ Security Features

### 1. Environment Variable Management

All sensitive configuration is stored in `.env` files (never committed to version control):

- **SECRET_KEY**: Django secret key for cryptographic signing
- **DATABASE_URL**: Database connection string
- **EMAIL_HOST_USER/PASSWORD**: Email credentials
- **JWT Settings**: Token lifetime and rotation settings
- **CORS Origins**: Allowed frontend origins

**Files:**

- `.env` - Your local/production configuration (gitignored)
- `.env.example` - Template for required variables

### 2. CORS Protection

Django CORS Headers configured to:

- Only allow specified origins (no wildcards in production)
- Support credentials (cookies, authorization headers)
- Whitelist necessary headers only

**Configuration:** `CORS_ALLOWED_ORIGINS` in `.env`

### 3. JWT Token Security

Enhanced JWT configuration:

- **Short-lived access tokens** (15 minutes default)
- **Token rotation** on refresh
- **Blacklist old tokens** after rotation
- **Automatic last login tracking**

**Configuration:** JWT settings in `.env`

### 4. Admin Panel Protection

Two-layer admin security:

1. **Enable/Disable flag**: `ADMIN_ENABLED=False` to completely disable admin
2. **IP Whitelist**: `ADMIN_IP_WHITELIST=192.168.1.1,10.0.0.5` to restrict access

**Middleware:** `AdminIPWhitelistMiddleware` enforces restrictions

### 5. HTTPS & Transport Security

Production security headers:

- `SECURE_SSL_REDIRECT`: Force HTTPS
- `SECURE_HSTS_SECONDS`: HTTP Strict Transport Security
- `SESSION_COOKIE_SECURE`: Only send cookies over HTTPS
- `CSRF_COOKIE_SECURE`: Only send CSRF tokens over HTTPS
- `X_FRAME_OPTIONS`: Prevent clickjacking
- `SECURE_BROWSER_XSS_FILTER`: XSS protection
- `SECURE_CONTENT_TYPE_NOSNIFF`: Prevent MIME sniffing

**Configuration:** Security flags in `.env`

### 6. Database Security

- Connection pooling with health checks
- Configurable via `DATABASE_URL` for easy environment switching
- Supports PostgreSQL, MySQL, SQLite

---

## 📋 Production Deployment Checklist

### Pre-Deployment

- [ ] Generate a new `SECRET_KEY` (never use the development key)
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain(s)
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Configure email service (SMTP credentials)
- [ ] Set `CORS_ALLOWED_ORIGINS` to your frontend domain(s)

### Security Configuration

- [ ] Set `SECURE_SSL_REDIRECT=True`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `CSRF_COOKIE_SECURE=True`
- [ ] Set `SECURE_HSTS_SECONDS=31536000` (1 year)
- [ ] Set `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- [ ] Set `SECURE_HSTS_PRELOAD=True`
- [ ] Configure `ADMIN_IP_WHITELIST` or disable admin with `ADMIN_ENABLED=False`

### JWT Configuration

- [ ] Review `JWT_ACCESS_TOKEN_LIFETIME` (15 minutes recommended)
- [ ] Review `JWT_REFRESH_TOKEN_LIFETIME` (7 days recommended)
- [ ] Ensure `JWT_ROTATE_REFRESH_TOKENS=True`
- [ ] Ensure `JWT_BLACKLIST_AFTER_ROTATION=True`

### Database & Static Files

- [ ] Run migrations: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Set up database backups
- [ ] Configure database connection pooling

### Server Setup

- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Set up reverse proxy (Nginx, Apache)
- [ ] Configure SSL/TLS certificates (Let's Encrypt)
- [ ] Set up firewall rules
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts

### Testing

- [ ] Test all API endpoints
- [ ] Verify CORS configuration with frontend
- [ ] Test JWT token refresh flow
- [ ] Verify admin panel restrictions
- [ ] Test email sending
- [ ] Run security scan (e.g., `python manage.py check --deploy`)

---

## 🔧 Environment Variables Reference

### Required

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### Email

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@smarthr360.com
```

### CORS

```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
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

### JWT

```bash
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True
```

### Admin

```bash
ADMIN_ENABLED=True
ADMIN_IP_WHITELIST=192.168.1.1,10.0.0.5
```

---

## 🚨 Security Best Practices

1. **Never commit `.env` files** - Always use `.env.example` as a template
2. **Rotate secrets regularly** - Change SECRET_KEY, database passwords periodically
3. **Use strong passwords** - For database, email, admin accounts
4. **Keep dependencies updated** - Run `pip list --outdated` regularly
5. **Monitor logs** - Set up centralized logging and alerts
6. **Limit database permissions** - Use separate DB users for different environments
7. **Enable rate limiting** - Add rate limiting for API endpoints (consider django-ratelimit)
8. **Regular backups** - Automate database and media file backups
9. **Security audits** - Run `python manage.py check --deploy` before each deployment
10. **Use environment-specific settings** - Separate development, staging, production configs

---

## 🔍 Django Security Check

Run Django's built-in security check before deployment:

```bash
python manage.py check --deploy
```

This will identify security issues and provide recommendations.

---

## 📞 Security Incident Response

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email security concerns to: security@smarthr360.com (update with your contact)
3. Include detailed description and steps to reproduce
4. Allow reasonable time for response before public disclosure

---

## 📚 Additional Resources

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Let's Encrypt](https://letsencrypt.org/) - Free SSL certificates

---

**Last Updated:** November 25, 2025
