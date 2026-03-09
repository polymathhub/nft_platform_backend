#!/bin/bash
# Quick deployment script for Ubuntu server
# Run this on Ubuntu: bash deploy.sh

set -e

echo "=================================================="
echo "NFT Platform Backend - Ubuntu Quick Deploy"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="nft_app"
APP_DIR="/home/nft_app/nft_platform"
DB_NAME="nft_db"
DB_USER="nft_user"
DB_PASSWORD="GiftedForge"

# Step 1: Update system
echo -e "${BLUE}[1/8] Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Step 2: Install dependencies
echo -e "${BLUE}[2/8] Installing dependencies...${NC}"
sudo apt install -y \
    git \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-client \
    curl \
    wget \
    nginx

# Step 3: Create application user
echo -e "${BLUE}[3/8] Creating application user...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash "$APP_USER"
    sudo usermod -aG sudo "$APP_USER"
    echo "✓ User $APP_USER created"
else
    echo "✓ User $APP_USER already exists"
fi

# Step 4: Setup PostgreSQL
echo -e "${BLUE}[4/8] Setting up PostgreSQL...${NC}"
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check if nft_user exists
if ! sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1; then
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    echo "✓ Created PostgreSQL user: $DB_USER"
else
    echo "✓ PostgreSQL user $DB_USER already exists"
fi

# Check if nft_db exists
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    echo "✓ Created PostgreSQL database: $DB_NAME"
else
    echo "✓ PostgreSQL database $DB_NAME already exists"
fi

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;"

# Step 5: Setup Python environment
echo -e "${BLUE}[5/8] Setting up Python virtual environment...${NC}"
if [ ! -d "$APP_DIR/.venv" ]; then
    cd "$APP_DIR"
    sudo -u "$APP_USER" python3.11 -m venv .venv
    sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip
    sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt
    echo "✓ Virtual environment created and dependencies installed"
else
    echo "✓ Virtual environment already exists"
fi

# Step 6: Setup systemd service
echo -e "${BLUE}[6/8] Setting up systemd service...${NC}"
sudo cp "$APP_DIR/deployment/systemd/nft-platform.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nft-platform
echo "✓ Systemd service configured"

# Step 7: Setup Nginx
echo -e "${BLUE}[7/8] Setting up Nginx reverse proxy...${NC}"
sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
sudo cp "$APP_DIR/deployment/nginx/nft-platform.conf" /etc/nginx/sites-available/
if [ ! -L /etc/nginx/sites-enabled/nft-platform.conf ]; then
    sudo ln -s /etc/nginx/sites-available/nft-platform.conf /etc/nginx/sites-enabled/
fi
sudo systemctl enable nginx
echo "✓ Nginx configured"

# Step 8: Start services
echo -e "${BLUE}[8/8] Starting services...${NC}"
sudo systemctl start nft-platform
sudo systemctl start nginx

# Wait for service to start
sleep 5

# Check status
if sudo systemctl is-active --quiet nft-platform; then
    echo -e "${GREEN}✓ NFT Platform Backend is running${NC}"
else
    echo "✗ NFT Platform Backend failed to start"
    sudo systemctl status nft-platform
fi

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo "✗ Nginx failed to start"
fi

# Summary
echo ""
echo "=================================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "Your NFT Platform Backend is now running!"
echo ""
echo "Access points:"
echo "  • Direct API: http://5.252.155.82:8000"
echo "  • Via Nginx: http://5.252.155.82"
echo "  • API Docs: http://5.252.155.82:8000/docs"
echo ""
echo "Services:"
echo "  • Start service: sudo systemctl start nft-platform"
echo "  • Stop service: sudo systemctl stop nft-platform"
echo "  • View logs: sudo journalctl -u nft-platform -f"
echo "  • Status: sudo systemctl status nft-platform"
echo ""
