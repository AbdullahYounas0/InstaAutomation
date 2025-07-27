#!/bin/bash

# Quick deployment script for updates
echo "🔄 Deploying updates..."

APP_DIR="/var/www/insta-automation"

# Navigate to app directory
cd $APP_DIR

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update Python dependencies
echo "📚 Updating Python dependencies..."
pip install -r requirements.txt

# Build React frontend
echo "⚛️ Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart insta-automation
sudo systemctl reload nginx

# Check status
echo "📊 Service status:"
sudo systemctl status insta-automation --no-pager

echo "✅ Deployment complete!"
