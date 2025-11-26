# Deploy to Railway - Quick Guide

## Overview

Railway offers the fastest deployment experience with automatic HTTPS, PostgreSQL database, and zero-downtime deployments.

**Deployment time: ~5-10 minutes**

---

## Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Code pushed to GitHub repository
- Environment variables ready (see `.env.example`)

---

## Step 1: Push Code to GitHub

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - ready for Railway deployment"

# Add remote and push
git remote add origin https://github.com/yourusername/smarthr360_backend.git
git push -u origin main
```

---

## Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account (if not connected)
5. Select `smarthr360_backend` repository
6. Click **"Deploy Now"**

Railway will automatically:

- Detect Python project
- Use `nixpacks.toml` configuration
- Install dependencies from `requirements.txt`
- Run build commands

---

## Step 3: Add PostgreSQL Database

1. In your Railway project dashboard
2. Click **"+ New"**
3. Select **"Database"**
4. Choose **"PostgreSQL"**
5. Wait for database provisioning (~30 seconds)

Railway automatically creates a `DATABASE_URL` environment variable.

---

## Step 4: Configure Environment Variables

1. Click on your **web service**
2. Go to **"Variables"** tab
3. Click **"+ New Variable"**
4. Add each variable below:

### Required Variables

```bash
# Core Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=False
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}

# Database (automatically set by Railway)
# DATABASE_URL=postgresql://... (already set)

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

**Note**: Railway provides these automatic variables:

- `DATABASE_URL` - PostgreSQL connection string
- `RAILWAY_PUBLIC_DOMAIN` - Your public domain
- `PORT` - Application port (set by Railway)

---

## Step 5: Deploy Application

1. After adding variables, Railway **automatically redeploys**
2. Monitor deployment in the **"Deployments"** tab
3. Wait for **"Success"** status (~2-3 minutes)

### Deployment Process

Railway executes these steps (from `nixpacks.toml`):

1. **Setup**: Install Python 3.12 + PostgreSQL
2. **Install**: `pip install -r requirements.txt`
3. **Build**: `python manage.py collectstatic --no-input`
4. **Migrate**: `python manage.py migrate --no-input` (from Procfile)
5. **Start**: `gunicorn smarthr360_backend.wsgi:application` (4 workers)

---

## Step 6: Create Superuser

Railway doesn't support interactive commands during deployment, so create superuser after deployment:

### Option 1: Using Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run command
railway run python manage.py createsuperuser
```

### Option 2: Using Django Shell

```bash
# Run shell
railway run python manage.py shell

# In Python shell:
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

## Step 7: Verify Deployment

1. **Get your URL**: Find in Railway dashboard (e.g., `smarthr360-production.up.railway.app`)

2. **Test API endpoints**:

   ```bash
   # API root
   curl https://smarthr360-production.up.railway.app/api/

   # API documentation
   curl https://smarthr360-production.up.railway.app/api/schema/swagger-ui/
   ```

3. **Test admin panel**:

   - Visit `https://smarthr360-production.up.railway.app/admin/`
   - Login with superuser credentials

4. **Check health**:
   ```bash
   # Should return 200 OK
   curl -I https://smarthr360-production.up.railway.app/admin/
   ```

---

## Step 8: Configure Custom Domain (Optional)

1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"+ Add Domain"**
4. Enter your domain: `api.smarthr360.com`
5. Add DNS records at your domain provider:
   ```
   Type: CNAME
   Name: api
   Value: smarthr360-production.up.railway.app
   TTL: 3600
   ```
6. Wait for DNS propagation (~5-30 minutes)
7. Railway automatically provisions SSL certificate

---

## Environment Variable Management

### Using Railway Dashboard

1. Go to **"Variables"** tab
2. Click **"+ New Variable"**
3. Add/edit variables
4. Click **"Deploy"** to apply

### Using Railway CLI

```bash
# Set variable
railway variables set SECRET_KEY=new-secret-key

# Get variable
railway variables get SECRET_KEY

# Delete variable
railway variables delete OLD_VAR
```

---

## Viewing Logs

### Dashboard Method

1. Go to **"Deployments"** tab
2. Click on latest deployment
3. View real-time logs

### CLI Method

```bash
# View logs
railway logs

# Follow logs (real-time)
railway logs -f
```

---

## Database Management

### Access Database

```bash
# Connect to PostgreSQL
railway connect postgres

# Or get connection details
railway variables | grep DATABASE_URL
```

### Run Migrations

```bash
# Migrations run automatically on each deploy (from Procfile)
# To run manually:
railway run python manage.py migrate
```

### Backup Database

```bash
# Using Railway CLI
railway run pg_dump $DATABASE_URL > backup.sql

# Restore
railway run psql $DATABASE_URL < backup.sql
```

---

## Scaling

### Vertical Scaling (More Resources)

1. Go to **"Settings"** tab
2. Scroll to **"Resources"**
3. Upgrade plan for more CPU/RAM

### Horizontal Scaling (More Instances)

1. Go to **"Settings"** tab
2. Scroll to **"Replicas"**
3. Increase replica count
4. Railway handles load balancing automatically

### Adjust Gunicorn Workers

Modify `Procfile`:

```procfile
web: gunicorn smarthr360_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 8 --threads 2 --timeout 120 --access-logfile - --error-logfile -
```

**Formula**: `workers = (2 x CPU cores) + 1`

---

## Continuous Deployment

Railway automatically deploys on git push:

1. Make code changes
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin main
   ```
3. Railway detects push and deploys automatically
4. Monitor progress in **"Deployments"** tab

### Disable Auto-Deploy

1. Go to **"Settings"** tab
2. Scroll to **"Deploy Triggers"**
3. Toggle **"Auto Deploy"** off
4. Deploy manually by clicking **"Deploy"**

---

## Rollback Deployment

If a deployment fails or has issues:

1. Go to **"Deployments"** tab
2. Find previous successful deployment
3. Click **"⋯"** (three dots)
4. Select **"Redeploy"**
5. Confirm rollback

---

## Monitoring & Observability

### Built-in Metrics

Railway provides:

- CPU usage
- Memory usage
- Network traffic
- Request count
- Response times

Access in **"Metrics"** tab.

### Add Sentry (Error Tracking)

```bash
# Install Sentry SDK
pip install sentry-sdk

# Add to requirements.txt
echo "sentry-sdk>=1.40.0" >> requirements.txt
```

In `settings.py`:

```python
import sentry_sdk

if not DEBUG:
    sentry_sdk.init(
        dsn=config('SENTRY_DSN', default=''),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
```

Add `SENTRY_DSN` to Railway variables.

---

## Troubleshooting

### Deployment Fails

**Check build logs**:

1. Go to **"Deployments"** tab
2. Click failed deployment
3. Review error messages

**Common issues**:

- Missing environment variables → Add in Variables tab
- Requirements not installed → Check `requirements.txt`
- Port binding error → Use `$PORT` (Railway sets this)

### Database Connection Issues

```bash
# Test connection
railway run python manage.py check --database default

# View DATABASE_URL
railway variables get DATABASE_URL
```

### Static Files Not Loading

```bash
# Collect static files
railway run python manage.py collectstatic --no-input

# Verify STATIC_ROOT in settings.py
```

### CORS Errors

- Ensure frontend URL in `CORS_ALLOWED_ORIGINS`
- Check Railway public domain in `ALLOWED_HOSTS`

---

## Cost Optimization

### Free Tier Limits

- $5/month credit (trial)
- Limited CPU/RAM
- No custom domains

### Paid Plans

- **Developer**: $5/month (1 GB RAM, 1 CPU)
- **Team**: $20/month (2 GB RAM, 2 CPUs)
- **Enterprise**: Custom pricing

### Tips to Reduce Costs

- Use fewer gunicorn workers
- Optimize database queries
- Enable query caching
- Use WhiteNoise for static files (no separate server)
- Monitor resource usage in Metrics tab

---

## Next Steps

After successful deployment:

- [ ] Configure custom domain
- [ ] Set up error tracking (Sentry)
- [ ] Enable automated backups
- [ ] Configure CI/CD pipeline
- [ ] Set up monitoring alerts
- [ ] Load test application
- [ ] Document deployment process

---

## Resources

- **Railway Docs**: https://docs.railway.app/
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app/
- **Pricing**: https://railway.app/pricing

---

## Support

Need help? Contact:

- Railway Support: https://help.railway.app/
- SmartHR360 Docs: See `DEPLOYMENT.md`
