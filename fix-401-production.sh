#!/bin/bash

# Quick Fix for 401 Unauthorized Error on Production
# Run this script on your VPS as root

echo "🚨 FIXING 401 UNAUTHORIZED ERROR ON PRODUCTION"
echo "================================================"

# Check if we're on the right server
if [ ! -d "/var/www/insta-automation" ]; then
    echo "❌ Project directory not found. Run this on your VPS where the project is deployed."
    exit 1
fi

cd /var/www/insta-automation

echo "1️⃣ Stopping existing services..."
sudo systemctl stop insta-automation
sudo systemctl stop nginx

echo "2️⃣ Installing SSL certificate with Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace your-email@example.com with your actual email)
echo "📧 Please replace 'your-email@example.com' with your actual email address!"
read -p "Enter your email address: " email
sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop --non-interactive --agree-tos --email "$email"

echo "3️⃣ Updating Nginx configuration for HTTPS..."
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

    # SSL Configuration (managed by Certbot)
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

    # Handle file uploads
    location /uploads/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for file uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

echo "4️⃣ Updating systemd service with environment variables..."
sudo tee /etc/systemd/system/insta-automation.service > /dev/null << 'EOF'
[Unit]
Description=Instagram Automation Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/insta-automation/backend
Environment=PATH=/var/www/insta-automation/venv/bin
Environment=FLASK_ENV=production
Environment=DEBUG=False
Environment=SECRET_KEY=your-production-secret-key-change-this-immediately-123456789
Environment=JWT_SECRET_KEY=your-jwt-secret-key-change-this-immediately-987654321
Environment=PORT=5000
Environment=HOST=0.0.0.0
Environment=MAX_CONTENT_LENGTH=104857600
Environment=LOG_LEVEL=info
Environment=DOMAIN=wdyautomation.shop
ExecStart=/var/www/insta-automation/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "5️⃣ Setting proper permissions..."
sudo chown -R www-data:www-data /var/www/insta-automation
sudo chmod -R 755 /var/www/insta-automation

echo "6️⃣ Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid."
else
    echo "❌ Nginx configuration error. Check the logs."
    exit 1
fi

echo "7️⃣ Reloading systemd and restarting services..."
sudo systemctl daemon-reload
sudo systemctl enable insta-automation
sudo systemctl start insta-automation
sudo systemctl start nginx

echo "8️⃣ Setting up SSL auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo "9️⃣ Checking service status..."
sleep 3
echo "Backend service status:"
sudo systemctl status insta-automation --no-pager -l

echo "Nginx status:"
sudo systemctl status nginx --no-pager -l

echo ""
echo "🎉 FIX COMPLETE!"
echo "========================================"
echo "✅ SSL certificate installed"
echo "✅ HTTPS enabled with automatic redirect"
echo "✅ Environment variables configured"
echo "✅ Services restarted"
echo ""
echo "🔗 Test your site at: https://wdyautomation.shop"
echo "🔑 Login should now work properly"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTE:"
echo "   Change the SECRET_KEY and JWT_SECRET_KEY in the systemd service file"
echo "   to more secure random strings before going live!"
echo ""
echo "📝 If you still get errors, check the logs:"
echo "   sudo journalctl -u insta-automation -f"
echo "   sudo tail -f /var/log/nginx/error.log"
