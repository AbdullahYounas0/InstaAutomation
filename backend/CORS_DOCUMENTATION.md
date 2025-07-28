# CORS Implementation Documentation

## Overview
This backend implements a comprehensive Cross-Origin Resource Sharing (CORS) system to handle requests from the React frontend and other authorized origins.

## Features

### 1. Enhanced CORS Configuration
- **Environment Variable Support**: CORS origins can be configured via environment variables
- **Multiple Origins**: Supports multiple frontend domains/ports
- **Development Defaults**: Automatically includes common development ports
- **Production Ready**: Easy configuration for production domains

### 2. Security Headers
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-XSS-Protection**: Enables XSS filtering

### 3. Comprehensive Method Support
- GET, POST, PUT, DELETE, OPTIONS, PATCH
- Proper preflight handling for complex requests

### 4. Header Management
- **Allowed Headers**: Content-Type, Authorization, X-Requested-With, etc.
- **Exposed Headers**: Content-Range, Authorization, Content-Disposition
- **Credentials Support**: Enables sending cookies and authorization headers

## Configuration

### Environment Variables

```bash
# Set allowed origins (comma-separated)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,http://localhost:3000

# Set preflight cache duration (seconds)
CORS_MAX_AGE=86400
```

### Default Development Origins
If no `CORS_ORIGINS` environment variable is set, the following are allowed:
- `http://localhost:3000` (React dev server)
- `http://127.0.0.1:3000`
- `http://localhost:8080`
- `http://127.0.0.1:8080`

## Testing CORS

### Test Endpoint
The backend includes a CORS test endpoint:

```
GET/POST /api/cors-test
```

This endpoint returns:
- CORS status
- Request method
- Origin header
- Current CORS configuration
- Timestamp

### Frontend Testing
```javascript
// Test CORS from your React frontend
fetch('http://localhost:5000/api/cors-test', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-token'
  },
  credentials: 'include',
  body: JSON.stringify({ test: 'data' })
})
.then(response => response.json())
.then(data => console.log('CORS Test:', data))
.catch(error => console.error('CORS Error:', error));
```

## Production Deployment

### 1. Set Environment Variables
```bash
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
export CORS_MAX_AGE=86400
```

### 2. Update Your Frontend
Ensure your React frontend is configured to make requests to your production backend URL.

### 3. SSL/HTTPS
For production, ensure both frontend and backend use HTTPS to avoid mixed content issues.

## Error Handling

### CORS Errors
If you encounter CORS errors:

1. **Check Origins**: Ensure your frontend domain is in the allowed origins list
2. **Check Methods**: Verify the HTTP method is in the allowed methods list
3. **Check Headers**: Ensure all custom headers are in the allowed headers list
4. **Check Credentials**: If using authentication, ensure credentials are enabled

### Common Issues

#### 1. Origin Not Allowed
```
Access to fetch at 'backend-url' from origin 'frontend-url' has been blocked by CORS policy
```
**Solution**: Add your frontend URL to `CORS_ORIGINS` environment variable

#### 2. Method Not Allowed
```
Method POST is not allowed by Access-Control-Allow-Methods
```
**Solution**: The method should already be allowed, check your request

#### 3. Header Not Allowed
```
Request header 'custom-header' is not allowed by Access-Control-Allow-Headers
```
**Solution**: Add the header to the `allow_headers` list in the CORS configuration

## Browser Support
This CORS implementation supports all modern browsers that support:
- XMLHttpRequest Level 2
- Fetch API
- Preflight requests

## Security Considerations

1. **Specific Origins**: Avoid using `*` for origins in production
2. **HTTPS Only**: Use HTTPS in production for secure credential transmission
3. **Header Validation**: Only allow necessary headers
4. **Method Restriction**: Only allow required HTTP methods

## Monitoring

### Logs
CORS requests are logged with the following information:
- Origin
- Method
- Headers
- Response status

### Metrics
Monitor these metrics:
- CORS preflight requests
- CORS errors
- Origin distribution
- Method usage

## Integration with Authentication

The CORS system works seamlessly with the JWT authentication system:
- Authorization headers are properly handled
- Credentials are supported for authenticated requests
- Token refresh works across origins

## Testing Commands

```bash
# Test basic CORS
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     -X OPTIONS \
     http://localhost:5000/api/cors-test

# Test authenticated CORS
curl -H "Origin: http://localhost:3000" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-jwt-token" \
     -X POST \
     http://localhost:5000/api/cors-test
```
