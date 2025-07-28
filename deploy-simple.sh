#!/bin/bash
# Simple VPS Deployment Script for wdyautomation.shop
# Run this as root on your VPS

set -e  # Exit on any error

echo "🚀 Starting simple production deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/instaAutomation"
NGINX_SITE="wdyautomation.shop"

echo -e "${YELLOW}1. Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}2. Installing required dependencies...${NC}"
apt install -y curl wget git nginx certbot python3-certbot-nginx python3-pip python3-venv

# Install Node.js 18.x
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}3. Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

# Install PM2
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}4. Installing PM2...${NC}"
    npm install -g pm2
fi

echo -e "${YELLOW}5. Setting up backend...${NC}"
cd $PROJECT_DIR/backend

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs uploads

echo -e "${YELLOW}6. Setting up frontend...${NC}"
cd $PROJECT_DIR/frontend

# Install Node dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    npm install
fi

# Build production version
npm run build

echo -e "${YELLOW}7. Configuring PM2...${NC}"
cd $PROJECT_DIR

# Stop any existing PM2 processes
pm2 stop all || true
pm2 delete all || true

# Start application with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Set PM2 to start on system boot
pm2 startup
env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u root --hp /root

echo -e "${YELLOW}8. Configuring Nginx...${NC}"
# Copy nginx configuration
cp nginx-production.conf /etc/nginx/sites-available/$NGINX_SITE

# Enable the site
ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Restart nginx
systemctl restart nginx

echo -e "${YELLOW}9. Configuring firewall...${NC}"
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw --force enable

echo -e "${GREEN}✅ Basic deployment completed!${NC}"
echo -e "${GREEN}Your application should now be accessible at: http://wdyautomation.shop${NC}"

echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Set up SSL: sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop"
echo "2. Check PM2 status: pm2 status"
echo "3. Check application logs: pm2 logs"
echo "4. Test the application: curl http://wdyautomation.shop/api/health"
