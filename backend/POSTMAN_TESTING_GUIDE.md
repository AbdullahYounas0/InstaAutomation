# Postman Testing Guide for wdyautomation.shop

## 🚀 **Testing Live Project on wdyautomation.shop**

This guide will help you test the Instagram automation API endpoints on your live production server using Postman.

### **Base URL**
```
https://wdyautomation.shop
```

## 📋 **Step-by-Step Testing Process**

### **1. Setup Postman Environment**

Create a new Postman environment with these variables:

| Variable Name | Initial Value | Current Value |
|---------------|---------------|---------------|
| `base_url` | `https://wdyautomation.shop` | `https://wdyautomation.shop` |
| `token` | (leave empty) | (will be set after login) |
| `user_id` | (leave empty) | (will be set after login) |

### **2. Test Basic Connectivity**

**Request 1: Health Check**
```
Method: GET
URL: {{base_url}}/api/health
Headers: None required
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T..."
}
```

### **3. Test CORS Configuration**

**Request 2: CORS Test**
```
Method: GET
URL: {{base_url}}/api/cors-test
Headers:
  Origin: https://your-frontend-domain.com
```

**Expected Response:**
```json
{
  "status": "CORS working",
  "method": "GET",
  "origin": "https://your-frontend-domain.com",
  "timestamp": "2025-01-28T...",
  "cors_config": {
    "allowed_origins": [...],
    "allowed_methods": [...],
    "supports_credentials": true
  }
}
```

### **4. Test User Authentication**

#### **Login Request**
```
Method: POST
URL: {{base_url}}/api/auth/login
Headers:
  Content-Type: application/json
Body (JSON):
{
  "username": "your_username",
  "password": "your_password"
}
```

#### **Default Admin Credentials**
If you haven't changed them, try these default credentials:

**Admin User:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Test VA User:**
```json
{
  "username": "test_va",
  "password": "password123"
}
```

#### **Expected Login Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "user_id": "uuid-here",
    "username": "admin",
    "name": "Admin User",
    "role": "admin",
    "is_active": true
  }
}
```

#### **Postman Test Script for Login**
Add this to the "Tests" tab of your login request:
```javascript
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
    pm.expect(jsonData.token).to.exist;
    
    // Store token for future requests
    pm.environment.set("token", jsonData.token);
    pm.environment.set("user_id", jsonData.user.user_id);
    
    console.log("Token stored:", jsonData.token);
});
```

### **5. Test Protected Endpoints**

After successful login, test protected endpoints using the stored token:

#### **Get All Users (Admin Only)**
```
Method: GET
URL: {{base_url}}/api/admin/users
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
```

#### **Get Instagram Accounts**
```
Method: GET
URL: {{base_url}}/api/instagram-accounts
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
```

#### **Get Script Statistics**
```
Method: GET
URL: {{base_url}}/api/scripts/stats
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
```

### **6. Test Script Endpoints**

#### **Get Active Scripts**
```
Method: GET
URL: {{base_url}}/api/scripts
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
```

### **7. Test File Upload Endpoints**

#### **Daily Post Validation**
```
Method: POST
URL: {{base_url}}/api/daily-post/validate
Headers:
  Authorization: Bearer {{token}}
Body: form-data
  accounts_file: [Upload CSV/Excel file]
  media_file: [Upload image/video file]
```

## 🔧 **Troubleshooting Common Issues**

### **Issue 1: Login Fails with 401**
**Possible causes:**
- Wrong username/password
- User account is deactivated
- Database connection issues

**Solutions:**
1. Try default credentials
2. Check server logs
3. Verify database is accessible

### **Issue 2: CORS Errors**
**Error message:** `Access-Control-Allow-Origin`
**Solution:** Add your frontend domain to CORS_ORIGINS environment variable

### **Issue 3: SSL Certificate Issues**
**Error:** SSL verification failed
**Solution:** In Postman settings, turn off "SSL certificate verification"

### **Issue 4: Token Expired**
**Error:** 401 after some time
**Solution:** Login again to get a new token

## 📚 **Complete Postman Collection**

### **Authentication Flow Test**
```javascript
// Pre-request Script for protected endpoints
if (!pm.environment.get("token")) {
    throw new Error("Please login first to get authentication token");
}
```

### **Global Test Script**
```javascript
// Add to collection level tests
pm.test("Response time is reasonable", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

pm.test("No server errors", function () {
    pm.expect(pm.response.code).to.not.be.oneOf([500, 502, 503, 504]);
});
```

## 🔍 **Testing Checklist**

- [ ] Health check endpoint responds
- [ ] CORS configuration works
- [ ] Admin login successful
- [ ] VA user login successful
- [ ] Token authentication works
- [ ] Protected endpoints require auth
- [ ] File upload endpoints work
- [ ] Script management endpoints work
- [ ] Error handling works properly

## 📊 **Production Testing Notes**

### **Server Information**
- **Domain:** wdyautomation.shop
- **Protocol:** HTTPS (SSL enabled)
- **Backend Port:** 5000 (reverse proxied through Nginx)
- **Database:** File-based JSON storage

### **Security Considerations**
1. Always use HTTPS in production
2. Tokens expire after 24 hours by default
3. Rate limiting may be in place
4. File uploads are limited to 100MB

### **Performance Testing**
- Test concurrent logins
- Test large file uploads
- Test long-running scripts
- Monitor response times

## 🚨 **Emergency Contacts**

If you encounter issues:
1. Check server logs: `tail -f /var/log/insta-automation.log`
2. Restart service: `sudo systemctl restart insta-automation`
3. Check SSL certificate: `sudo certbot certificates`

## 📝 **Sample Test Requests**

Copy these into Postman:

### **1. Login Test**
```bash
curl -X POST https://wdyautomation.shop/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### **2. Protected Endpoint Test**
```bash
curl -X GET https://wdyautomation.shop/api/scripts/stats \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **3. Health Check**
```bash
curl -X GET https://wdyautomation.shop/api/health
```

---

**💡 Pro Tip:** Use Postman's environment variables to easily switch between development and production environments!
