# Instagram Automation Platform

A full-stack web application for Instagram automation including daily posting, DM automation, and account warmup functionality.

## 🚀 Features

- **Daily Post Automation**: Automated posting with media upload support
- **DM Automation**: AI-powered personalized messaging campaigns
- **Account Warmup**: Human-like behavior simulation for account trust building
- **Multi-Account Support**: Handle multiple Instagram accounts concurrently
- **Real-time Logging**: Live status updates and detailed logging
- **Visual Mode**: Watch automation in real-time (development)

## 🏗️ Architecture

### Frontend (React + TypeScript)
- Modern React application with TypeScript
- Responsive design for mobile and desktop
- Real-time log streaming
- File upload handling

### Backend (FastAPI + Python)
- High-performance FastAPI server
- Async/await support for concurrent operations
- Playwright browser automation
- JWT authentication system

## 🛠️ Local Development

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python start_development.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 🚀 Production Deployment

### Prerequisites
- Ubuntu/Debian VPS
- Domain name (wdyautomation.shop)
- Hostinger VPS or similar

### Quick Deployment
1. Clone the repository to your VPS
2. Make the deployment script executable: `chmod +x deploy.sh`
3. Run the deployment script: `./deploy.sh`

### Manual Deployment Steps

#### 1. System Setup
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx git curl nodejs npm certbot python3-certbot-nginx
```

#### 2. Application Setup
```bash
sudo mkdir -p /var/www/instaAutomation
cd /var/www/instaAutomation
git clone https://github.com/yourusername/instaAutomation.git .
```

#### 3. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

#### 4. Frontend Setup
```bash
cd ../frontend
npm install
NODE_ENV=production npm run build
```

#### 5. System Service Setup
```bash
sudo cp insta-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable insta-automation
sudo systemctl start insta-automation
```

#### 6. Nginx Configuration
```bash
sudo cp nginx.conf /etc/nginx/sites-available/wdyautomation.shop
sudo ln -sf /etc/nginx/sites-available/wdyautomation.shop /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. SSL Certificate
```bash
sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop
```

## 📝 Environment Configuration

### Backend Environment Variables (.env.production)
```env
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://wdyautomation.shop,https://www.wdyautomation.shop
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this
LOG_LEVEL=INFO
```

## 🔧 Maintenance Commands

### Check Service Status
```bash
sudo systemctl status insta-automation
sudo systemctl status nginx
```

### View Logs
```bash
# Backend logs
sudo journalctl -f -u insta-automation

# Nginx logs
sudo tail -f /var/log/nginx/wdyautomation_error.log
```

### Restart Services
```bash
sudo systemctl restart insta-automation
sudo systemctl restart nginx
```

### Update Application
```bash
cd /var/www/instaAutomation
git pull origin main
cd frontend && npm run build
sudo systemctl restart insta-automation
```

## 🛡️ Security Features

- JWT token-based authentication
- CORS protection
- Rate limiting
- HTTPS encryption
- Secure file upload handling
- Environment-based configuration

## 📊 Monitoring

- Real-time logging system
- Service status monitoring via systemd
- Nginx access and error logs
- Application performance tracking

## 🆘 Troubleshooting

### Common Issues

1. **Service won't start**: Check logs with `sudo journalctl -u insta-automation`
2. **Frontend not loading**: Verify nginx configuration and build files
3. **Playwright issues**: Ensure system dependencies are installed
4. **Permission errors**: Check file ownership and permissions

### Debug Mode

For debugging, you can run the backend in development mode:
```bash
cd /var/www/instaAutomation/backend
source venv/bin/activate
python start_development.py
```

## 📞 Support

For issues and support, check the application logs and service status first. Common solutions can be found in the troubleshooting section above.

## 🔄 Updates

To update the application:
1. Pull latest changes from git
2. Rebuild frontend if needed
3. Restart services
4. Monitor logs for any issues

## 📜 License

This project is for educational and personal use only. Please comply with Instagram's Terms of Service and applicable laws.
