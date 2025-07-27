#!/bin/bash

# Instagram Automation VPS Deployment Script
# Run this script on your VPS after cloning the repository

set -e

echo "🚀 Starting Instagram Automation VPS Deployment..."

# Variables
PROJECT_DIR="/var/www/instaAutoamtion"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DOMAIN="wdyautomation.shop"

# Function to print colored output
print_status() {
    echo -e "\e[32m[INFO]\e[0m $1"
}

print_error() {
    echo -e "\e[31m[ERROR]\e[0m $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx curl

# Install Node.js
print_status "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Navigate to project directory
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory $PROJECT_DIR not found!"
    print_status "Please clone your repository first:"
    print_status "cd /var/www && git clone https://github.com/yourusername/instaUI2.git instaAutomation"
    exit 1
fi

cd $PROJECT_DIR

# Setup backend
print_status "Setting up backend..."
cd $BACKEND_DIR

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
PORT=5000
MAX_CONTENT_LENGTH=104857600
EOF
fi

# Setup frontend
print_status "Setting up frontend..."
cd $FRONTEND_DIR

# Install npm dependencies
npm install

# Build production version
npm run build

# Setup Nginx
print_status "Configuring Nginx..."
cp $PROJECT_DIR/nginx.conf /etc/nginx/sites-available/instaAutomation

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Enable our site
ln -sf /etc/nginx/sites-available/instaAutomation /etc/nginx/sites-enabled/

# Test nginx configuration
nginx -t

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/instaAutomation.service << EOF
[Unit]
Description=Instagram Automation Flask App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/venv/bin
ExecStart=$BACKEND_DIR/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set proper permissions
print_status "Setting file permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# Enable and start services
print_status "Starting services..."
systemctl daemon-reload
systemctl enable instaAutomation
systemctl start instaAutomation
systemctl enable nginx
systemctl restart nginx

# Setup firewall
print_status "Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow ssh
ufw --force enable

# Setup SSL certificate
print_status "Setting up SSL certificate..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Enable auto-renewal
systemctl enable certbot.timer

# Check service status
print_status "Checking service status..."
systemctl status instaAutomation --no-pager
systemctl status nginx --no-pager

print_status "🎉 Deployment completed!"
print_status "Your application should now be available at: https://$DOMAIN"
print_status ""
print_status "To check logs:"
print_status "  Backend: sudo journalctl -u instaAutomation -f"
print_status "  Nginx: sudo tail -f /var/log/nginx/error.log"
print_status ""
print_status "To restart services:"
print_status "  Backend: sudo systemctl restart instaAutomation"
print_status "  Nginx: sudo systemctl restart nginx"
