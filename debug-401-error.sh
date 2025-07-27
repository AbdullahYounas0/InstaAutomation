#!/bin/bash

# Debug script to identify the exact cause of 401 error
echo "🔍 DEBUGGING 401 UNAUTHORIZED ERROR"
echo "===================================="

# Check if we're on the correct server
if [ ! -d "/var/www/insta-automation" ]; then
    echo "❌ Run this script on your VPS where the project is deployed"
    exit 1
fi

cd /var/www/insta-automation

echo "1️⃣ Checking current SSL/HTTPS status..."
echo "Domain SSL Certificate:"
sudo certbot certificates | grep wdyautomation.shop || echo "❌ No SSL certificate found"

echo ""
echo "2️⃣ Checking Nginx configuration..."
echo "Current Nginx sites-enabled:"
ls -la /etc/nginx/sites-enabled/

echo ""
echo "Testing if site responds to HTTPS:"
curl -I https://wdyautomation.shop/api/health 2>/dev/null | head -3 || echo "❌ HTTPS not working"

echo ""
echo "Testing if site responds to HTTP:"
curl -I http://wdyautomation.shop/api/health 2>/dev/null | head -3 || echo "❌ HTTP not working"

echo ""
echo "3️⃣ Checking backend service status..."
echo "Backend service status:"
sudo systemctl status insta-automation --no-pager -l | head -10

echo ""
echo "Backend process listening on port 5000:"
sudo netstat -tlnp | grep :5000 || echo "❌ No process listening on port 5000"

echo ""
echo "4️⃣ Checking recent backend logs..."
echo "Last 20 lines of backend logs:"
sudo journalctl -u insta-automation --no-pager -n 20

echo ""
echo "5️⃣ Testing login endpoint directly..."
echo "Testing direct API call to backend:"
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  2>/dev/null || echo "❌ Direct backend call failed"

echo ""
echo "6️⃣ Checking users.json file..."
echo "Users file exists:"
ls -la backend/users.json 2>/dev/null || echo "❌ users.json not found"

if [ -f "backend/users.json" ]; then
    echo "Users file content:"
    cat backend/users.json | head -10
fi

echo ""
echo "7️⃣ Checking Flask environment..."
echo "Environment variables in systemd service:"
sudo systemctl show insta-automation --property=Environment

echo ""
echo "🔧 RECOMMENDED ACTIONS:"
echo "======================="
echo "Based on the above output, run the appropriate fix script:"
echo "- If SSL certificate is missing: Run enable-ssl-fix.sh"
echo "- If backend is not running: Run fix-backend-service.sh"
echo "- If users.json is missing: Run fix-admin-user.sh"
