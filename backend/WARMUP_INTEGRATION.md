# Instagram Account Warmup Integration

## Overview
This module provides Instagram account warmup functionality that simulates human-like behavior to maintain account trust scores.

## Features
- Multiple concurrent browsers for batch processing
- Human-like typing and scrolling patterns
- Various activities: feed scrolling, reel watching/liking, post liking, exploring
- Configurable timing and activity parameters
- Visual mode support (show/hide browsers)
- Real-time logging and progress tracking
- Graceful stopping capability

## API Endpoints

### 1. Start Warmup
**POST** `/api/warmup/start`

**Form Data:**
- `accounts_file` (file): CSV/Excel file with Username and Password columns
- `warmup_duration` (int): Duration in minutes (default: 300)
- `max_concurrent` (int): Max concurrent browsers (default: 10)
- `visual_mode` (boolean): Show browsers (default: false)

**Activity Settings:**
- `feed_scroll` (boolean): Enable feed scrolling
- `watch_reels` (boolean): Enable reel watching
- `like_reels` (boolean): Enable reel liking
- `like_posts` (boolean): Enable post liking
- `explore_page` (boolean): Enable explore page browsing
- `random_visits` (boolean): Enable random page visits

**Timing Settings:**
- `activity_delay_min` (int): Min delay between activities in seconds (default: 3)
- `activity_delay_max` (int): Max delay between activities in seconds (default: 7)
- `scroll_attempts_min` (int): Min scroll attempts per activity (default: 5)
- `scroll_attempts_max` (int): Max scroll attempts per activity (default: 10)

**Response:**
```json
{
    "script_id": "uuid-string",
    "status": "started",
    "message": "Account warmup script initiated successfully"
}
```

### 2. Validate Files
**POST** `/api/warmup/validate`

**Form Data:**
- `accounts_file` (file): CSV/Excel file to validate

**Response:**
```json
{
    "valid": true,
    "message": "Files validated successfully",
    "accounts_count": 10,
    "warnings": []
}
```

## Account File Format

### CSV Format (accounts.csv):
```csv
Username,Password
your_username1,your_password1
your_username2,your_password2
```

### Excel Format (accounts.xlsx):
Should contain columns: Username, Password

## Usage Example

1. Prepare accounts file with valid Instagram credentials
2. Configure warmup settings (duration, activities, timing)
3. Start warmup via API call
4. Monitor progress through logs endpoint
5. Stop if needed via stop endpoint

## Safety Features

- Human-like delays and patterns
- Batch processing to avoid overloading
- Error handling and screenshots on failures
- Graceful stopping mechanism
- Activity randomization
- Browser rotation

## Integration Notes

- Requires playwright installation: `playwright install chromium`
- Uses Chrome/Chromium browser
- Supports headless and visual modes
- Creates screenshots on errors in logs/screenshots/
- Integrates with existing Flask app logging system
