# Temporary File System Implementation

## Overview
The backend has been updated to use a temporary file system instead of permanently saving uploaded files. This change improves security, reduces disk usage, and automatically cleans up files after processing.

## Changes Made

### 1. Temporary File System Implementation
- **Removed**: Permanent file storage in `uploads/` directory
- **Added**: Temporary file system using Python's `tempfile` module
- **Added**: Automatic cleanup mechanisms for temporary files

### 2. New Functions Added
- `save_temp_file(file, script_id, prefix="")`: Saves uploaded files to temporary locations
- `cleanup_temp_files(script_id)`: Cleans up temporary files for a specific script
- `cleanup_all_temp_files()`: Cleans up all temporary files on application shutdown
- `atexit.register(cleanup_all_temp_files)`: Ensures cleanup on app termination

### 3. Screenshot Mechanism Removal
- **Removed**: `capture_screenshot()` function from `instagram_warmup.py`
- **Removed**: All screenshot capture calls throughout the application
- **Removed**: Screenshots directory and related functionality

### 4. Updated Endpoints
All file upload endpoints now use temporary files:
- `/api/daily-post/start` - Daily Post automation
- `/api/dm-automation/start` - DM automation
- `/api/warmup/start` - Account warmup

### 5. Automatic Cleanup
Temporary files are automatically cleaned up in the following scenarios:
- When a script completes successfully
- When a script encounters an error
- When a script is manually stopped by the user
- When the application shuts down

## Benefits

### Security
- No permanent storage of sensitive account files
- Files are automatically removed after processing
- Reduced risk of data exposure

### Performance
- No disk space accumulation from old uploads
- Faster cleanup process
- Reduced maintenance overhead

### Reliability
- Automatic cleanup prevents disk space issues
- Better error handling for file operations
- Consistent temporary file management

## Technical Details

### File Tracking
- Each script maintains a list of its temporary files in `script_temp_files` dictionary
- Files are tracked by script ID for organized cleanup

### Cleanup Triggers
1. **Script Completion**: Files cleaned up when script finishes
2. **Script Error**: Files cleaned up when script encounters errors
3. **Manual Stop**: Files cleaned up when user stops script
4. **Application Exit**: All remaining files cleaned up on shutdown

### Error Handling
- Robust error handling for file operations
- Graceful cleanup even if individual files fail to delete
- Logging of cleanup operations for monitoring

## Migration Notes
- Existing uploads directory has been removed
- Screenshots directory has been removed
- No action required for existing scripts - they will automatically use the new system
- All temporary files are created with appropriate extensions for compatibility

## Testing
All endpoints have been tested to ensure:
- Files are properly saved to temporary locations
- Scripts can access temporary files correctly
- Cleanup occurs reliably in all scenarios
- No references to old upload/screenshot directories remain
