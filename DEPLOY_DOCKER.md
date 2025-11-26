# Deploy to VPS with Docker - Complete Guide

## Overview

Deploy SmartHR360 Backend to any VPS (DigitalOcean, AWS EC2, Linode, etc.) using Docker, Nginx, and PostgreSQL.

**Deployment time: ~30-60 minutes**

---

## Prerequisites

- VPS with Ubuntu 20.04+ (2 GB RAM minimum, 4 GB recommended)
- Root or sudo access
- Domain name (optional but recommended)
- SSH client
- Basic Linux command line knowledge

---

## Step 1: Provision VPS

Choose a VPS provider:

- **DigitalOcean**: $6/month (1 GB RAM, 25 GB SSD)
- **Linode**: $5/month (1 GB RAM, 25 GB SSD)
- **AWS EC2**: t2.micro (1 GB RAM, free tier eligible)
- **Vultr**: $6/month (1 GB RAM, 25 GB SSD)

**Recommended specs**:

- **Memory**: 2-4 GB RAM
- **CPU**: 1-2 cores
- **Storage**: 25-50 GB SSD
- **OS**: Ubuntu 22.04 LTS

---

## Step 2: Initial Server Setup

### Connect to VPS

```bash
ssh root@your-server-ip
```

### Update system

```bash
apt update && apt upgrade -y
```

### Create non-root user

```bash
# Create user
adduser deploy

# Add to sudo group
usermod -aG sudo deploy

# Switch to deploy user
su - deploy
```

### Configure firewall

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

---

## Step 3: Install Docker & Docker Compose

### Install Docker

```bash
# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login to apply group changes
exit
ssh deploy@your-server-ip

# Verify installation
docker --version
```

### Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

---

## Step 4: Clone Repository

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone repository
git clone https://github.com/yourusername/smarthr360_backend.git
cd smarthr360_backend
```

---

## Step 5: Configure Environment Variables

### Create production .env file

```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env
```

### Production .env configuration

```bash
# Core Settings
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Database (Docker internal connection)
DATABASE_URL=postgresql://smarthr360_user:YourSecurePassword123@db:5432/smarthr360

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com

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
ADMIN_IP_WHITELIST=your-office-ip,your-home-ip

# Database credentials (for docker-compose.yml)
DB_NAME=smarthr360
DB_USER=smarthr360_user
DB_PASSWORD=YourSecurePassword123
```

**Generate SECRET_KEY**:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 6: Configure Docker Compose

### Edit docker-compose.yml (if needed)

```bash
nano docker-compose.yml
```

Verify these settings:

- Database credentials match `.env` file
- Port mappings (80:80, 443:443)
- Volume mounts for persistent data

---

## Step 7: Build and Start Containers

### Build Docker images

```bash
docker-compose build
```

### Start services

```bash
docker-compose up -d
```

### Verify containers are running

```bash
docker-compose ps
```

Expected output:

```
NAME                  STATUS          PORTS
smarthr360_db         Up              5432/tcp
smarthr360_web        Up              8000/tcp
smarthr360_nginx      Up              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

## Step 8: Create Superuser

```bash
# Enter web container
docker-compose exec web bash

# Create superuser
python manage.py createsuperuser

# Exit container
exit
```

Follow prompts to create admin account.

---

## Step 9: Configure SSL with Let's Encrypt

### Install Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop Nginx container temporarily
docker-compose stop nginx

# Obtain SSL certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Start Nginx container
docker-compose start nginx
```

### Update nginx.conf with SSL

```bash
nano nginx.conf
```

Update server_name:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... rest of config
}
```

### Mount SSL certificates in docker-compose.yml

```yaml
nginx:
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - static_volume:/app/staticfiles:ro
    - media_volume:/app/media:ro
    - /etc/letsencrypt:/etc/nginx/ssl:ro # SSL certificates
```

### Restart Nginx

```bash
docker-compose restart nginx
```

### Auto-renew SSL certificates

```bash
# Add cron job
sudo crontab -e

# Add this line (runs daily at 3 AM)
0 3 * * * certbot renew --quiet && docker-compose restart nginx
```

---

## Step 10: Verify Deployment

### Test API endpoints

```bash
# API root
curl https://your-domain.com/api/

# API documentation
curl https://your-domain.com/api/schema/swagger-ui/

# Admin panel
curl https://your-domain.com/admin/
```

### Check container logs

```bash
# All logs
docker-compose logs

# Web container only
docker-compose logs web

# Follow logs (real-time)
docker-compose logs -f
```

### Test database connection

```bash
docker-compose exec web python manage.py check --database default
```

---

## Database Management

### Access PostgreSQL

```bash
# Enter database container
docker-compose exec db psql -U smarthr360_user -d smarthr360

# Run SQL queries
\dt  # List tables
\q   # Exit
```

### Run migrations

```bash
docker-compose exec web python manage.py migrate
```

### Create database backup

```bash
# Backup
docker-compose exec db pg_dump -U smarthr360_user smarthr360 > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T db psql -U smarthr360_user smarthr360 < backup_20240101.sql
```

### Automated daily backups

```bash
# Create backup script
nano ~/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cd /home/deploy/apps/smarthr360_backend
docker-compose exec -T db pg_dump -U smarthr360_user smarthr360 > $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql"
```

```bash
# Make executable
chmod +x ~/backup.sh

# Add to cron (runs daily at 2 AM)
crontab -e
0 2 * * * /home/deploy/backup.sh >> /home/deploy/backup.log 2>&1
```

---

## Monitoring & Logs

### View logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f db
```

### Monitor resource usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Check volumes
docker volume ls
```

### Install monitoring tools (optional)

#### Netdata (System Monitoring)

```bash
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

Access at: `http://your-server-ip:19999`

#### Glances (CLI Monitoring)

```bash
sudo apt install -y glances
glances
```

---

## Scaling

### Vertical Scaling (More Resources)

Upgrade VPS plan for more CPU/RAM.

### Horizontal Scaling (More Containers)

```bash
# Scale web containers
docker-compose up -d --scale web=3

# Update nginx.conf for load balancing
upstream django {
    server web1:8000;
    server web2:8000;
    server web3:8000;
}
```

### Adjust Gunicorn Workers

Edit `docker-compose.yml`:

```yaml
web:
  command: >
    sh -c "python manage.py migrate --no-input &&
           gunicorn smarthr360_backend.wsgi:application
           --bind 0.0.0.0:8000
           --workers 8  # Increase workers
           --threads 2
           --timeout 120"
```

**Formula**: `workers = (2 x CPU cores) + 1`

---

## Continuous Deployment

### Manual Deployment

```bash
# SSH to server
ssh deploy@your-server-ip

# Navigate to app directory
cd ~/apps/smarthr360_backend

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --no-input
```

### Automated Deployment with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USERNAME }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd ~/apps/smarthr360_backend
            git pull origin main
            docker-compose down
            docker-compose build
            docker-compose up -d
            docker-compose exec -T web python manage.py migrate
            docker-compose exec -T web python manage.py collectstatic --no-input
```

Add secrets in GitHub repo settings:

- `VPS_HOST`: your-server-ip
- `VPS_USERNAME`: deploy
- `VPS_SSH_KEY`: SSH private key

---

## Security Best Practices

### Keep system updated

```bash
# Update system weekly
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

### Configure fail2ban

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Enable and start
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Limit SSH access

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Disable root login
PermitRootLogin no

# Change SSH port (optional)
Port 2222

# Restart SSH
sudo systemctl restart sshd

# Update firewall
sudo ufw allow 2222/tcp
sudo ufw delete allow 22/tcp
```

### Use SSH keys only

```bash
# Disable password authentication
sudo nano /etc/ssh/sshd_config
PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

---

## Troubleshooting

### Containers not starting

```bash
# Check logs
docker-compose logs

# Verify .env file
cat .env

# Check port conflicts
sudo netstat -tulpn | grep -E ':(80|443|5432|8000)'
```

### Database connection failed

```bash
# Check database is running
docker-compose ps db

# Test connection
docker-compose exec web python manage.py check --database default

# View database logs
docker-compose logs db
```

### Nginx 502 Bad Gateway

```bash
# Check web container is running
docker-compose ps web

# View web logs
docker-compose logs web

# Restart services
docker-compose restart web nginx
```

### SSL certificate issues

```bash
# Renew certificate
sudo certbot renew

# Restart nginx
docker-compose restart nginx

# Check certificate expiry
sudo certbot certificates
```

### Disk space issues

```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a

# Clean old backups
find ~/backups -name "*.sql" -mtime +30 -delete
```

---

## Maintenance

### Regular maintenance checklist

- [ ] Update system packages weekly
- [ ] Check disk space monthly
- [ ] Review logs for errors weekly
- [ ] Verify backups are working weekly
- [ ] Renew SSL certificates (auto-renews)
- [ ] Update Docker images monthly
- [ ] Monitor resource usage
- [ ] Test restore from backup quarterly

### Update Django application

```bash
cd ~/apps/smarthr360_backend
git pull origin main
docker-compose build web
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --no-input
```

---

## Cost Optimization

### VPS Provider Comparison

| Provider     | Plan          | RAM  | Storage | Price |
| ------------ | ------------- | ---- | ------- | ----- |
| DigitalOcean | Basic         | 1 GB | 25 GB   | $6/mo |
| Linode       | Nanode        | 1 GB | 25 GB   | $5/mo |
| Vultr        | Cloud Compute | 1 GB | 25 GB   | $6/mo |
| AWS EC2      | t2.micro      | 1 GB | 30 GB   | $8/mo |

**Recommended**: Start with 2 GB RAM ($12-15/month)

### Tips to Reduce Costs

- Use fewer gunicorn workers
- Optimize database queries
- Enable query caching
- Use WhiteNoise for static files
- Monitor resource usage
- Clean Docker images regularly

---

## Next Steps

After successful deployment:

- [ ] Configure domain DNS
- [ ] Set up SSL auto-renewal
- [ ] Enable automated backups
- [ ] Configure monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Implement CI/CD pipeline
- [ ] Load test application
- [ ] Document runbook

---

## Resources

- **Docker Docs**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **Nginx Docs**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **DigitalOcean Tutorials**: https://www.digitalocean.com/community/tutorials

---

## Support

Need help? Contact:

- SmartHR360 Docs: See `DEPLOYMENT.md`
- Docker Community: https://forums.docker.com/
