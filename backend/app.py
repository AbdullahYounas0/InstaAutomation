"""
FastAPI Instagram Automation Backend
Converted from Flask to FastAPI for better performance and async support
"""

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import uuid
import logging
import asyncio
import threading
import time as time_module
import tempfile
import atexit
import traceback
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import custom modules
from auth import (
    user_manager, 
    verify_token_dependency, 
    admin_required_dependency,
    log_user_activity
)
from instagram_accounts import instagram_accounts_manager
from instagram_daily_post import run_daily_post_automation
from instagram_dm_automation import run_dm_automation
from instagram_warmup import run_warmup_automation

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Instagram Automation API",
    description="FastAPI backend for Instagram automation scripts",
    version="2.0.0"
)

# CORS Configuration
def get_allowed_origins():
    """Get allowed origins from environment or use defaults"""
    env_origins = os.environ.get('CORS_ORIGINS', '')
    if env_origins:
        return [origin.strip() for origin in env_origins.split(',') if origin.strip()]
    else:
        return [
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'http://localhost:8080',
            'http://127.0.0.1:8080',
            'https://instaui.sitetostart.com',
            'https://www.instaui.sitetostart.com'
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Cache-Control",
        "Pragma"
    ],
)

# Configuration
LOGS_FOLDER = 'logs'
ALLOWED_EXTENSIONS = {
    'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
    'videos': {'mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'},
    'files': {'csv', 'xlsx', 'xls', 'txt'}
}

# Create necessary directories
os.makedirs(LOGS_FOLDER, exist_ok=True)

# Global variables to track running scripts
active_scripts = {}
script_logs = {}
script_stop_flags = {}
script_temp_files = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenRequest(BaseModel):
    token: str

class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    role: str = "va"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class StopScriptRequest(BaseModel):
    reason: str = "Script stopped by user"

# Utility Functions
def cleanup_temp_files(script_id):
    """Clean up temporary files for a specific script"""
    if script_id in script_temp_files:
        for file_path in script_temp_files[script_id]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file {file_path}: {e}")
        del script_temp_files[script_id]

def cleanup_all_temp_files():
    """Clean up all temporary files on shutdown"""
    for script_id in list(script_temp_files.keys()):
        cleanup_temp_files(script_id)

# Register cleanup function
atexit.register(cleanup_all_temp_files)

def save_temp_file(file: UploadFile, script_id: str, prefix: str = ""):
    """Save uploaded file to temporary location and track it"""
    if script_id not in script_temp_files:
        script_temp_files[script_id] = []
    
    # Create temporary file with appropriate extension
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ''
    temp_fd, temp_path = tempfile.mkstemp(suffix=file_extension, prefix=f"{prefix}_{script_id}_")
    
    try:
        # Save file to temporary location
        with os.fdopen(temp_fd, 'wb') as temp_file:
            content = file.file.read()
            temp_file.write(content)
        
        # Track the temporary file
        script_temp_files[script_id].append(temp_path)
        return temp_path
    except Exception as e:
        # Clean up on error
        try:
            os.close(temp_fd)
            os.remove(temp_path)
        except:
            pass
        raise e

def allowed_file(filename: str, file_type: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def generate_script_id() -> str:
    """Generate unique script ID"""
    return str(uuid.uuid4())

def log_script_message(script_id: str, message: str, level: str = "INFO"):
    """Log message for specific script"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    if script_id not in script_logs:
        script_logs[script_id] = []
    
    script_logs[script_id].append(log_entry)
    
    # Keep only last 1000 logs per script
    if len(script_logs[script_id]) > 1000:
        script_logs[script_id] = script_logs[script_id][-1000:]

# Health and Debug Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/debug")
async def debug_endpoint(request: Request):
    """Debug endpoint to check server status"""
    return {
        "status": "Server is running",
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "available_endpoints": [
            "/api/health",
            "/api/debug", 
            "/api/cors-test",
            "/api/auth/login"
        ]
    }

@app.options("/api/cors-test")
@app.get("/api/cors-test")
@app.post("/api/cors-test")
async def cors_test(request: Request):
    """CORS test endpoint to verify CORS configuration"""
    try:
        return {
            "status": "CORS working",
            "method": request.method,
            "origin": request.headers.get('Origin', 'No origin header'),
            "user_agent": request.headers.get('User-Agent', 'No user agent'),
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "fastapi_version": "0.104.1",
                "endpoint_working": True
            },
            "cors_config": {
                "allowed_origins": get_allowed_origins(),
                "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "supports_credentials": True
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            }
        )

# Authentication Endpoints
@app.post("/api/auth/login")
async def login(login_request: LoginRequest, request: Request):
    """Login endpoint for both admin and VA users"""
    try:
        client_ip = request.client.host if request.client else 'unknown'
        result = user_manager.authenticate_user(login_request.username, login_request.password)
        
        if result['success']:
            # Log successful login with IP
            user_id = result['user']['user_id']
            log_user_activity('login', f"Successful login from {client_ip}", user_id, client_ip)
            return result
        else:
            # Log failed login attempt
            log_user_activity('failed_login', f"Failed login attempt for {login_request.username} from {client_ip}", ip_address=client_ip)
            raise HTTPException(status_code=401, detail=result)
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Login error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/auth/verify-token")
async def verify_token(token_request: TokenRequest):
    """Verify JWT token"""
    try:
        result = user_manager.verify_token(token_request.token)
        if not result['success']:
            raise HTTPException(status_code=401, detail=result)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(verify_token_dependency)):
    """Logout endpoint"""
    try:
        log_user_activity('logout', f"User {current_user['username']} logged out", current_user['user_id'])
        return {'success': True, 'message': 'Logged out successfully'}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

# Daily Post Endpoints
@app.post("/api/daily-post/start")
async def start_daily_post(
    background_tasks: BackgroundTasks,
    account_ids: str = Form(...),
    media_file: UploadFile = File(...),
    caption: str = Form(""),
    auto_generate_caption: bool = Form(True),
    visual_mode: bool = Form(True),
    current_user: dict = Depends(verify_token_dependency)
):
    """Start Instagram Daily Post script"""
    script_id = generate_script_id()
    
    try:
        # Parse account IDs
        try:
            account_ids_list = json.loads(account_ids)
            if not isinstance(account_ids_list, list) or len(account_ids_list) == 0:
                raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids_list)
        if len(selected_accounts) == 0:
            raise HTTPException(status_code=400, detail={"error": "No valid accounts found"})
        
        # Check media file type
        is_image = allowed_file(media_file.filename, 'images')
        is_video = allowed_file(media_file.filename, 'videos')
        
        if not (is_image or is_video):
            raise HTTPException(status_code=400, detail={"error": "Invalid media file format. Use supported image/video formats"})
        
        # Save uploaded media file to temporary location
        media_path = save_temp_file(media_file, script_id, "media")
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        accounts_df = pd.DataFrame(accounts_data)
        accounts_path = f"temp_accounts_{script_id}.csv"
        accounts_df.to_csv(accounts_path, index=False)
        
        # Track the temporary accounts file
        if script_id not in script_temp_files:
            script_temp_files[script_id] = []
        script_temp_files[script_id].append(accounts_path)
        
        # Initialize script tracking
        active_scripts[script_id] = {
            "type": "daily_post",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_id": current_user.get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "media_file": media_path,
                "caption": caption,
                "concurrent_accounts": len(selected_accounts),
                "auto_generate_caption": auto_generate_caption,
                "visual_mode": visual_mode,
                "is_video": is_video,
                "selected_account_ids": account_ids_list
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"Daily Post script started with {len(selected_accounts)} accounts")
        log_script_message(script_id, f"Media file: {media_file.filename} ({'Video' if is_video else 'Image'})")
        log_script_message(script_id, f"Visual mode: {'Enabled' if visual_mode else 'Disabled'}")
        
        # Start the script in background
        background_tasks.add_task(run_daily_post_script, script_id)
        
        return {
            "script_id": script_id,
            "status": "started",
            "message": "Daily post script initiated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting daily post script: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

async def run_daily_post_script(script_id: str):
    """Run the actual daily post script"""
    try:
        config = active_scripts[script_id]["config"]
        
        # Create log callback function
        def log_callback(message, level="INFO"):
            log_script_message(script_id, message, level)
        
        # Create stop callback function
        def stop_callback():
            return script_stop_flags.get(script_id, False)
        
        log_script_message(script_id, "Starting Instagram Daily Post automation...")
        
        # Run the automation function
        success = await run_daily_post_automation(
            script_id=script_id,
            accounts_file=config['accounts_file'],
            media_file=config['media_file'],
            concurrent_accounts=config['concurrent_accounts'],
            caption=config.get('caption', ''),
            auto_generate_caption=config.get('auto_generate_caption', True),
            visual_mode=config.get('visual_mode', False),
            log_callback=log_callback,
            stop_callback=stop_callback
        )
        
        if success:
            active_scripts[script_id]["status"] = "completed"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            log_script_message(script_id, "Daily post script completed successfully!", "SUCCESS")
        else:
            active_scripts[script_id]["status"] = "error"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            active_scripts[script_id]["error"] = "Script execution failed"
            log_script_message(script_id, "Daily post script failed", "ERROR")
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# DM Automation Endpoints
@app.post("/api/dm-automation/start")
async def start_dm_automation(
    background_tasks: BackgroundTasks,
    account_ids: str = Form(...),
    target_file: Optional[UploadFile] = File(None),
    dm_prompt_file: Optional[UploadFile] = File(None),
    custom_prompt: str = Form(""),
    dms_per_account: int = Form(30),
    visual_mode: bool = Form(False),
    current_user: dict = Depends(verify_token_dependency)
):
    """Start Instagram DM Automation script"""
    script_id = generate_script_id()
    
    try:
        # Parse account IDs
        try:
            account_ids_list = json.loads(account_ids)
            if not isinstance(account_ids_list, list) or len(account_ids_list) == 0:
                raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids_list)
        if len(selected_accounts) == 0:
            raise HTTPException(status_code=400, detail={"error": "No valid accounts found"})
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        accounts_df = pd.DataFrame(accounts_data)
        accounts_path = f"temp_dm_accounts_{script_id}.csv"
        accounts_df.to_csv(accounts_path, index=False)
        
        # Track the temporary accounts file
        if script_id not in script_temp_files:
            script_temp_files[script_id] = []
        script_temp_files[script_id].append(accounts_path)
        
        target_path = None
        if target_file:
            target_path = save_temp_file(target_file, script_id, "targets")
        
        prompt_path = None
        if dm_prompt_file:
            prompt_path = save_temp_file(dm_prompt_file, script_id, "prompt")
        
        # Initialize script tracking
        active_scripts[script_id] = {
            "type": "dm_automation",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_id": current_user.get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "target_file": target_path,
                "prompt_file": prompt_path,
                "custom_prompt": custom_prompt,
                "dms_per_account": dms_per_account,
                "visual_mode": visual_mode,
                "selected_account_ids": account_ids_list
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"DM Automation script started with {len(selected_accounts)} accounts")
        log_script_message(script_id, f"Target: {dms_per_account} DMs per account")
        log_script_message(script_id, f"Visual mode: {'Enabled' if visual_mode else 'Disabled'}")
        
        # Start the script in background
        background_tasks.add_task(run_dm_automation_script, script_id)
        
        return {
            "script_id": script_id,
            "status": "started",
            "message": "DM automation script initiated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting DM automation script: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

async def run_dm_automation_script(script_id: str):
    """Run the actual DM automation script"""
    try:
        config = active_scripts[script_id]["config"]
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        # Create log callback function
        def log_callback(message, level="INFO"):
            log_script_message(script_id, message, level)
        
        # Create stop callback function  
        def stop_callback():
            return script_stop_flags.get(script_id, False)
        
        log_script_message(script_id, "Starting Instagram DM automation...")
        
        # Run the automation function
        success = await run_dm_automation(
            script_id=script_id,
            accounts_file=config['accounts_file'],
            target_file=config.get('target_file'),
            prompt_file=config.get('prompt_file'),
            custom_prompt=config.get('custom_prompt', ''),
            dms_per_account=config.get('dms_per_account', 30),
            visual_mode=config.get('visual_mode', False),
            log_callback=log_callback,
            stop_callback=stop_callback
        )
        
        if success:
            active_scripts[script_id]["status"] = "completed"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            log_script_message(script_id, "DM automation completed successfully!", "SUCCESS")
        else:
            active_scripts[script_id]["status"] = "error"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            active_scripts[script_id]["error"] = "Script execution failed"
            log_script_message(script_id, "DM automation script failed", "ERROR")
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# Warmup Endpoints
@app.post("/api/warmup/start")
async def start_warmup(
    background_tasks: BackgroundTasks,
    account_ids: str = Form(...),
    warmup_duration_min: int = Form(10),
    warmup_duration_max: int = Form(400),
    scheduler_delay: int = Form(0),
    visual_mode: bool = Form(False),
    feed_scroll: bool = Form(True),
    watch_reels: bool = Form(True),
    like_reels: bool = Form(True),
    like_posts: bool = Form(True),
    explore_page: bool = Form(True),
    random_visits: bool = Form(True),
    activity_delay_min: int = Form(3),
    activity_delay_max: int = Form(7),
    scroll_attempts_min: int = Form(5),
    scroll_attempts_max: int = Form(10),
    current_user: dict = Depends(verify_token_dependency)
):
    """Start Instagram Account Warmup script"""
    script_id = generate_script_id()
    
    try:
        # Parse account IDs
        try:
            account_ids_list = json.loads(account_ids)
            if not isinstance(account_ids_list, list) or len(account_ids_list) == 0:
                raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids_list)
        if len(selected_accounts) == 0:
            raise HTTPException(status_code=400, detail={"error": "No valid accounts found"})
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        accounts_df = pd.DataFrame(accounts_data)
        accounts_path = f"temp_warmup_accounts_{script_id}.csv"
        accounts_df.to_csv(accounts_path, index=False)
        
        # Track the temporary accounts file
        if script_id not in script_temp_files:
            script_temp_files[script_id] = []
        script_temp_files[script_id].append(accounts_path)
        
        # Initialize script tracking
        active_scripts[script_id] = {
            "type": "warmup",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_id": current_user.get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "warmup_duration_min": warmup_duration_min,
                "warmup_duration_max": warmup_duration_max,
                "scheduler_delay": scheduler_delay,
                "visual_mode": visual_mode,
                "selected_account_ids": account_ids_list,
                "activities": {
                    "feed_scroll": feed_scroll,
                    "watch_reels": watch_reels,
                    "like_reels": like_reels,
                    "like_posts": like_posts,
                    "explore_page": explore_page,
                    "random_visits": random_visits
                },
                "timing": {
                    "activity_delay": (activity_delay_min, activity_delay_max),
                    "scroll_attempts": (scroll_attempts_min, scroll_attempts_max)
                }
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"Account warmup script started")
        log_script_message(script_id, f"Random duration range: {warmup_duration_min}-{warmup_duration_max} minutes per session")
        if scheduler_delay > 0:
            log_script_message(script_id, f"🔄 RECURRING MODE: {scheduler_delay} hour delay between sessions")
        else:
            log_script_message(script_id, f"🎯 SINGLE MODE: One-time execution")
        log_script_message(script_id, f"Dynamic account processing: All selected accounts will be used")
        log_script_message(script_id, f"Visual mode: {'Enabled' if visual_mode else 'Disabled'}")
        
        # Start the script in background
        background_tasks.add_task(run_warmup_script, script_id)
        
        return {
            "script_id": script_id,
            "status": "started",
            "message": "Account warmup script initiated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting warmup script: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

async def run_warmup_script(script_id: str):
    """Run the actual warmup script with recurring functionality"""
    try:
        config = active_scripts[script_id]["config"]
        
        # Create log callback function
        def log_callback(message, level="INFO"):
            log_script_message(script_id, message, level)
        
        # Create stop callback function
        def stop_callback():
            return script_stop_flags.get(script_id, False)
        
        # Get configuration
        scheduler_delay_hours = config.get('scheduler_delay', 0)
        duration_min = config.get('warmup_duration_min', 10)
        duration_max = config.get('warmup_duration_max', 400)
        
        # Determine if this is recurring or single run
        is_recurring = scheduler_delay_hours > 0
        session_count = 0
        
        log_script_message(script_id, f"Starting warmup automation...")
        log_script_message(script_id, f"Duration range: {duration_min}-{duration_max} minutes per session")
        
        if is_recurring:
            log_script_message(script_id, f"🔄 RECURRING MODE: Will run sessions with {scheduler_delay_hours} hour delay between them")
            log_script_message(script_id, f"⏹️ Stop the script manually to end recurring sessions")
        else:
            log_script_message(script_id, f"🎯 SINGLE MODE: Will run one session and complete")
        
        # Main execution loop
        while True:
            if stop_callback():
                log_script_message(script_id, "Script stopped by user", "INFO")
                active_scripts[script_id]["status"] = "stopped"
                active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                return
            
            session_count += 1
            session_start_time = datetime.now()
            
            # Generate random duration for this session
            import random
            random_duration = random.randint(duration_min, duration_max)
            
            log_script_message(script_id, f"")
            log_script_message(script_id, f"🚀 Starting Session #{session_count}")
            log_script_message(script_id, f"📊 Session duration: {random_duration} minutes")
            log_script_message(script_id, f"⏰ Session started at: {session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run the automation function for this session
            success = await run_warmup_automation(
                script_id=script_id,
                accounts_file=config['accounts_file'],
                warmup_duration=random_duration,
                activities=config['activities'],
                timing=config['timing'],
                visual_mode=config.get('visual_mode', False),
                log_callback=log_callback,
                stop_callback=stop_callback
            )
            
            session_end_time = datetime.now()
            session_duration = (session_end_time - session_start_time).total_seconds() / 60
            
            if success:
                log_script_message(script_id, f"✅ Session #{session_count} completed successfully!", "SUCCESS")
                log_script_message(script_id, f"📈 Actual session duration: {session_duration:.1f} minutes")
            else:
                log_script_message(script_id, f"❌ Session #{session_count} failed", "ERROR")
                if not is_recurring:
                    active_scripts[script_id]["status"] = "error"
                    active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                    active_scripts[script_id]["error"] = "Session execution failed"
                    return
                else:
                    log_script_message(script_id, f"🔄 Continuing to next session despite failure...", "WARNING")
            
            # Check if this is a single run (no recurring)
            if not is_recurring:
                active_scripts[script_id]["status"] = "completed"
                active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                log_script_message(script_id, "🎯 Single session warmup completed successfully!", "SUCCESS")
                return
            
            # For recurring mode, wait for the specified delay
            if scheduler_delay_hours > 0:
                delay_seconds = scheduler_delay_hours * 3600
                next_session_time = datetime.now() + timedelta(hours=scheduler_delay_hours)
                
                log_script_message(script_id, f"")
                log_script_message(script_id, f"⏳ Waiting {scheduler_delay_hours} hour{'s' if scheduler_delay_hours > 1 else ''} before next session...")
                log_script_message(script_id, f"🕐 Next session scheduled for: {next_session_time.strftime('%Y-%m-%d %H:%M:%S')}")
                log_script_message(script_id, f"⏹️ You can stop the script anytime during this wait")
                
                # Wait with periodic checks for stop signal (check every minute)
                start_wait_time = time_module.time()
                while time_module.time() - start_wait_time < delay_seconds:
                    if stop_callback():
                        log_script_message(script_id, "Script stopped during delay period", "INFO")
                        active_scripts[script_id]["status"] = "stopped"
                        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                        return
                    
                    # Log progress every 15 minutes during long waits
                    elapsed_wait = time_module.time() - start_wait_time
                    remaining_wait = delay_seconds - elapsed_wait
                    if elapsed_wait > 0 and int(elapsed_wait) % 900 == 0:  # Every 15 minutes
                        remaining_hours = remaining_wait / 3600
                        log_script_message(script_id, f"⏳ Still waiting... {remaining_hours:.1f} hours remaining until next session")
                    
                    await asyncio.sleep(60)  # Check every minute
                
                log_script_message(script_id, f"✅ Delay period completed. Preparing for next session...")
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# Script Management Endpoints
@app.get("/api/script/{script_id}/status")
async def get_script_status(script_id: str, current_user: dict = Depends(verify_token_dependency)):
    """Get status of a running script"""
    if script_id not in active_scripts:
        raise HTTPException(status_code=404, detail={"error": "Script not found"})
    
    script_data = active_scripts[script_id].copy()
    
    # Add auto_stop flag for completed, error, or stopped scripts
    auto_stop = script_data.get("status") in ["completed", "error", "stopped"]
    script_data["auto_stop"] = auto_stop
    
    return script_data

@app.get("/api/script/{script_id}/logs")
async def get_script_logs(script_id: str, current_user: dict = Depends(verify_token_dependency)):
    """Get logs for a specific script"""
    logs = script_logs.get(script_id, [])
    return {"logs": logs}

@app.post("/api/script/{script_id}/stop")
async def stop_script(
    script_id: str, 
    stop_request: StopScriptRequest,
    current_user: dict = Depends(verify_token_dependency)
):
    """Stop a running script"""
    if script_id not in active_scripts:
        raise HTTPException(status_code=404, detail={"error": "Script not found"})
    
    if active_scripts[script_id]["status"] == "running":
        # Set stop flag for the script
        script_stop_flags[script_id] = True
        active_scripts[script_id]["status"] = "stopped"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["stop_reason"] = stop_request.reason
        
        # Log the stop reason
        log_script_message(script_id, stop_request.reason, "WARNING")
        
        # Clean up temporary files when script is stopped
        cleanup_temp_files(script_id)
        return {
            "status": "stopped", 
            "message": "Script stopped successfully", 
            "reason": stop_request.reason
        }
    
    return {
        "status": active_scripts[script_id]["status"], 
        "message": "Script not running"
    }

@app.get("/api/scripts")
async def list_scripts(current_user: dict = Depends(verify_token_dependency)):
    """List all scripts with their status - filtered by user or all for admin"""
    user_id = current_user.get('user_id', 'system')
    user_role = current_user.get('role', 'va')
    
    # Admin can see all scripts, VAs only see their own
    if user_role == 'admin':
        filtered_scripts = active_scripts
    else:
        filtered_scripts = {
            script_id: script_data 
            for script_id, script_data in active_scripts.items() 
            if script_data.get('user_id') == user_id
        }
    
    return filtered_scripts

@app.get("/api/scripts/stats")
async def get_script_stats(current_user: dict = Depends(verify_token_dependency)):
    """Get script statistics for the current user or all users for admin"""
    user_id = current_user.get('user_id', 'system')
    user_role = current_user.get('role', 'va')
    
    # Admin can see all scripts, VAs only see their own
    if user_role == 'admin':
        user_scripts = active_scripts
    else:
        user_scripts = {
            script_id: script_data 
            for script_id, script_data in active_scripts.items() 
            if script_data.get('user_id') == user_id
        }
    
    # Calculate statistics
    total_scripts = len(user_scripts)
    running_scripts = len([s for s in user_scripts.values() if s['status'] == 'running'])
    completed_scripts = len([s for s in user_scripts.values() if s['status'] == 'completed'])
    error_scripts = len([s for s in user_scripts.values() if s['status'] == 'error'])
    stopped_scripts = len([s for s in user_scripts.values() if s['status'] == 'stopped'])
    
    # Calculate per-script-type statistics
    script_types = {}
    for script_data in user_scripts.values():
        script_type = script_data.get('type', 'unknown')
        if script_type not in script_types:
            script_types[script_type] = {
                'total': 0,
                'running': 0,
                'completed': 0,
                'error': 0,
                'stopped': 0
            }
        
        script_types[script_type]['total'] += 1
        script_types[script_type][script_data['status']] += 1
    
    return {
        'user_id': user_id,
        'user_role': user_role,
        'total_scripts': total_scripts,
        'running_scripts': running_scripts,
        'completed_scripts': completed_scripts,
        'error_scripts': error_scripts,
        'stopped_scripts': stopped_scripts,
        'script_types': script_types,
        'recent_scripts': sorted(
            user_scripts.values(),
            key=lambda x: x['start_time'],
            reverse=True
        )[:10]  # Last 10 scripts
    }

@app.get("/api/script/{script_id}/download-logs")
async def download_script_logs(script_id: str):
    """Download logs for a specific script as a text file"""
    if script_id not in script_logs:
        raise HTTPException(status_code=404, detail={"error": "Script logs not found"})
    
    logs = script_logs.get(script_id, [])
    log_content = "\n".join(logs)
    
    # Create logs file
    log_filename = f"script_{script_id}_logs.txt"
    log_path = os.path.join(LOGS_FOLDER, log_filename)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    return FileResponse(log_path, filename=log_filename, media_type='text/plain')

@app.post("/api/script/{script_id}/clear-logs")
async def clear_script_logs(script_id: str):
    """Clear logs for a specific script"""
    if script_id not in script_logs:
        raise HTTPException(status_code=404, detail={"error": "Script logs not found"})
    
    script_logs[script_id] = []
    return {"message": "Logs cleared successfully"}

@app.get("/api/script/{script_id}/responses")
async def get_dm_responses(script_id: str, current_user: dict = Depends(verify_token_dependency)):
    """Get positive responses for a completed DM automation script"""
    try:
        # Check if responses file exists
        responses_file = os.path.join(LOGS_FOLDER, f'dm_responses_{script_id}.json')
        
        if not os.path.exists(responses_file):
            return {
                "responses": [],
                "message": f"No responses found for this script. Looking for: {responses_file}"
            }
        
        # Read and return responses
        with open(responses_file, 'r', encoding='utf-8') as f:
            responses = json.load(f)
        
        # Group responses by account for better organization
        grouped_responses = {}
        for response in responses:
            account = response['account']
            if account not in grouped_responses:
                grouped_responses[account] = []
            grouped_responses[account].append({
                'responder': response['responder'],
                'message': response['message'],
                'timestamp': response['timestamp']
            })
        
        return {
            "responses": responses,
            "grouped_responses": grouped_responses,
            "total_responses": len(responses),
            "accounts_with_responses": len(grouped_responses)
        }
        
    except Exception as e:
        logger.error(f"Error fetching responses for script {script_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

# Admin Endpoints
@app.get("/api/admin/users")
async def get_all_users(current_user: dict = Depends(admin_required_dependency)):
    """Get all users (admin only)"""
    try:
        users = user_manager.get_all_users()
        return {'success': True, 'users': users}
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/admin/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(admin_required_dependency)):
    """Create new user (admin only)"""
    try:
        if user_data.role not in ['admin', 'va']:
            raise HTTPException(status_code=400, detail={'success': False, 'message': 'Invalid role'})
        
        result = user_manager.create_user(user_data.name, user_data.username, user_data.password, user_data.role)
        
        if result['success']:
            log_user_activity('user_created', f"Created user {user_data.username} with role {user_data.role}", current_user['user_id'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    current_user: dict = Depends(admin_required_dependency)
):
    """Update user (admin only)"""
    try:
        updates = {}
        
        # Allow updating name, password, is_active
        if user_update.name is not None:
            updates['name'] = user_update.name
        if user_update.password is not None:
            updates['password'] = user_update.password
        if user_update.is_active is not None:
            updates['is_active'] = user_update.is_active
        
        if not updates:
            raise HTTPException(status_code=400, detail={'success': False, 'message': 'No updates provided'})
        
        result = user_manager.update_user(user_id, updates)
        
        if result['success']:
            log_user_activity('user_updated', f"Updated user {user_id}", current_user['user_id'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/admin/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, current_user: dict = Depends(admin_required_dependency)):
    """Deactivate user (admin only)"""
    try:
        result = user_manager.deactivate_user(user_id)
        
        if result['success']:
            log_user_activity('user_deactivated', f"Deactivated user {user_id}", current_user['user_id'])
        
        return result
        
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(admin_required_dependency)):
    """Delete user permanently (admin only)"""
    try:
        result = user_manager.delete_user(user_id)
        
        if result['success']:
            log_user_activity('user_deleted', f"Deleted user {user_id}", current_user['user_id'])
        
        return result
        
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/admin/activity-logs")
async def get_activity_logs(current_user: dict = Depends(admin_required_dependency)):
    """Get activity logs (admin only)"""
    try:
        logs = user_manager.get_activity_logs()
        return {'success': True, 'logs': logs}
    except Exception as e:
        logger.error(f"Get activity logs error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(admin_required_dependency)):
    """Get admin dashboard statistics"""
    try:
        users = user_manager.get_all_users()
        logs = user_manager.get_activity_logs(50)
        
        stats = {
            'total_users': len(users),
            'active_users': len([u for u in users if u.get('is_active', True)]),
            'admin_users': len([u for u in users if u['role'] == 'admin']),
            'va_users': len([u for u in users if u['role'] == 'va']),
            'total_scripts': len(active_scripts),
            'running_scripts': len([s for s in active_scripts.values() if s['status'] == 'running']),
            'recent_activity': logs[:10]
        }
        
        return {'success': True, 'stats': stats}
    except Exception as e:
        logger.error(f"Get admin stats error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

# Instagram Accounts Management Endpoints
@app.get("/api/instagram-accounts")
async def get_instagram_accounts(current_user: dict = Depends(verify_token_dependency)):
    """Get all Instagram accounts"""
    try:
        accounts = instagram_accounts_manager.get_all_accounts()
        return {'success': True, 'accounts': accounts}
    except Exception as e:
        logger.error(f"Get Instagram accounts error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/instagram-accounts/active")
async def get_active_instagram_accounts(current_user: dict = Depends(verify_token_dependency)):
    """Get only active Instagram accounts"""
    try:
        accounts = instagram_accounts_manager.get_active_accounts()
        return {'success': True, 'accounts': accounts}
    except Exception as e:
        logger.error(f"Get active Instagram accounts error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

# File validation endpoints
@app.post("/api/daily-post/validate")
async def validate_daily_post_files(
    media_file: UploadFile = File(...),
    current_user: dict = Depends(verify_token_dependency)
):
    """Validate uploaded files before starting the script"""
    try:
        errors = []
        
        # Validate media file
        if not media_file:
            errors.append("Media file is required")
        else:
            is_image = allowed_file(media_file.filename, 'images')
            is_video = allowed_file(media_file.filename, 'videos')
            if not (is_image or is_video):
                errors.append("Invalid media file format. Use supported image/video formats")
        
        if errors:
            raise HTTPException(status_code=400, detail={"valid": False, "errors": errors})
        
        return {
            "valid": True, 
            "message": "Files validated successfully",
            "media_type": "video" if is_video else "image"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"valid": False, "errors": [str(e)]})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
