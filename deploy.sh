#!/bin/bash

# Instagram Automation Deployment Script
# This script sets up the application on a Ubuntu/Debian VPS

set -e

echo "🚀 Starting Instagram Automation deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx git curl nodejs npm certbot python3-certbot-nginx

# Install Playwright dependencies
echo "🎭 Installing Playwright system dependencies..."
sudo apt install -y libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgtk-3-0 libatspi2.0-0 libxss1 libasound2

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/instaAutomation
sudo chown -R $USER:$USER /var/www/instaAutomation

# Navigate to application directory
cd /var/www/instaAutomation

# Clone repository (assuming this script is run after git clone)
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found. Make sure you've cloned the repository correctly."
    exit 1
fi

# Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

# Setup environment file
echo "⚙️ Setting up environment configuration..."
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found!"
    echo "Please make sure .env.production is in the backend directory"
    exit 1
fi

# Create logs directory
mkdir -p logs
sudo chown -R www-data:www-data logs

# Setup frontend
echo "⚛️ Setting up frontend..."
cd ../frontend

# Install Node.js dependencies
npm install

# Build frontend for production
echo "🏗️ Building frontend for production..."
NODE_ENV=production npm run build

# Setup systemd service
echo "🔧 Setting up systemd service..."
cd ..
sudo cp insta-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable insta-automation

# Setup Nginx
echo "🌐 Setting up Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/wdyautomation.shop
sudo ln -sf /etc/nginx/sites-available/wdyautomation.shop /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Setup SSL certificate with Let's Encrypt
echo "🔒 Setting up SSL certificate..."
sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop --non-interactive --agree-tos --email your-email@domain.com

# Start services
echo "🚀 Starting services..."
sudo systemctl start insta-automation
sudo systemctl reload nginx

# Setup firewall
echo "🔥 Setting up firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# Final checks
echo "✅ Checking service status..."
sudo systemctl status insta-automation --no-pager
sudo systemctl status nginx --no-pager

echo "🎉 Deployment completed successfully!"
echo "🌐 Your application should be available at: https://wdyautomation.shop"
echo ""
echo "📋 Useful commands:"
echo "  - Check backend logs: sudo journalctl -f -u insta-automation"
echo "  - Check nginx logs: sudo tail -f /var/log/nginx/wdyautomation_error.log"
echo "  - Restart backend: sudo systemctl restart insta-automation"
echo "  - Restart nginx: sudo systemctl restart nginx"
