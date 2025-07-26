# Instagram Daily Post - API Documentation

This document describes all the available API endpoints for the Instagram Daily Post automation backend.

## Base URL
```
http://localhost:5000/api
```

## Authentication
No authentication required for local development.

---

## Daily Post Endpoints

### POST `/daily-post/start`
Start Instagram Daily Post automation script.

**Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| accounts_file | File | Yes | Excel (.xlsx, .xls) or CSV file with Username and Password columns |
| media_file | File | Yes | Image or video file to post |
| caption | String | No | Custom caption for posts (empty string for auto-generated) |
| concurrent_accounts | Integer | No | Number of accounts to process simultaneously (default: 5, max: 10) |
| auto_generate_caption | String | No | "true" or "false" - whether to auto-generate captions |

**Response:**
```json
{
  "script_id": "uuid-string",
  "status": "started",
  "message": "Daily post script initiated successfully"
}
```

**Example Usage (JavaScript):**
```javascript
const formData = new FormData();
formData.append('accounts_file', accountsFile);
formData.append('media_file', mediaFile);
formData.append('caption', 'My custom caption');
formData.append('concurrent_accounts', '5');
formData.append('auto_generate_caption', 'false');

const response = await axios.post('/api/daily-post/start', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
```

### POST `/daily-post/validate`
Validate uploaded files before starting the script.

**Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| accounts_file | File | Yes | Excel or CSV file to validate |
| media_file | File | Yes | Media file to validate |

**Response (Success):**
```json
{
  "valid": true,
  "message": "Files validated successfully",
  "accounts_count": 5,
  "media_type": "image"
}
```

**Response (Error):**
```json
{
  "valid": false,
  "errors": ["Missing columns in accounts file: ['Username']"]
}
```

---

## Script Management Endpoints

### GET `/script/{script_id}/status`
Get the current status of a running script.

**Response:**
```json
{
  "type": "daily_post",
  "status": "running",
  "start_time": "2025-07-21T10:30:00.000Z",
  "config": {
    "accounts_file": "/path/to/accounts.xlsx",
    "media_file": "/path/to/image.jpg",
    "caption": "Custom caption",
    "concurrent_accounts": 5,
    "auto_generate_caption": false,
    "is_video": false
  },
  "end_time": "2025-07-21T10:35:00.000Z" // Only present when completed
}
```

**Status Values:**
- `running` - Script is currently executing
- `completed` - Script finished successfully
- `error` - Script encountered an error
- `stopped` - Script was stopped by user

### GET `/script/{script_id}/logs`
Get real-time logs for a specific script.

**Response:**
```json
{
  "logs": [
    "[2025-07-21 10:30:01] [INFO] Daily Post script started with 5 accounts",
    "[2025-07-21 10:30:02] [INFO] Media file: image.jpg (Image)",
    "[2025-07-21 10:30:05] [INFO] [Account 1] Starting automation for username1",
    "[2025-07-21 10:30:08] [SUCCESS] [Account 1] Post completed successfully!"
  ]
}
```

### POST `/script/{script_id}/stop`
Stop a running script.

**Response:**
```json
{
  "status": "stopped",
  "message": "Script stopped successfully"
}
```

### GET `/script/{script_id}/download-logs`
Download script logs as a text file.

**Response:** Text file download with filename `script_{script_id}_logs.txt`

### POST `/script/{script_id}/clear-logs`
Clear logs for a specific script.

**Response:**
```json
{
  "message": "Logs cleared successfully"
}
```

---

## General Endpoints

### GET `/scripts`
List all scripts with their current status.

**Response:**
```json
{
  "uuid-1": {
    "type": "daily_post",
    "status": "completed",
    "start_time": "2025-07-21T10:30:00.000Z",
    "end_time": "2025-07-21T10:35:00.000Z"
  },
  "uuid-2": {
    "type": "daily_post",
    "status": "running",
    "start_time": "2025-07-21T10:40:00.000Z"
  }
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-21T10:30:00.000Z"
}
```

---

## File Format Requirements

### Accounts File (Excel/CSV)
The accounts file must contain the following columns:
- `Username` - Instagram username
- `Password` - Instagram password

**Example:**
```csv
Username,Password
account1,password123
account2,password456
account3,password789
```

### Supported Media Formats

**Images:**
- .jpg, .jpeg, .png, .gif, .bmp, .webp

**Videos:**
- .mp4, .mov, .avi, .mkv, .webm, .m4v

---

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found (script not found)
- `500` - Internal Server Error

**Error Response Format:**
```json
{
  "error": "Error message description"
}
```

---

## Real-time Features

### Log Polling
The frontend can poll the `/script/{script_id}/logs` endpoint every 2-3 seconds to get real-time updates:

```javascript
const pollLogs = () => {
  setInterval(async () => {
    try {
      const response = await axios.get(`/api/script/${scriptId}/logs`);
      setLogs(response.data.logs);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  }, 2000);
};
```

### Status Monitoring
Monitor script status by polling the status endpoint:

```javascript
const checkStatus = async () => {
  try {
    const response = await axios.get(`/api/script/${scriptId}/status`);
    if (response.data.status === 'completed' || response.data.status === 'error') {
      // Script finished
      clearInterval(pollingInterval);
    }
  } catch (error) {
    console.error('Error checking status:', error);
  }
};
```

---

## Security Considerations

1. **File Upload Limits:** The backend validates file types and uses secure filenames
2. **Input Sanitization:** All form inputs are validated and sanitized
3. **Rate Limiting:** Consider implementing rate limiting for production use
4. **CORS:** CORS is enabled for development - configure appropriately for production

---

## Deployment Notes

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Install Playwright browsers: `python -m playwright install chromium`
3. The backend creates `uploads/` and `logs/` directories automatically
4. Log files are kept for the last 1000 entries per script to prevent excessive disk usage
