#!/bin/bash

# Production setup script for Instagram Automation App
echo "🚀 Setting up Instagram Automation App for production..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx git supervisor

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
python3 -m pip install playwright
playwright install chromium
playwright install-deps

# Create application directory
APP_DIR="/var/www/insta-automation"
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Build React frontend
echo "⚛️ Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs uploads
chmod 755 logs uploads

# Setup environment variables
echo "🔐 Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual values!"
fi

# Setup systemd services
echo "🔄 Setting up systemd services..."
sudo cp deployment/insta-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable insta-automation

# Setup nginx
echo "🌐 Setting up Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/insta-automation
sudo ln -sf /etc/nginx/sites-available/insta-automation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL with Let's Encrypt (optional)
echo "🔒 Setting up SSL..."
sudo apt install -y certbot python3-certbot-nginx
echo "Run: sudo certbot --nginx -d yourdomain.com"

# Setup log rotation
echo "📝 Setting up log rotation..."
sudo cp logrotate-config /etc/logrotate.d/insta-automation

echo "✅ Setup complete!"
echo "📋 Next steps:"
echo "1. Edit .env file with your actual values"
echo "2. Update nginx.conf with your domain"
echo "3. Run: sudo systemctl start insta-automation"
echo "4. Setup SSL: sudo certbot --nginx -d yourdomain.com"
