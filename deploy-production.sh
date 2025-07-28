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

# Check if running as root - modified for VPS deployment
if [[ $EUID -eq 0 ]]; then
   echo -e "${YELLOW}Running as root - this is okay for VPS deployment${NC}"
   # Create a non-root user if needed
   if ! id "deploy" &>/dev/null; then
       echo -e "${YELLOW}Creating deploy user...${NC}"
       useradd -m -s /bin/bash deploy
       usermod -aG sudo deploy
       # Set up sudo without password for deploy user
       echo "deploy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
   fi
   
   # Switch to deploy user for the rest of the script
   echo -e "${YELLOW}Switching to deploy user...${NC}"
   sudo -u deploy bash -c "
       export PROJECT_DIR='$PROJECT_DIR'
       export NGINX_SITE='$NGINX_SITE'
       export RED='$RED'
       export GREEN='$GREEN' 
       export YELLOW='$YELLOW'
       export NC='$NC'
       
       # Continue with the deployment as deploy user
       exec /var/www/instaAutomation/deploy-production.sh
   "
   exit 0
fi

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

# Install Node dependencies
npm install

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
pm2 startup systemd
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

echo -e "${YELLOW}9. Setting up SSL certificate...${NC}"
# First, make sure the domain is pointing to this server
echo "Please ensure your domain wdyautomation.shop is pointing to this server's IP address"
echo "Press Enter to continue with SSL setup, or Ctrl+C to exit..."
read

certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop --non-interactive --agree-tos --email admin@wdyautomation.shop

echo -e "${YELLOW}10. Configuring firewall...${NC}"
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw --force enable

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
