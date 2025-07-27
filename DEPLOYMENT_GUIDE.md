# Instagram Automation App - Production Deployment Guide

## 🚀 Production Deployment on Hostinger VPS

### Prerequisites
- Ubuntu/Debian VPS from Hostinger
- Domain name configured to point to your VPS IP
- SSH access to your VPS

### Step 1: Initial VPS Setup

```bash
# Connect to your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Create a new user (replace 'username' with your preferred username)
adduser username
usermod -aG sudo username

# Switch to the new user
su - username
```

### Step 2: Clone and Setup the Project

```bash
# Clone your repository
git clone https://github.com/yourusername/insta-automation.git
cd insta-automation

# Make setup script executable
chmod +x setup-env.sh

# Run the setup script
./setup-env.sh
```

### Step 3: Configure Environment Variables

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

Edit the `.env` file with your actual values:
```env
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
PORT=5000
HOST=0.0.0.0
MAX_CONTENT_LENGTH=104857600
LOG_LEVEL=info
DOMAIN=yourdomain.com
```

### Step 4: Configure Nginx

```bash
# Edit nginx configuration
sudo nano /etc/nginx/sites-available/insta-automation
```

Update the server_name with your domain:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

### Step 5: Start Services

```bash
# Start the application
sudo systemctl start insta-automation
sudo systemctl enable insta-automation

# Restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status insta-automation
sudo systemctl status nginx
```

### Step 6: Setup SSL Certificate

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 7: Configure Firewall

```bash
# Install and configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status
```

## 📋 Post-Deployment Checklist

- [ ] Application is running on your domain
- [ ] SSL certificate is installed and working
- [ ] Authentication system is working
- [ ] File uploads are working
- [ ] All three automation features are accessible
- [ ] Logs are being written properly
- [ ] Services restart automatically after reboot

## 🔧 Maintenance Commands

### View Application Logs
```bash
# View application logs
sudo journalctl -u insta-automation -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# View application-specific logs
tail -f /var/www/insta-automation/logs/gunicorn_access.log
tail -f /var/www/insta-automation/logs/gunicorn_error.log
```

### Deploy Updates
```bash
cd /var/www/insta-automation
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

### Restart Services
```bash
sudo systemctl restart insta-automation
sudo systemctl restart nginx
```

## 🔒 Security Considerations

1. **Change Default Passwords**: Update all default passwords in users.json
2. **Firewall**: Only allow necessary ports (22, 80, 443)
3. **SSL**: Always use HTTPS in production
4. **Environment Variables**: Never commit .env files to git
5. **Regular Updates**: Keep system and dependencies updated
6. **Backups**: Set up regular backups of your data

## 🐛 Troubleshooting

### Application won't start
```bash
# Check logs
sudo journalctl -u insta-automation -n 50

# Check if port is in use
sudo netstat -tlnp | grep :5000

# Restart service
sudo systemctl restart insta-automation
```

### Nginx issues
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx status
sudo systemctl status nginx

# Restart nginx
sudo systemctl restart nginx
```

### SSL certificate issues
```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

## 📞 Support

If you encounter issues during deployment:
1. Check the logs first
2. Ensure all environment variables are set correctly
3. Verify that your domain DNS is pointing to your VPS IP
4. Make sure all required ports are open

## 🚀 GitHub Repository Setup

1. Create a new repository on GitHub
2. Add the remote origin:
   ```bash
   git remote add origin https://github.com/yourusername/insta-automation.git
   ```
3. Push your code:
   ```bash
   git add .
   git commit -m "Initial production-ready version"
   git push -u origin main
   ```

## Domain Connection

1. In your Hostinger control panel, point your domain to your VPS IP
2. Update the nginx configuration with your domain name
3. Get SSL certificate using certbot
4. Test the connection

Your application will be live at: `https://yourdomain.com`
