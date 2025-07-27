#!/bin/bash

# Fix for 401 Unauthorized Error - Enable HTTPS with SSL

echo "🔧 Fixing SSL Configuration for wdyautomation.shop"

# Step 1: Install Certbot if not already installed
echo "📦 Installing Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Step 2: Get SSL Certificate
echo "🔐 Obtaining SSL Certificate..."
sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop --non-interactive --agree-tos --email your-email@example.com

# Step 3: Update Nginx configuration to force HTTPS
echo "⚙️ Updating Nginx configuration..."
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

# Step 4: Test and reload Nginx
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid. Reloading..."
    sudo systemctl reload nginx
    echo "🎉 SSL enabled successfully!"
    echo "🔗 Your site should now work at: https://wdyautomation.shop"
else
    echo "❌ Nginx configuration error. Please check the config."
    exit 1
fi

# Step 5: Set up auto-renewal
echo "⏰ Setting up SSL certificate auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo "🎯 SSL Fix Complete!"
echo "📝 Next steps:"
echo "   1. Test your site at: https://wdyautomation.shop"
echo "   2. Verify login functionality works"
echo "   3. Check that API requests are now successful"
