# VPS Deployment Guide for Instagram Automation System

## Prerequisites
- VPS with Ubuntu/Debian
- Domain: wdyautomation.shop pointing to your VPS IP
- SSH access to your VPS
- Git installed on VPS

## Step 1: Clone Repository on VPS

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Navigate to web directory
cd /var/www

# Clone your GitHub repository
git clone https://github.com/yourusername/instaUI2.git insta-automation

# Navigate to project directory
cd insta-automation
```

## Step 2: Install Dependencies

### Backend Dependencies
```bash
# Install Python and pip if not already installed
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Frontend Dependencies
```bash
# Install Node.js and npm if not already installed
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Navigate to frontend directory
cd ../frontend

# Install npm dependencies
npm install

# Build production version
npm run build
```

## Step 3: Configure Environment Variables

```bash
# Create .env file in backend directory
cd ../backend
nano .env
```

Add the following to your `.env` file:
```env
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
PORT=5000
MAX_CONTENT_LENGTH=104857600
```

## Step 4: Configure Nginx

```bash
# Install Nginx if not already installed
sudo apt install nginx

# Copy your nginx configuration
sudo cp /var/www/insta-automation/nginx.conf /etc/nginx/sites-available/insta-automation

# Create symbolic link
sudo ln -s /etc/nginx/sites-available/insta-automation /etc/nginx/sites-enabled/

# Remove default site if it exists
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Step 5: Setup SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop

# Auto-renewal setup (should be automatic)
sudo systemctl enable certbot.timer
```

## Step 6: Create Systemd Service for Backend

```bash
# Create service file
sudo nano /etc/systemd/system/insta-automation.service
```

Add the following content:
```ini
[Unit]
Description=Instagram Automation Flask App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/insta-automation/backend
Environment=PATH=/var/www/insta-automation/backend/venv/bin
ExecStart=/var/www/insta-automation/backend/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Step 7: Start Services

```bash
# Set proper permissions
sudo chown -R www-data:www-data /var/www/insta-automation
sudo chmod -R 755 /var/www/insta-automation

# Enable and start the service
sudo systemctl enable insta-automation
sudo systemctl start insta-automation

# Check service status
sudo systemctl status insta-automation

# Check nginx status
sudo systemctl status nginx
```

## Step 8: Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

## Step 9: Verify Deployment

1. Check if backend is running:
```bash
curl http://localhost:5000/api/health
```

2. Check if frontend is accessible:
```bash
curl https://wdyautomation.shop
```

3. Test API endpoints:
```bash
curl https://wdyautomation.shop/api/health
```

## Troubleshooting Commands

```bash
# Check backend logs
sudo journalctl -u insta-automation -f

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Restart services
sudo systemctl restart insta-automation
sudo systemctl restart nginx

# Check if ports are open
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## Updating the Application

When you make changes to your GitHub repository:

```bash
# SSH into VPS
cd /var/www/insta-automation

# Pull latest changes
git pull origin main

# Update backend (if backend changes)
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart insta-automation

# Update frontend (if frontend changes)
cd ../frontend
npm install
npm run build
sudo systemctl restart nginx
```

## Common Issues and Solutions

1. **Permission Denied**: Make sure www-data owns the files
2. **Port 5000 in use**: Check what's using the port with `sudo lsof -i :5000`
3. **SSL Issues**: Make sure your domain DNS is pointing to your VPS IP
4. **Backend not starting**: Check logs with `sudo journalctl -u insta-automation`

## Security Notes

- Change default passwords in your application
- Keep your system updated: `sudo apt update && sudo apt upgrade`
- Monitor logs regularly
- Consider setting up fail2ban for additional security
