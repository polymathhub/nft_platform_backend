# NFT Platform Backend - Ubuntu Deployment Guide

**Deployment Target:** Ubuntu Server at `root@5.252.155.82`

## Prerequisites

✓ Ubuntu 20.04 LTS or later  
✓ Root or sudo access  
✓ 2GB+ RAM  
✓ 10GB+ free disk space  

---

## Quick Deployment (Automated)

This is the **easiest method** if you have SSH access to the Ubuntu server.

### 1. Copy deployment script to Ubuntu

```bash
# On your Windows machine
scp deploy.sh root@5.252.155.82:/tmp/
```

### 2. SSH into the server and run the script

```bash
ssh root@5.252.155.82

# On Ubuntu server:
bash /tmp/deploy.sh
```

The script will:
- ✅ Update system packages
- ✅ Install Python 3.11, PostgreSQL, Nginx
- ✅ Create `nft_user` and `nft_db` database
- ✅ Setup Python virtual environment
- ✅ Configure systemd service for auto-restart
- ✅ Setup Nginx reverse proxy
- ✅ Start all services

**Total time: ~5-10 minutes**

---

## Manual Deployment (Step-by-Step)

If you prefer to do it manually or the script fails:

### 1. Connect to Ubuntu Server

```bash
ssh root@5.252.155.82
```

### 2. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Install Dependencies

```bash
sudo apt install -y \
    git \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-client \
    nginx \
    curl \
    wget
```

### 4. Create Application User

```bash
sudo useradd -m -s /bin/bash nft_app
sudo usermod -aG sudo nft_app
```

### 5. Clone Repository

```bash
sudo -u nft_app git clone https://github.com/your-username/nft_platform_backend.git /home/nft_app/nft_platform
cd /home/nft_app/nft_platform
```

### 6. Setup PostgreSQL Database

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER nft_user WITH PASSWORD 'GiftedForge';
CREATE DATABASE nft_db OWNER nft_user;
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nft_user;
EOF
```

### 7. Setup Python Virtual Environment

```bash
cd /home/nft_app/nft_platform
sudo -u nft_app python3.11 -m venv .venv
sudo -u nft_app .venv/bin/pip install --upgrade pip
sudo -u nft_app .venv/bin/pip install -r requirements.txt
```

### 8. Copy Environment File

On your Windows machine:
```bash
scp .env root@5.252.155.82:/home/nft_app/nft_platform/
```

Verify the DATABASE_URL in the `.env` file:
```bash
cat /home/nft_app/nft_platform/.env | grep DATABASE_URL
# Should show: postgresql+asyncpg://nft_user:GiftedForge@5.252.155.82:5432/nft_db
```

### 9. Setup Systemd Service

```bash
# Copy service file
sudo cp /home/nft_app/nft_platform/deployment/systemd/nft-platform.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable nft-platform
sudo systemctl start nft-platform

# Check status
sudo systemctl status nft-platform
```

### 10. Setup Nginx Reverse Proxy

```bash
# Copy Nginx config
sudo cp /home/nft_app/nft_platform/deployment/nginx/nft-platform.conf /etc/nginx/sites-available/

# Enable site
sudo ln -s /etc/nginx/sites-available/nft-platform.conf /etc/nginx/sites-enabled/

# Test and start
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Verify Deployment

### Check services are running

```bash
sudo systemctl status nft-platform
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Check logs

```bash
# Real-time logs
sudo journalctl -u nft-platform -f

# Last 50 lines
sudo journalctl -u nft-platform -n 50
```

### Test API

```bash
# Direct (port 8000)
curl http://localhost:8000/health

# Via Nginx (port 80)
curl http://localhost/health

# API Documentation
# Open in browser: http://5.252.155.82/docs
```

---

## Common Commands

### Service Management

```bash
# View real-time logs
sudo journalctl -u nft-platform -f

# Restart service
sudo systemctl restart nft-platform

# View last 100 lines of logs
sudo systemctl -u nft-platform -n 100

# Service status
sudo systemctl status nft-platform

# Enable/disable auto-start
sudo systemctl enable nft-platform
sudo systemctl disable nft-platform
```

### Database Management

```bash
# Connect to PostgreSQL as nft_user
psql -h localhost -U nft_user -d nft_db

# View database size
sudo -u postgres psql -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datname = 'nft_db';"

# Backup database
sudo -u postgres pg_dump nft_db > backup_nft_db.sql

# Restore database
sudo -u postgres psql nft_db < backup_nft_db.sql
```

### Nginx Management

```bash
# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### Service won't start

```bash
# Check error logs
sudo journalctl -u nft-platform -n 50

# Manually run the startup script to see errors
cd /home/nft_app/nft_platform
source .venv/bin/activate
python startup.py
```

### Database connection error

```bash
# Test PostgreSQL connection
psql -h localhost -U nft_user -d nft_db

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check if nft_db exists
sudo -u postgres psql -l | grep nft_db
```

### Nginx 502 Bad Gateway

```bash
# Check if backend is running
sudo systemctl status nft-platform

# Check if 8000 is listening
sudo netstat -tlnp | grep 8000

# Test direct connection to backend
curl http://localhost:8000/health
```

### Permission denied errors

```bash
# Fix file ownership
sudo chown -R nft_app:nft_app /home/nft_app/nft_platform
sudo chmod -R 755 /home/nft_app/nft_platform
```

---

## Access Your Application

### Direct Access (Port 8000)
```
http://5.252.155.82:8000
http://5.252.155.82:8000/docs    # API Documentation
```

### Via Nginx (Port 80)
```
http://5.252.155.82
http://5.252.155.82/docs         # API Documentation
```

---

## Next Steps (Production)

1. **Setup SSL/HTTPS**
   - Use Let's Encrypt: `sudo apt install certbot python3-certbot-nginx`
   - Uncomment HTTPS section in `/etc/nginx/sites-available/nft-platform.conf`

2. **Database Backups**
   ```bash
   # Daily backup script
   sudo crontab -e
   # Add: 0 2 * * * pg_dump -U nft_user -d nft_db > /backups/nft_db_$(date +\%Y\%m\%d).sql
   ```

3. **Monitor Performance**
   - Setup uptime monitoring (Uptime Kuma, NewRelic, etc.)
   - Monitor disk space: `df -h`
   - Monitor database size: `du -sh /var/lib/postgresql`

4. **Log Management**
   - Rotate logs: `sudo logrotate -f /etc/logrotate.conf`
   - Archive logs to cloud storage

---

## Support

For issues, check:
1. Service logs: `sudo journalctl -u nft-platform -f`
2. Database connectivity: `psql -h localhost -U nft_user -d nft_db`
3. Nginx errors: `sudo tail -f /var/log/nginx/error.log`

---

**Deployment Date:** March 9, 2026  
**Server:** root@5.252.155.82  
**Status:** Ready for Production
