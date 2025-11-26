# 🔒 Security Features Quick Reference

## Overview

SmartHR360 implements comprehensive security measures for production deployment. This guide provides a quick reference for security features and configuration.

---

## 🎯 Quick Start

### Development Setup (5 minutes)

1. **Copy environment template:**

   ```bash
   cp .env.example .env
   ```

2. **Your `.env` is ready!** Default values work for development.

   - `DEBUG=True` - Shows detailed errors
   - `ALLOWED_HOSTS=localhost,127.0.0.1` - Local access only
   - `CORS_ALLOWED_ORIGINS=http://localhost:3000` - Frontend access

3. **Start developing:**
   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

### Production Setup (10 minutes)

1. **Generate SECRET_KEY:**

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Update `.env` for production:**

   ```bash
   SECRET_KEY=<generated-key>
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com
   DATABASE_URL=postgresql://user:pass@host:5432/db
   CORS_ALLOWED_ORIGINS=https://yourdomain.com

   # Enable HTTPS security
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   SECURE_HSTS_SECONDS=31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS=True
   SECURE_HSTS_PRELOAD=True
   ```

3. **Verify security:**
   ```bash
   python manage.py check --deploy
   ```

---

## 🛡️ Security Features Matrix

| Feature                     | Development | Production | Configuration                       |
| --------------------------- | ----------- | ---------- | ----------------------------------- |
| **Environment Variables**   | ✅          | ✅         | `.env` file                         |
| **Debug Mode**              | ON          | OFF        | `DEBUG=False`                       |
| **HTTPS Redirect**          | OFF         | ON         | `SECURE_SSL_REDIRECT=True`          |
| **Secure Cookies**          | OFF         | ON         | `SESSION_COOKIE_SECURE=True`        |
| **HSTS**                    | OFF         | ON         | `SECURE_HSTS_SECONDS=31536000`      |
| **CORS Protection**         | Lenient     | Strict     | `CORS_ALLOWED_ORIGINS`              |
| **JWT Rotation**            | ✅          | ✅         | `JWT_ROTATE_REFRESH_TOKENS=True`    |
| **Token Blacklist**         | ✅          | ✅         | `JWT_BLACKLIST_AFTER_ROTATION=True` |
| **Admin IP Whitelist**      | OFF         | Optional   | `ADMIN_IP_WHITELIST=192.168.1.1`    |
| **XSS Protection**          | ✅          | ✅         | `SECURE_BROWSER_XSS_FILTER=True`    |
| **Clickjacking Protection** | ✅          | ✅         | `X_FRAME_OPTIONS='DENY'`            |

---

## 🔐 JWT Token Security

### Token Lifetimes

| Token Type        | Default | Recommendation | Variable                     |
| ----------------- | ------- | -------------- | ---------------------------- |
| **Access Token**  | 15 min  | 15-30 min      | `JWT_ACCESS_TOKEN_LIFETIME`  |
| **Refresh Token** | 7 days  | 7-14 days      | `JWT_REFRESH_TOKEN_LIFETIME` |

### Token Rotation Flow

```
1. User logs in → Gets access + refresh token
2. Access token expires → Use refresh token
3. Refresh endpoint → New access + new refresh token
4. Old refresh token → Automatically blacklisted ✅
```

**Benefits:**

- ✅ Prevents token reuse attacks
- ✅ Limits exposure window
- ✅ Enables forced logout (blacklist)

### Configuration

```bash
# .env
JWT_ACCESS_TOKEN_LIFETIME=15        # Minutes
JWT_REFRESH_TOKEN_LIFETIME=7        # Days
JWT_ROTATE_REFRESH_TOKENS=True      # Enable rotation
JWT_BLACKLIST_AFTER_ROTATION=True   # Blacklist old tokens
```

---

## 🚪 Admin Panel Security

### Three Security Layers

1. **Enable/Disable Toggle**

   ```bash
   ADMIN_ENABLED=False  # Completely disable admin
   ```

2. **IP Whitelist**

   ```bash
   ADMIN_IP_WHITELIST=192.168.1.100,10.0.0.50
   ```

3. **Django Permissions** (built-in)
   - Staff status required
   - Superuser for full access

### Use Cases

| Scenario                         | Configuration                                             |
| -------------------------------- | --------------------------------------------------------- |
| **Development**                  | `ADMIN_ENABLED=True`, `ADMIN_IP_WHITELIST=` (empty)       |
| **Production - Allow All Staff** | `ADMIN_ENABLED=True`, `ADMIN_IP_WHITELIST=` (empty)       |
| **Production - Office Only**     | `ADMIN_ENABLED=True`, `ADMIN_IP_WHITELIST=your-office-ip` |
| **Production - Disabled**        | `ADMIN_ENABLED=False`                                     |

### Testing IP Whitelist

```bash
# Check your current IP
curl ifconfig.me

# Add to .env
ADMIN_IP_WHITELIST=<your-ip>

# Test admin access
curl -I http://localhost:8000/admin/
```

---

## 🌐 CORS Configuration

### Development (Permissive)

```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
```

### Production (Restrictive)

```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Common Issues

| Issue                 | Cause                    | Solution                                          |
| --------------------- | ------------------------ | ------------------------------------------------- |
| CORS error in browser | Origin not whitelisted   | Add frontend URL to `CORS_ALLOWED_ORIGINS`        |
| Credentials not sent  | Missing credentials flag | Already configured: `CORS_ALLOW_CREDENTIALS=True` |
| Preflight fails       | Missing headers          | Already configured with standard headers          |

---

## 🔒 HTTPS & Transport Security

### Security Headers Checklist

```bash
# .env (Production)
SECURE_SSL_REDIRECT=True              # Force HTTPS
SESSION_COOKIE_SECURE=True            # HTTPS-only sessions
CSRF_COOKIE_SECURE=True               # HTTPS-only CSRF
SECURE_HSTS_SECONDS=31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True   # Apply to subdomains
SECURE_HSTS_PRELOAD=True              # Enable preload
```

### What Each Setting Does

| Setting                          | Purpose                          | Production Value    |
| -------------------------------- | -------------------------------- | ------------------- |
| `SECURE_SSL_REDIRECT`            | Redirect HTTP → HTTPS            | `True`              |
| `SESSION_COOKIE_SECURE`          | Only send cookies over HTTPS     | `True`              |
| `CSRF_COOKIE_SECURE`             | Only send CSRF tokens over HTTPS | `True`              |
| `SECURE_HSTS_SECONDS`            | Browser remembers to use HTTPS   | `31536000` (1 year) |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | Apply HSTS to subdomains         | `True`              |
| `SECURE_HSTS_PRELOAD`            | Submit to HSTS preload list      | `True`              |

**⚠️ Warning:** Don't enable HSTS in development or before HTTPS is working!

---

## 📊 Security Verification Commands

### Basic System Check

```bash
python manage.py check
```

### Deployment Security Check

```bash
python manage.py check --deploy
```

### Test Email Configuration

```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Testing', 'from@example.com', ['to@example.com'])
```

### Generate OpenAPI Schema

```bash
python manage.py spectacular --color --file schema.yml
```

### Check Installed Packages

```bash
pip list
```

---

## 🚨 Common Security Mistakes

| ❌ Don't                       | ✅ Do                               |
| ------------------------------ | ----------------------------------- |
| Commit `.env` to git           | Add `.env` to `.gitignore`          |
| Use `DEBUG=True` in production | Set `DEBUG=False`                   |
| Allow all CORS origins (`*`)   | Whitelist specific origins          |
| Use default `SECRET_KEY`       | Generate unique key per environment |
| Disable CSRF protection        | Keep it enabled                     |
| Use short token lifetimes only | Enable token rotation + blacklist   |
| Ignore security warnings       | Run `check --deploy` before deploy  |

---

## 📚 File Reference

| File                               | Purpose                                      |
| ---------------------------------- | -------------------------------------------- |
| `.env`                             | Your local configuration (gitignored)        |
| `.env.example`                     | Template with all variables                  |
| `.gitignore`                       | Prevents committing sensitive files          |
| `SECURITY.md`                      | Complete security guide (30+ page checklist) |
| `STEP_14_IMPLEMENTATION.md`        | Implementation details                       |
| `smarthr360_backend/middleware.py` | Admin IP whitelist middleware                |
| `smarthr360_backend/settings.py`   | Django configuration (uses `.env`)           |

---

## 🆘 Troubleshooting

### "SECRET_KEY not found"

```bash
# Make sure .env exists
cp .env.example .env

# Verify SECRET_KEY is set
grep SECRET_KEY .env
```

### "CORS error in browser"

```bash
# Check CORS configuration
grep CORS_ALLOWED_ORIGINS .env

# Add your frontend URL
echo "CORS_ALLOWED_ORIGINS=http://localhost:3000" >> .env
```

### "Admin access denied"

```bash
# Check IP whitelist
grep ADMIN_IP_WHITELIST .env

# Find your IP
curl ifconfig.me

# Update whitelist
# ADMIN_IP_WHITELIST=<your-ip>
```

### "Database connection failed"

```bash
# Check DATABASE_URL
grep DATABASE_URL .env

# For SQLite (development)
DATABASE_URL=sqlite:///db.sqlite3

# For PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

---

## 🎓 Learning Resources

- **Django Security:** https://docs.djangoproject.com/en/stable/topics/security/
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **JWT Best Practices:** https://tools.ietf.org/html/rfc8725
- **CORS Explained:** https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS

---

**Need Help?**

- See `SECURITY.md` for complete production checklist
- See `STEP_14_IMPLEMENTATION.md` for implementation details
- Run `python manage.py check --deploy` for security recommendations

**Last Updated:** November 25, 2025
