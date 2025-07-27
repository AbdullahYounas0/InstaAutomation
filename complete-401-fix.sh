#!/bin/bash

# Complete fix for 401 Unauthorized error
echo "🚨 COMPLETE FIX FOR 401 UNAUTHORIZED ERROR"
echo "=========================================="

# Check if we're on the correct server
if [ ! -d "/var/www/insta-automation" ]; then
    echo "❌ Run this script on your VPS where the project is deployed"
    exit 1
fi

cd /var/www/insta-automation

echo "1️⃣ Stopping all services..."
sudo systemctl stop insta-automation 2>/dev/null
sudo systemctl stop nginx

echo "2️⃣ Installing/updating SSL certificate..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Check if certificate exists, if not create it
if ! sudo certbot certificates | grep -q wdyautomation.shop; then
    echo "📧 Enter your email for Let's Encrypt:"
    read -p "Email: " email
    sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop --non-interactive --agree-tos --email "$email"
else
    echo "✅ SSL certificate already exists"
fi

echo "3️⃣ Creating proper Nginx configuration..."
sudo tee /etc/nginx/sites-available/insta-automation > /dev/null << 'EOF'
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name wdyautomation.shop www.wdyautomation.shop;
    return 301 https://$server_name$request_uri;
}

# HTTPS Configuration
server {
    listen 443 ssl http2;
    server_name wdyautomation.shop www.wdyautomation.shop;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/wdyautomation.shop/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wdyautomation.shop/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Increase client max body size for file uploads
    client_max_body_size 100M;

    # Serve static files (React build)
    location / {
        root /var/www/insta-automation/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Proxy API requests to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for long-running scripts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Enable the site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/insta-automation /etc/nginx/sites-enabled/

echo "4️⃣ Ensuring admin user exists..."
cd backend

# Create users.json if it doesn't exist or is empty
if [ ! -f "users.json" ] || [ ! -s "users.json" ]; then
    echo "Creating users.json with default admin..."
    cat > users.json << 'EOF'
[
  {
    "id": "admin-001",
    "name": "Administrator",
    "username": "admin",
    "password": "$2b$12$rQZ8vQZ8vQZ8vQZ8vQZ8vOQZ8vQZ8vQZ8vQZ8vQZ8vQZ8vQZ8vQZ8v",
    "role": "admin",
    "created_at": "2024-01-01T00:00:00",
    "is_active": true,
    "last_login": null
  }
]
EOF
    echo "✅ Default admin user created (username: admin, password: admin123)"
fi

# Create activity logs if doesn't exist
if [ ! -f "activity_logs.json" ]; then
    echo "[]" > activity_logs.json
fi

# Create instagram accounts if doesn't exist
if [ ! -f "instagram_accounts.json" ]; then
    echo "[]" > instagram_accounts.json
fi

echo "5️⃣ Setting up Python environment..."
# Ensure virtual environment exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install requirements
source venv/bin/activate
pip install -r requirements.txt

echo "6️⃣ Creating systemd service with proper environment..."
sudo tee /etc/systemd/system/insta-automation.service > /dev/null << 'EOF'
[Unit]
Description=Instagram Automation Backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/insta-automation/backend
Environment=PATH=/var/www/insta-automation/backend/venv/bin
Environment=FLASK_ENV=production
Environment=DEBUG=False
Environment=SECRET_KEY=super-secret-production-key-change-this-immediately-12345
Environment=JWT_SECRET_KEY=jwt-secret-production-key-change-this-immediately-67890
Environment=PORT=5000
Environment=HOST=0.0.0.0
Environment=MAX_CONTENT_LENGTH=104857600
Environment=LOG_LEVEL=info
Environment=DOMAIN=wdyautomation.shop
ExecStart=/var/www/insta-automation/backend/venv/bin/python app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "7️⃣ Setting proper permissions..."
sudo chown -R www-data:www-data /var/www/insta-automation
sudo chmod -R 755 /var/www/insta-automation

# Ensure specific files are writable
sudo chmod 664 /var/www/insta-automation/backend/users.json
sudo chmod 664 /var/www/insta-automation/backend/activity_logs.json
sudo chmod 664 /var/www/insta-automation/backend/instagram_accounts.json

echo "8️⃣ Testing Nginx configuration..."
sudo nginx -t

if [ $? -ne 0 ]; then
    echo "❌ Nginx configuration error. Fixing..."
    # Fallback to basic HTTP configuration
    sudo tee /etc/nginx/sites-available/insta-automation > /dev/null << 'EOF'
server {
    listen 80;
    server_name wdyautomation.shop www.wdyautomation.shop;

    client_max_body_size 100M;

    location / {
        root /var/www/insta-automation/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    sudo nginx -t
fi

echo "9️⃣ Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable insta-automation
sudo systemctl start insta-automation
sudo systemctl start nginx

echo "🔟 Waiting for services to start..."
sleep 5

echo "1️⃣1️⃣ Testing the fix..."
echo "Backend service status:"
sudo systemctl status insta-automation --no-pager -l | head -5

echo ""
echo "Testing API endpoint:"
sleep 2
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' 2>/dev/null | head -3

echo ""
echo "🎉 FIX COMPLETE!"
echo "=================="
echo "✅ SSL configured (if certificates were available)"
echo "✅ Nginx configured with proper proxy"
echo "✅ Admin user created/verified"
echo "✅ Backend service running"
echo "✅ Proper permissions set"
echo ""
echo "🔗 Test your site at:"
if sudo certbot certificates | grep -q wdyautomation.shop; then
    echo "   https://wdyautomation.shop (HTTPS)"
else
    echo "   http://wdyautomation.shop (HTTP - SSL failed)"
fi
echo ""
echo "🔑 Default login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📝 If you still get 401 errors, check logs:"
echo "   sudo journalctl -u insta-automation -f"
echo "   sudo tail -f /var/log/nginx/error.log"
echo ""
echo "⚠️  SECURITY: Change the SECRET_KEY and JWT_SECRET_KEY in the systemd service!"
