#!/bin/bash
# Quick fix for current VPS deployment issues

echo "🔧 Quick fix for wdyautomation.shop deployment issues..."

# Stop any existing PM2 processes
pm2 stop all || true
pm2 delete all || true

# Go to project directory
cd /var/www/instaAutomation

# Activate Python virtual environment
cd backend
source venv/bin/activate

# Start backend directly with PM2
pm2 start app.py --name "instaautomation-backend" --interpreter python3

# Build frontend
cd ../frontend
npm run build

# Check PM2 status
pm2 status

# Test backend health
echo "Testing backend health..."
curl -X GET http://localhost:8001/api/health || echo "Backend not responding on 8001"
curl -X GET http://localhost:5000/api/health || echo "Backend not responding on 5000"

# Check if Nginx is running
systemctl status nginx --no-pager

echo "✅ Quick fix completed!"
echo "📋 Next steps:"
echo "1. Check PM2 logs: pm2 logs"
echo "2. Test API: curl https://wdyautomation.shop/api/health"
echo "3. Check Nginx config: nginx -t"
