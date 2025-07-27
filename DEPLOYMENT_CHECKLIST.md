# 🚀 VPS Deployment Checklist

## Before You Start
- [ ] Upload your code to GitHub repository
- [ ] Make sure your domain DNS is pointing to your VPS IP address
- [ ] Have SSH access to your VPS
- [ ] Know your GitHub repository URL

## Step-by-Step Deployment

### 1. Clone Repository on VPS
```bash
# SSH into your VPS
ssh root@your-vps-ip

# Navigate to web directory and clone
cd /var/www
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git insta-automation
```

### 2. Run Automated Deployment Script
```bash
# Make script executable
chmod +x /var/www/insta-automation/deploy-vps.sh

# Run deployment script
/var/www/insta-automation/deploy-vps.sh
```

### 3. Manual Steps (if automated script fails)
Follow the detailed guide in `VPS_DEPLOYMENT_GUIDE.md`

### 4. Test Your Deployment
- [ ] Visit https://wdyautomation.shop
- [ ] Try logging in
- [ ] Test API endpoints
- [ ] Check if all features work

### 5. Monitor and Troubleshoot
```bash
# Check backend service
sudo systemctl status insta-automation

# Check backend logs
sudo journalctl -u insta-automation -f

# Check nginx
sudo systemctl status nginx

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

## Important Files Updated
- ✅ All API URLs changed from localhost to wdyautomation.shop
- ✅ Frontend rebuilt with production URLs
- ✅ BrowserCloseDetector import fixed
- ✅ Nginx configuration updated for HTTPS
- ✅ Deployment scripts created

## Quick Commands for VPS

### Restart Services
```bash
sudo systemctl restart insta-automation
sudo systemctl restart nginx
```

### Update Application (after GitHub changes)
```bash
cd /var/www/insta-automation
git pull origin main

# If backend changes
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart insta-automation

# If frontend changes
cd ../frontend
npm install
npm run build
sudo systemctl restart nginx
```

### Check Status
```bash
# Services status
sudo systemctl status insta-automation nginx

# Check if ports are open
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :443

# Test API
curl https://wdyautomation.shop/api/health
```

## Security Notes
- [ ] SSL certificate will be automatically configured
- [ ] Firewall configured to allow only necessary ports
- [ ] Application running under www-data user (not root)

## If Something Goes Wrong
1. Check the logs first
2. Verify your domain DNS settings
3. Make sure your VPS firewall allows HTTP/HTTPS traffic
4. Ensure the backend service is running on port 5000

## Contact Info
If you need help, share the error logs from:
- `sudo journalctl -u insta-automation --no-pager`
- `sudo tail -n 50 /var/log/nginx/error.log`
