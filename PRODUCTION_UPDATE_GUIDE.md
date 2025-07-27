# Production Deployment & Update Guide
## Instagram Automation App - Live Site Management

### 🚀 **Why Use Automated Deployment?**

**Automated Script Method is RECOMMENDED** because:
- ✅ **One Command Deployment**: Just run `./deploy.sh` and everything is done  
- ✅ **No Human Error**: You can't forget steps or make typos  
- ✅ **Consistent**: Same process every time  
- ✅ **Time Saving**: Takes 30 seconds instead of 5 minutes  
- ✅ **Professional**: Industry standard practice  
- ✅ **Status Checking**: Automatically checks if deployment worked  
- ✅ **Easy for Team**: Anyone can deploy with one command  

---

## 📋 **Initial Setup (One-Time Only)**

### **Step 1: Create Deployment Script**

```bash
# SSH to your VPS
ssh username@your-vps-ip

# Create the deployment script
nano /var/www/instaAutomation/deploy.sh
```

**Copy and paste this complete script:**

```bash
#!/bin/bash

echo "🚀 Starting deployment for wdyautomation.shop..."

# Navigate to project directory
cd /var/www/instaAutomation

# Check if git repo is clean
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️ Warning: Local changes detected. Stashing them..."
    git stash
fi

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Check if requirements changed
if git diff HEAD~1 HEAD --name-only | grep -q "backend/requirements.txt"; then
    echo "🐍 Requirements changed. Updating Python dependencies..."
    pip install -r backend/requirements.txt
else
    echo "🐍 Python dependencies up to date."
fi

# Check if frontend changed
if git diff HEAD~1 HEAD --name-only | grep -q "frontend/"; then
    echo "⚛️ Frontend changes detected. Rebuilding..."
    cd frontend
    if git diff HEAD~1 HEAD --name-only | grep -q "frontend/package.json"; then
        echo "📦 Package.json changed. Updating npm packages..."
        npm install
    fi
    npm run build
    cd ..
else
    echo "⚛️ No frontend changes detected."
fi

# Set correct permissions
sudo chown -R www-data:www-data /var/www/instaAutomation

# Restart services
echo "🔄 Restarting application service..."
sudo systemctl restart insta-automation

# Wait a moment for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet insta-automation; then
    echo "✅ Application service is running!"
else
    echo "❌ Application service failed to start!"
    sudo systemctl status insta-automation --no-pager -l
    exit 1
fi

# Test if site is responding
echo "🌐 Testing site response..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302"; then
    echo "✅ Site is responding correctly!"
else
    echo "⚠️ Site might not be responding properly. Check nginx logs."
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "🌐 Your site is live at: https://wdyautomation.shop"
echo "📊 To monitor logs: sudo journalctl -u insta-automation -f"
```

### **Step 2: Make Script Executable**

```bash
# Make deployment script executable
chmod +x /var/www/instaAutomation/deploy.sh
```

### **Step 3: Create Deployment Alias (Optional but Recommended)**

```bash
# Add deployment alias to your profile
echo 'alias deploy="cd /var/www/instaAutomation && ./deploy.sh"' >> ~/.bashrc
source ~/.bashrc
```

**Now you can deploy from anywhere with just:** `deploy`

---

## 🔄 **Daily Workflow: Making Updates**

### **Method A: Basic Workflow**

#### **On Your Local Machine:**
```bash
# 1. Make your code changes
# 2. Test locally to ensure everything works
# 3. Commit and push to GitHub
git add .
git commit -m "Description of your changes"
git push origin main
```

#### **On Your VPS:**
```bash
# SSH to your VPS
ssh username@your-vps-ip

# Deploy with one command
cd /var/www/instaAutomation && ./deploy.sh

# OR if you created the alias:
deploy
```

### **Method B: Advanced Workflow (Recommended)**

#### **Create Local Push-and-Deploy Script:**

```bash
# On your local machine, create this script
nano push-and-deploy.sh
```

**Add this content:**
```bash
#!/bin/bash
echo "🚀 Pushing to GitHub and deploying to production..."

# Check if commit message provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide a commit message"
    echo "Usage: ./push-and-deploy.sh 'Your commit message'"
    exit 1
fi

# Push to GitHub
echo "📤 Pushing changes to GitHub..."
git add .
git commit -m "$1"
git push origin main

# Deploy to VPS (replace 'username' and 'your-vps-ip' with your actual values)
echo "🚀 Deploying to production server..."
ssh username@your-vps-ip "cd /var/www/instaAutomation && ./deploy.sh"

echo "✅ Complete! Your changes are live at https://wdyautomation.shop"
```

```bash
# Make it executable
chmod +x push-and-deploy.sh
```

#### **Usage:**
```bash
# Make your code changes, then:
./push-and-deploy.sh "Added new feature to homepage"
```

**This will automatically push to GitHub AND deploy to your live site!**

---

## 🔧 **Manual Commands (For Specific Scenarios)**

### **Frontend Only Changes:**
```bash
cd /var/www/instaAutomation
git pull origin main
cd frontend
npm run build
cd ..
# No backend restart needed
```

### **Backend Only Changes:**
```bash
cd /var/www/instaAutomation
git pull origin main
sudo systemctl restart insta-automation
```

### **Environment Variables Changed:**
```bash
cd /var/www/instaAutomation
nano .env  # Edit your environment variables
sudo systemctl restart insta-automation
```

### **Dependencies Updated:**
```bash
cd /var/www/instaAutomation
git pull origin main
source venv/bin/activate

# For Python dependencies
pip install -r backend/requirements.txt

# For Node dependencies
cd frontend
npm install
npm run build
cd ..

sudo systemctl restart insta-automation
```

### **Nginx Configuration Changed:**
```bash
cd /var/www/instaAutomation
git pull origin main
sudo cp nginx.conf /etc/nginx/sites-available/insta-automation
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

## 📊 **Monitoring & Troubleshooting**

### **Check Service Status:**
```bash
# Check if your app is running
sudo systemctl status insta-automation

# Check nginx status
sudo systemctl status nginx
```

### **View Logs:**
```bash
# Real-time application logs
sudo journalctl -u insta-automation -f

# Application-specific logs
tail -f /var/www/instaAutomation/logs/gunicorn_error.log
tail -f /var/www/instaAutomation/logs/gunicorn_access.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Test Site Accessibility:**
```bash
# Test from server
curl -I https://wdyautomation.shop

# Test specific endpoints
curl -I https://wdyautomation.shop/api/health
```

---

## 🔙 **Rollback Commands (Emergency)**

### **If Something Goes Wrong:**

```bash
# See git history
cd /var/www/instaAutomation
git log --oneline -10

# Rollback to previous commit
git checkout PREVIOUS_COMMIT_HASH

# Rebuild and restart
cd frontend
npm run build
cd ..
sudo systemctl restart insta-automation

# To return to latest version later
git checkout main
./deploy.sh
```

---

## 🛡️ **Best Practices**

### **Before Every Deployment:**
1. ✅ **Test locally first** - Always ensure your changes work on your local machine
2. ✅ **Use descriptive commit messages** - Makes debugging easier later
3. ✅ **Check logs after deployment** - Ensure no errors occurred
4. ✅ **Test the live site** - Visit your site to confirm it's working

### **Regular Maintenance:**
```bash
# Weekly: Check service status
sudo systemctl status insta-automation nginx

# Monthly: Update system packages
sudo apt update && sudo apt upgrade

# Check disk space
df -h

# Check memory usage
free -h
```

---

## 🚨 **Emergency Contacts & Resources**

### **Quick Status Check:**
```bash
# One-liner to check everything
sudo systemctl status insta-automation nginx && curl -I https://wdyautomation.shop
```

### **Service Restart (if site is down):**
```bash
# Nuclear option - restart everything
sudo systemctl restart insta-automation nginx
```

### **Log Locations:**
- Application logs: `/var/www/instaAutomation/logs/`
- System logs: `sudo journalctl -u insta-automation`
- Nginx logs: `/var/log/nginx/`

---

## 📞 **Support Checklist**

**If deployment fails:**
1. Check the deployment script output for error messages
2. Check service status: `sudo systemctl status insta-automation`
3. Check logs: `sudo journalctl -u insta-automation -n 50`
4. Verify GitHub push was successful
5. Check if VPS has enough disk space: `df -h`
6. Check if VPS has enough memory: `free -h`

**Common issues:**
- **Git conflicts**: The script will stash local changes automatically
- **Permission errors**: Run `sudo chown -R www-data:www-data /var/www/instaAutomation`
- **Port conflicts**: Check if another service is using port 5000
- **Memory issues**: Restart the VPS if needed

---

## 🎯 **Summary**

**Your deployment workflow should be:**

1. **Develop locally** → Test changes
2. **Push to GitHub** → `git push origin main`
3. **Deploy to production** → `ssh to VPS` → `deploy` (or `./deploy.sh`)
4. **Verify** → Check https://wdyautomation.shop

**With the automated script, updates take less than 60 seconds!**

---

*Last updated: July 27, 2025*  
*Site: https://wdyautomation.shop*
