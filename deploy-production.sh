#!/bin/bash
# Production Deployment Script for wdyautomation.shop

set -e  # Exit on any error

echo "🚀 Starting production deployment for wdyautomation.shop..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/instaAutomation"
NGINX_SITE="wdyautomation.shop"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}" 
   exit 1
fi

echo -e "${YELLOW}1. Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${YELLOW}2. Installing required dependencies...${NC}"
sudo apt install -y curl wget git nginx certbot python3-certbot-nginx

# Install Node.js 18.x
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}3. Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install PM2
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}4. Installing PM2...${NC}"
    sudo npm install -g pm2
fi

echo -e "${YELLOW}5. Setting up project directory...${NC}"
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

echo -e "${YELLOW}6. Cloning/updating repository...${NC}"
if [ -d "$PROJECT_DIR/.git" ]; then
    cd $PROJECT_DIR
    git pull origin main
else
    git clone https://github.com/YOUR_USERNAME/instaAutomation.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

echo -e "${YELLOW}7. Setting up backend...${NC}"
cd $PROJECT_DIR/backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs uploads

echo -e "${YELLOW}8. Setting up frontend...${NC}"
cd $PROJECT_DIR/frontend

# Install Node dependencies
npm install

# Build production version
npm run build

echo -e "${YELLOW}9. Configuring PM2...${NC}"
cd $PROJECT_DIR

# Copy ecosystem config
cp ecosystem.config.js ecosystem.config.production.js

# Start application with PM2
pm2 start ecosystem.config.production.js

# Save PM2 configuration
pm2 save

# Set PM2 to start on system boot
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $USER --hp $HOME

echo -e "${YELLOW}10. Configuring Nginx...${NC}"
# Copy nginx configuration
sudo cp nginx-production.conf /etc/nginx/sites-available/$NGINX_SITE

# Enable the site
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

echo -e "${YELLOW}11. Setting up SSL certificate...${NC}"
sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop --non-interactive --agree-tos --email your-email@example.com

echo -e "${YELLOW}12. Configuring firewall...${NC}"
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw --force enable

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}Your application is now live at: https://wdyautomation.shop${NC}"

echo -e "${YELLOW}📋 Post-deployment checklist:${NC}"
echo "1. Update the SECRET_KEY in ecosystem.config.js"
echo "2. Update the email in certbot command"
echo "3. Test all application features"
echo "4. Set up monitoring and backups"
echo "5. Update DNS records if needed"

echo -e "${YELLOW}🔧 Useful commands:${NC}"
echo "pm2 status               - Check application status"
echo "pm2 logs                 - View application logs"
echo "pm2 restart all          - Restart application"
echo "sudo systemctl status nginx - Check nginx status"
echo "sudo certbot renew       - Renew SSL certificate"
