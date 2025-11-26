# Deploy to Render - Quick Guide

## Overview

Render offers a generous free tier with automatic HTTPS, PostgreSQL database, and infrastructure-as-code via `render.yaml`.

**Deployment time: ~10-15 minutes**

---

## Prerequisites

- GitHub/GitLab account
- Render account (sign up at [render.com](https://render.com))
- Code pushed to repository
- Environment variables ready (see `.env.example`)

---

## Step 1: Push Code to GitHub/GitLab

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - ready for Render deployment"

# Add remote and push
git remote add origin https://github.com/yourusername/smarthr360_backend.git
git push -u origin main
```

---

## Step 2: Create Render Account & Connect Repository

1. Go to [render.com](https://render.com)
2. Click **"Get Started"**
3. Sign up with GitHub/GitLab
4. Authorize Render to access your repositories

---

## Step 3: Deploy from render.yaml (Recommended)

Render automatically detects `render.yaml` in your repository.

1. Go to Render Dashboard
2. Click **"New +"** → **"Blueprint"**
3. Connect your repository
4. Select `smarthr360_backend` repository
5. Render reads `render.yaml` configuration
6. Click **"Apply"**

Render creates:

- **Web Service**: Django application with gunicorn
- **PostgreSQL Database**: Managed database
- **Environment Variables**: From render.yaml

---

## Step 4: Configure Environment Variables

After blueprint creation, add these variables:

1. Go to your **Web Service**
2. Click **"Environment"** tab
3. Add each variable:

### Required Variables

```bash
# Core Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=False
# ALLOWED_HOSTS is set automatically by Render

# Database
# DATABASE_URL is set automatically by Render

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://your-frontend.com

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True

# Security (Production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@smarthr360.com

# Admin Panel
ADMIN_ENABLED=True
ADMIN_IP_WHITELIST=  # Leave empty or add your IPs
```

**Note**: Render automatically provides:

- `DATABASE_URL` - PostgreSQL connection string
- Service URL in `ALLOWED_HOSTS`

---

## Step 5: Manual Deployment (Alternative)

If not using `render.yaml`:

### Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your repository
3. Configure:
   - **Name**: `smarthr360-backend`
   - **Environment**: `Python 3`
   - **Region**: Choose closest to users
   - **Branch**: `main`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --no-input
     ```
   - **Start Command**:
     ```bash
     gunicorn smarthr360_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2
     ```

### Create PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Configure:

   - **Name**: `smarthr360-db`
   - **Database**: `smarthr360`
   - **User**: `smarthr360_user`
   - **Region**: Same as web service
   - **Plan**: Free or Starter

3. Link to Web Service:
   - Go to Web Service
   - **Environment** → **Add Environment Variable**
   - Key: `DATABASE_URL`
   - Value: Internal Database URL from PostgreSQL service

---

## Step 6: Deploy Application

1. Render automatically deploys after configuration
2. Monitor in **"Logs"** tab
3. Wait for **"Live"** status (~3-5 minutes)

### Deployment Process

Render executes:

1. **Pre-deploy**: `python manage.py migrate --no-input` (from render.yaml)
2. **Build**: Install requirements + collectstatic
3. **Start**: Run gunicorn with 4 workers

---

## Step 7: Create Superuser

Render doesn't support interactive commands, use Django shell:

1. Go to **Shell** tab in your Web Service
2. Click **"Start Shell"**
3. Run Python commands:

```python
from accounts.models import User
User.objects.create_superuser(
    email='admin@smarthr360.com',
    password='YourSecurePassword123!',
    first_name='Admin',
    last_name='User'
)
exit()
```

---

## Step 8: Verify Deployment

1. **Get your URL**: Find in Render dashboard (e.g., `smarthr360-backend.onrender.com`)

2. **Test API endpoints**:

   ```bash
   # API root
   curl https://smarthr360-backend.onrender.com/api/

   # API documentation
   curl https://smarthr360-backend.onrender.com/api/schema/swagger-ui/
   ```

3. **Test admin panel**:

   - Visit `https://smarthr360-backend.onrender.com/admin/`
   - Login with superuser credentials

4. **Check health**:
   ```bash
   # Should return 200 OK
   curl -I https://smarthr360-backend.onrender.com/admin/
   ```

---

## Step 9: Configure Custom Domain (Optional)

1. Go to **"Settings"** tab
2. Scroll to **"Custom Domain"**
3. Click **"Add Custom Domain"**
4. Enter: `api.smarthr360.com`
5. Add DNS records at your domain provider:
   ```
   Type: CNAME
   Name: api
   Value: smarthr360-backend.onrender.com
   TTL: 3600
   ```
6. Wait for DNS propagation (~5-30 minutes)
7. Render automatically provisions SSL certificate

---

## Environment Variable Management

### Using Render Dashboard

1. Go to **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Enter key and value
4. Click **"Save Changes"**
5. Service redeploys automatically

### Environment Groups (Shared Variables)

1. Go to **"Environment Groups"**
2. Create group: `smarthr360-shared`
3. Add common variables
4. Link to multiple services

---

## Viewing Logs

### Real-time Logs

1. Go to **"Logs"** tab
2. View streaming logs

### Download Logs

1. Click **"Download Logs"**
2. Select time range
3. Download as text file

### Log Filtering

```
# Search logs
<search term>

# Filter by severity
level:error
level:warning
```

---

## Database Management

### Access Database

1. Go to your PostgreSQL service
2. Click **"Connect"** → **"External Connection"**
3. Use connection details with `psql`:
   ```bash
   psql postgresql://user:pass@host/database
   ```

### Run Migrations

Migrations run automatically via `preDeployCommand` in `render.yaml`.

To run manually:

1. Go to **"Shell"** tab
2. Run:
   ```bash
   python manage.py migrate
   ```

### Backup Database

1. Go to PostgreSQL service
2. Click **"Backups"** tab
3. Enable automatic backups
4. Or create manual backup

### Download Backup

```bash
# Get connection URL from Render
export DATABASE_URL="postgresql://..."

# Download backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

---

## Scaling

### Free Tier Limitations

- 750 hours/month
- Service sleeps after 15 minutes of inactivity
- 90-second spin-up time on first request
- 512 MB RAM
- Shared CPU

### Upgrade to Starter Plan ($7/month)

- No sleep
- Dedicated resources
- 1 GB RAM
- Better performance

### Vertical Scaling

1. Go to **"Settings"** tab
2. Scroll to **"Instance Type"**
3. Select larger plan:
   - **Starter**: $7/month (1 GB RAM)
   - **Standard**: $25/month (2 GB RAM)
   - **Pro**: $85/month (4 GB RAM)

### Horizontal Scaling

1. Go to **"Settings"** tab
2. Scroll to **"Scaling"**
3. Increase instance count
4. Render handles load balancing

### Adjust Gunicorn Workers

Modify start command in `render.yaml`:

```yaml
startCommand: gunicorn smarthr360_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 8 --threads 2
```

---

## Continuous Deployment

Render automatically deploys on git push:

1. Make code changes
2. Commit and push:
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin main
   ```
3. Render detects push and deploys automatically
4. Monitor in **"Events"** tab

### Disable Auto-Deploy

1. Go to **"Settings"** tab
2. Scroll to **"Deploy"**
3. Toggle **"Auto-Deploy"** off
4. Deploy manually by clicking **"Manual Deploy"** → **"Deploy latest commit"**

### Deploy Specific Commit

1. Go to **"Manual Deploy"**
2. Select commit from dropdown
3. Click **"Deploy"**

---

## Rollback Deployment

1. Go to **"Events"** tab
2. Find previous successful deployment
3. Click **"Rollback"**
4. Confirm rollback

---

## Monitoring & Observability

### Built-in Metrics

Render provides:

- CPU usage
- Memory usage
- Request count
- Response times

Access in **"Metrics"** tab (Starter plan and above).

### Health Checks

Render automatically monitors:

- HTTP response codes
- Service uptime
- Database connections

### Add Sentry (Error Tracking)

```bash
# Install Sentry SDK
pip install sentry-sdk
```

Add to `requirements.txt`:

```
sentry-sdk>=1.40.0
```

In `settings.py`:

```python
import sentry_sdk

if not DEBUG:
    sentry_sdk.init(
        dsn=config('SENTRY_DSN', default=''),
        traces_sample_rate=1.0,
    )
```

Add `SENTRY_DSN` to environment variables.

---

## Troubleshooting

### Service Won't Start

**Check logs**:

1. Go to **"Logs"** tab
2. Look for error messages

**Common issues**:

- Missing environment variables
- Database connection failed
- Port binding error (use `$PORT`)

### Free Tier Service Sleeping

**Symptoms**: 90-second delay on first request

**Solutions**:

1. Upgrade to Starter plan ($7/month)
2. Use external ping service (UptimeRobot)
3. Implement frontend loading state

### Database Connection Issues

```bash
# Test connection
python manage.py check --database default

# Verify DATABASE_URL format
echo $DATABASE_URL
```

### Static Files Not Loading

1. Check `STATIC_ROOT` in settings.py
2. Run collectstatic:
   ```bash
   python manage.py collectstatic --no-input
   ```
3. Verify WhiteNoise in MIDDLEWARE

### CORS Errors

- Add frontend URL to `CORS_ALLOWED_ORIGINS`
- Ensure `corsheaders.middleware.CorsMiddleware` is in MIDDLEWARE

---

## Cost Optimization

### Free Tier

- **Web Service**: 750 hours/month (free)
- **PostgreSQL**: 90 days free, then $7/month
- **Bandwidth**: 100 GB/month

### Paid Plans

- **Starter**: $7/month (1 GB RAM, no sleep)
- **Standard**: $25/month (2 GB RAM)
- **Pro**: $85/month (4 GB RAM)

### Tips to Reduce Costs

- Use free tier for development
- Optimize database queries
- Enable query caching
- Use WhiteNoise for static files
- Monitor bandwidth usage

---

## Best Practices

1. **Use render.yaml** for infrastructure as code
2. **Enable automatic backups** for database
3. **Set up health checks** for monitoring
4. **Use environment groups** for shared variables
5. **Enable preview environments** for pull requests
6. **Configure custom domain** with SSL
7. **Monitor logs** regularly
8. **Optimize build time** with dependency caching

---

## Next Steps

After successful deployment:

- [ ] Configure custom domain
- [ ] Enable database backups
- [ ] Set up error tracking (Sentry)
- [ ] Configure CI/CD pipeline
- [ ] Set up monitoring alerts
- [ ] Load test application
- [ ] Document deployment process

---

## Resources

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com/
- **Render Status**: https://status.render.com/
- **Pricing**: https://render.com/pricing

---

## Support

Need help? Contact:

- Render Support: https://render.com/support
- SmartHR360 Docs: See `DEPLOYMENT.md`
