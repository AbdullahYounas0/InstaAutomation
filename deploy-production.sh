#!/bin/bash
# Production Deployment Script for wdyautomation.shop

set -e  # Exit on any error

echo "🚀 Starting production deployment for wdyautomation.shop..."

# Build frontend for production
echo "📦 Building React frontend for production..."
cd frontend
npm run build
cd ..

# Copy built files to deployment directory
echo "📂 Copying files to deployment directory..."
rm -rf deployment/build
cp -r frontend/build deployment/

# Update nginx configuration
echo "🔧 Updating nginx configuration..."
sudo cp nginx-production.conf /etc/nginx/sites-available/wdyautomation.shop
sudo ln -sf /etc/nginx/sites-available/wdyautomation.shop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set production environment variables
echo "🌍 Setting up environment variables..."
export FLASK_ENV=production
export DEBUG=False
export SECRET_KEY="$(openssl rand -base64 32)"
export JWT_SECRET_KEY="$(openssl rand -base64 32)"
export PORT=5000
export HOST=0.0.0.0

# Create systemd service for backend
echo "⚙️ Setting up systemd service..."
sudo cp ../deployment/insta-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable insta-automation
sudo systemctl restart insta-automation

echo "✅ Production deployment completed!"
echo "🌐 Your application should now be available at https://wdyautomation.shop"
echo "📊 Check service status: sudo systemctl status insta-automation"
echo "📋 View logs: sudo journalctl -u insta-automation -f"
