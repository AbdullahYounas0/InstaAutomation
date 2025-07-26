# Instagram Daily Post Backend

This backend handles the Instagram Daily Post automation using Playwright and Flask.

## Setup Instructions

### Option 1: Quick Setup (Windows)
1. Run `setup.bat` to automatically install dependencies and Playwright browsers

### Option 2: Manual Setup
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

## Running the Backend

```bash
python app.py
```

The backend will start on `http://localhost:5000`

## Features

### Daily Post Automation
- **File Upload**: Supports Excel (.xlsx, .xls) and CSV files for account credentials
- **Media Support**: Images (jpg, jpeg, png, gif, bmp, webp) and Videos (mp4, mov, avi, mkv, webm, m4v)
- **Concurrent Processing**: Process up to 10 accounts simultaneously
- **Smart Caption Generation**: Auto-generate captions or use custom ones
- **Real-time Logging**: Monitor progress in real-time
- **Error Handling**: Comprehensive error handling and retry mechanisms

### Account File Format
The accounts file should have the following columns:
- `Username`: Instagram username
- `Password`: Instagram password

Example Excel/CSV structure:
```
Username    | Password
account1    | password1
account2    | password2
account3    | password3
```

## API Endpoints

### Daily Post
- `POST /api/daily-post/start` - Start daily post automation
- `GET /api/script/{script_id}/status` - Get script status
- `GET /api/script/{script_id}/logs` - Get script logs
- `POST /api/script/{script_id}/stop` - Stop running script

### General
- `GET /api/health` - Health check
- `GET /api/scripts` - List all scripts

## Configuration

The backend creates the following directories automatically:
- `uploads/` - For uploaded files
- `logs/` - For log files

## Browser Configuration

The script uses Chromium in headless mode for production. Key features:
- **Anti-detection**: Disabled automation control features
- **Human-like behavior**: Random delays and typing patterns
- **Popup handling**: Automatic dismissal of Instagram popups
- **Error screenshots**: Automatic screenshot capture on errors

## Security Notes

- Files are uploaded with secure filenames
- Input validation for file types and sizes
- Automatic cleanup of old log entries
- Script isolation with unique IDs

## Troubleshooting

1. **Playwright Installation Issues**: Make sure Chromium is installed with `python -m playwright install chromium`
2. **Permission Errors**: Run as administrator if file upload fails
3. **Browser Launch Issues**: Check if Chrome/Chromium is available on the system
4. **Account Login Issues**: Verify credentials and check for 2FA requirements

## Dependencies

- Flask 3.0.0
- Flask-CORS 4.0.0
- Playwright 1.40.0
- Pandas 2.1.4
- OpenPyXL 3.1.2
