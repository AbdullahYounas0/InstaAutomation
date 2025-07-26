# DM Automation API Documentation

## Overview
The DM Automation API provides endpoints for managing Instagram direct message campaigns with AI-powered personalization.

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Start DM Automation
**POST** `/dm-automation/start`

Starts a new Instagram DM automation campaign.

#### Request Format
- **Content-Type**: `multipart/form-data`

#### Form Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `accounts_file` | File | Yes | CSV/Excel file containing bot Instagram accounts |
| `target_file` | File | No | CSV/Excel file containing target users to DM |
| `dm_prompt_file` | File | No | Text file containing DM message template |
| `custom_prompt` | String | No | Custom DM prompt (alternative to file upload) |
| `accounts_to_use` | Integer | No | Number of bot accounts to use (1-10, default: 3) |
| `dms_per_account` | Integer | No | Number of DMs per account (1-100, default: 30) |

#### Bot Accounts File Format
CSV/Excel file with columns:
```csv
Username,Password
bot_account1,password123
bot_account2,password456
```

#### Target Accounts File Format (Optional)
CSV/Excel file with columns:
```csv
username,first_name,city,bio
target_user1,John,New York,entrepreneur
target_user2,Jane,Los Angeles,marketing manager
```

#### Response Format
```json
{
  "script_id": "uuid-string",
  "status": "started",
  "message": "DM automation script initiated successfully"
}
```

#### Error Response
```json
{
  "error": "Error message describing what went wrong"
}
```

### 2. Validate DM Files
**POST** `/dm-automation/validate`

Validates uploaded files before starting the automation.

#### Request Format
Same as start endpoint, but only validates files without starting the script.

#### Response Format
```json
{
  "valid": true,
  "message": "Files validated successfully",
  "bot_accounts_count": 5,
  "target_accounts_count": 100,
  "warnings": ["No target file provided - will use default target list"]
}
```

### 3. Get Script Status
**GET** `/script/{script_id}/status`

Gets the current status of a running DM automation script.

#### Response Format
```json
{
  "type": "dm_automation",
  "status": "running",
  "start_time": "2025-01-21T10:30:00",
  "end_time": null,
  "config": {
    "accounts_to_use": 3,
    "dms_per_account": 30,
    "deepseek_api_key": "sk-..."
  },
  "error": null
}
```

### 4. Get Script Logs
**GET** `/script/{script_id}/logs`

Gets real-time logs from the DM automation script.

#### Response Format
```json
{
  "logs": [
    "[10:30:01] [INFO] DM Automation script started",
    "[10:30:05] [INFO] Loaded 3 bot accounts",
    "[10:30:10] [INFO] [bot1] Login successful!",
    "[10:30:15] [INFO] [bot1] DM sent to target_user1 (1/30)"
  ]
}
```

### 5. Stop Script
**POST** `/script/{script_id}/stop`

Stops a running DM automation script.

#### Response Format
```json
{
  "status": "stopped",
  "message": "Script stopped successfully"
}
```

## Script Status Values

| Status | Description |
|--------|-------------|
| `running` | Script is currently executing |
| `completed` | Script finished successfully |
| `stopped` | Script was stopped by user |
| `error` | Script encountered an error |

## Log Levels

| Level | Description |
|-------|-------------|
| `INFO` | General information messages |
| `SUCCESS` | Successful operations |
| `WARNING` | Non-critical issues |
| `ERROR` | Critical errors |

## Features

### AI-Powered Message Generation
- Uses DeepSeek AI API for personalized message creation
- Incorporates user data (name, city, bio) for personalization
- Fallback to template messages if AI is unavailable

### Proxy Support
- Automatic proxy rotation for multiple accounts
- Built-in proxy pool with authentication
- Proxy failure handling and retry logic

### Rate Limiting & Safety
- Human-like delays between DMs (10-20 seconds)
- Account-specific rate limiting
- Browser automation with stealth mode

### Real-Time Monitoring
- Live log streaming
- Progress tracking per account
- Success/failure statistics

### Result Tracking
- CSV export of sent DMs
- Positive response detection
- Campaign performance metrics

## Error Handling

### Common Errors
- **"Bot accounts file is required"**: No accounts file uploaded
- **"Invalid accounts file format"**: File is not CSV/Excel
- **"No valid bot accounts found"**: File is empty or has invalid data
- **"Login failed"**: Instagram credentials are incorrect
- **"Script execution failed"**: General automation failure

### File Validation Errors
- Missing required columns in accounts file
- Empty files
- Corrupted file formats
- Encoding issues

## Usage Examples

### cURL Examples

#### Start DM Campaign
```bash
curl -X POST http://localhost:5000/api/dm-automation/start \
  -F "accounts_file=@bot_accounts.csv" \
  -F "target_file=@targets.csv" \
  -F "custom_prompt=Hi {first_name}! Interested in VA services?" \
  -F "accounts_to_use=3" \
  -F "dms_per_account=25"
```

#### Check Status
```bash
curl http://localhost:5000/api/script/uuid-here/status
```

#### Stop Script
```bash
curl -X POST http://localhost:5000/api/script/uuid-here/stop
```

### JavaScript Example
```javascript
const formData = new FormData();
formData.append('accounts_file', accountsFile);
formData.append('target_file', targetFile);
formData.append('custom_prompt', 'Your custom message template');
formData.append('accounts_to_use', '3');
formData.append('dms_per_account', '30');

const response = await fetch('http://localhost:5000/api/dm-automation/start', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Script ID:', result.script_id);
```

## Security Considerations

1. **Built-in AI**: Uses integrated DeepSeek API for message generation
2. **Instagram Credentials**: Encrypt stored passwords
3. **Rate Limiting**: Respect Instagram's API limits
4. **Proxy Security**: Use authenticated proxies only
5. **File Uploads**: Validate file types and sizes

## Performance Tips

1. **Concurrent Accounts**: Start with 3-5 accounts, increase gradually
2. **DM Limits**: Keep under 50 DMs per account per session
3. **Timing**: Space out campaigns to avoid detection
4. **Proxies**: Use residential proxies for better success rates
5. **Content**: Vary message templates to avoid spam detection

## Troubleshooting

### Common Issues
1. **Login failures**: Check credentials and account status
2. **Captcha challenges**: Use residential proxies, vary behavior
3. **Rate limiting**: Reduce concurrent accounts or DM limits
4. **Message delivery**: Verify targets exist and accept DMs
5. **AI generation**: Ensure DeepSeek API key is valid

### Debug Mode
Enable detailed logging by setting environment variable:
```bash
export DM_DEBUG=true
```

This will provide additional browser automation logs and network debugging information.
