from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import threading
import uuid
import json
import logging
import time
import asyncio
import pandas as pd
import traceback
import tempfile
import atexit
from datetime import datetime, timedelta
from instagram_daily_post import run_daily_post_automation
from instagram_dm_automation import run_dm_automation
from instagram_warmup import run_warmup_automation
from auth import user_manager, token_required, admin_required, log_user_activity
from instagram_accounts import instagram_accounts_manager

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
script_stop_flags = {}  # To handle stopping scripts
script_temp_files = {}  # Track temporary files per script

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Register cleanup function to run on exit
atexit.register(cleanup_all_temp_files)

def save_temp_file(file, script_id, prefix=""):
    """Save uploaded file to temporary location and track it"""
    if script_id not in script_temp_files:
        script_temp_files[script_id] = []
    
    # Create temporary file with appropriate extension
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ''
    temp_fd, temp_path = tempfile.mkstemp(suffix=file_extension, prefix=f"{prefix}_{script_id}_")
    
    try:
        # Save file to temporary location
        with os.fdopen(temp_fd, 'wb') as temp_file:
            file.save(temp_file)
        
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

def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def generate_script_id():
    """Generate unique script ID"""
    return str(uuid.uuid4())

def log_script_message(script_id, message, level="INFO"):
    """Log message for specific script"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    if script_id not in script_logs:
        script_logs[script_id] = []
    
    script_logs[script_id].append(log_entry)
    
    # Keep only last 1000 logs per script
    if len(script_logs[script_id]) > 1000:
        script_logs[script_id] = script_logs[script_id][-1000:]

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# =================== DAILY POST ENDPOINTS ===================

@app.route('/api/daily-post/start', methods=['POST'])
@token_required
def start_daily_post():
    """Start Instagram Daily Post script"""
    script_id = generate_script_id()
    
    try:
        # Get form data
        account_ids_str = request.form.get('account_ids')
        media_file = request.files.get('media_file')
        caption = request.form.get('caption', '')
        auto_generate_caption = request.form.get('auto_generate_caption') == 'true'
        visual_mode = request.form.get('visual_mode', 'true') == 'true'  # Default to true for Daily Post to show browsers
        
        # Validate required data
        if not account_ids_str or not media_file:
            return jsonify({"error": "Account IDs and media file are required"}), 400
        
        # Parse account IDs
        try:
            account_ids = json.loads(account_ids_str)
            if not isinstance(account_ids, list) or len(account_ids) == 0:
                return jsonify({"error": "Invalid account IDs format"}), 400
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid account IDs format"}), 400
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids)
        if len(selected_accounts) == 0:
            return jsonify({"error": "No valid accounts found"}), 400
        
        # Check media file type
        is_image = allowed_file(media_file.filename, 'images')
        is_video = allowed_file(media_file.filename, 'videos')
        
        if not (is_image or is_video):
            return jsonify({"error": "Invalid media file format. Use supported image/video formats"}), 400
        
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
        import pandas as pd
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
            "user_id": getattr(request, 'current_user', {}).get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "media_file": media_path,
                "caption": caption,
                "concurrent_accounts": len(selected_accounts),  # Use number of selected accounts
                "auto_generate_caption": auto_generate_caption,
                "visual_mode": visual_mode,
                "is_video": is_video,
                "selected_account_ids": account_ids
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"Daily Post script started with {len(selected_accounts)} accounts")
        log_script_message(script_id, f"Media file: {media_file.filename} ({'Video' if is_video else 'Image'})")
        log_script_message(script_id, f"Visual mode: {'Enabled' if visual_mode else 'Disabled'}")
        
        # Start the script in a separate thread
        thread = threading.Thread(target=run_daily_post_script, args=(script_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "script_id": script_id,
            "status": "started",
            "message": "Daily post script initiated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error starting daily post script: {e}")
        return jsonify({"error": str(e)}), 500

def run_daily_post_script(script_id):
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
        
        # Run the async automation function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                run_daily_post_automation(
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
                
        finally:
            loop.close()
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# =================== DM AUTOMATION ENDPOINTS ===================

@app.route('/api/dm-automation/start', methods=['POST'])
@token_required
def start_dm_automation():
    """Start Instagram DM Automation script"""
    script_id = generate_script_id()
    
    try:
        # Get form data
        account_ids_str = request.form.get('account_ids')
        target_file = request.files.get('target_file')
        dm_prompt_file = request.files.get('dm_prompt_file')
        custom_prompt = request.form.get('custom_prompt', '')
        dms_per_account = int(request.form.get('dms_per_account', 30))
        visual_mode = request.form.get('visual_mode', 'false') == 'true'  # New parameter for showing browsers
        
        # Validate required data
        if not account_ids_str:
            return jsonify({"error": "Account IDs are required"}), 400
        
        # Parse account IDs
        try:
            account_ids = json.loads(account_ids_str)
            if not isinstance(account_ids, list) or len(account_ids) == 0:
                return jsonify({"error": "Invalid account IDs format"}), 400
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid account IDs format"}), 400
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids)
        if len(selected_accounts) == 0:
            return jsonify({"error": "No valid accounts found"}), 400
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        import pandas as pd
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
            "user_id": getattr(request, 'current_user', {}).get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "target_file": target_path,
                "prompt_file": prompt_path,
                "custom_prompt": custom_prompt,
                "dms_per_account": dms_per_account,
                "visual_mode": visual_mode,
                "selected_account_ids": account_ids
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"DM Automation script started with dynamic account count")
        log_script_message(script_id, f"Target: {dms_per_account} DMs per account")
        log_script_message(script_id, f"Visual mode: {'Enabled' if visual_mode else 'Disabled'}")
        
        # Start the script in a separate thread
        thread = threading.Thread(target=run_dm_automation_script, args=(script_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "script_id": script_id,
            "status": "started",
            "message": "DM automation script initiated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error starting DM automation script: {e}")
        return jsonify({"error": str(e)}), 500

def run_dm_automation_script(script_id):
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
        
        # Run the async automation function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                run_dm_automation(
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
                
        finally:
            loop.close()
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# =================== WARMUP ENDPOINTS ===================

@app.route('/api/warmup/start', methods=['POST'])
@token_required
def start_warmup():
    """Start Instagram Account Warmup script"""
    script_id = generate_script_id()
    
    try:
        # Get form data
        account_ids_str = request.form.get('account_ids')
        warmup_duration_min = int(request.form.get('warmup_duration_min', 10))
        warmup_duration_max = int(request.form.get('warmup_duration_max', 400))
        scheduler_delay = int(request.form.get('scheduler_delay', 0))
        visual_mode = request.form.get('visual_mode', 'false') == 'true'  # New parameter for showing browsers
        
        # Activity settings
        feed_scroll = request.form.get('feed_scroll') == 'true'
        watch_reels = request.form.get('watch_reels') == 'true'
        like_reels = request.form.get('like_reels') == 'true'
        like_posts = request.form.get('like_posts') == 'true'
        explore_page = request.form.get('explore_page') == 'true'
        random_visits = request.form.get('random_visits') == 'true'
        
        activity_delay_min = int(request.form.get('activity_delay_min', 3))
        activity_delay_max = int(request.form.get('activity_delay_max', 7))
        scroll_attempts_min = int(request.form.get('scroll_attempts_min', 5))
        scroll_attempts_max = int(request.form.get('scroll_attempts_max', 10))
        
        # Validate required data
        if not account_ids_str:
            return jsonify({"error": "Account IDs are required"}), 400
        
        # Parse account IDs
        try:
            account_ids = json.loads(account_ids_str)
            if not isinstance(account_ids, list) or len(account_ids) == 0:
                return jsonify({"error": "Invalid account IDs format"}), 400
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid account IDs format"}), 400
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids)
        if len(selected_accounts) == 0:
            return jsonify({"error": "No valid accounts found"}), 400
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        import pandas as pd
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
            "user_id": getattr(request, 'current_user', {}).get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "warmup_duration_min": warmup_duration_min,
                "warmup_duration_max": warmup_duration_max,
                "scheduler_delay": scheduler_delay,
                "visual_mode": visual_mode,
                "selected_account_ids": account_ids,
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
        
        # Start the script in a separate thread (with scheduler delay if specified)
        thread = threading.Thread(target=run_warmup_script, args=(script_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "script_id": script_id,
            "status": "started",
            "message": "Account warmup script initiated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error starting warmup script: {e}")
        return jsonify({"error": str(e)}), 500

def run_warmup_script(script_id):
    """Run the actual warmup script with recurring functionality"""
    import random
    import time as time_module
    
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
            random_duration = random.randint(duration_min, duration_max)
            
            log_script_message(script_id, f"")
            log_script_message(script_id, f"🚀 Starting Session #{session_count}")
            log_script_message(script_id, f"📊 Session duration: {random_duration} minutes")
            log_script_message(script_id, f"⏰ Session started at: {session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run the async automation function for this session
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                success = loop.run_until_complete(
                    run_warmup_automation(
                        script_id=script_id,
                        accounts_file=config['accounts_file'],
                        warmup_duration=random_duration,
                        activities=config['activities'],
                        timing=config['timing'],
                        visual_mode=config.get('visual_mode', False),
                        log_callback=log_callback,
                        stop_callback=stop_callback
                    )
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
                        
            finally:
                loop.close()
            
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
                    
                    time_module.sleep(60)  # Check every minute
                
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

# =================== GENERAL ENDPOINTS ===================

@app.route('/api/script/<script_id>/status', methods=['GET'])
@token_required
def get_script_status(script_id):
    """Get status of a running script"""
    if script_id not in active_scripts:
        return jsonify({"error": "Script not found"}), 404
    
    script_data = active_scripts[script_id].copy()
    
    # Add auto_stop flag for completed, error, or stopped scripts
    auto_stop = script_data.get("status") in ["completed", "error", "stopped"]
    script_data["auto_stop"] = auto_stop
    
    return jsonify(script_data)

@app.route('/api/script/<script_id>/logs', methods=['GET'])
@token_required
def get_script_logs(script_id):
    """Get logs for a specific script"""
    logs = script_logs.get(script_id, [])
    return jsonify({"logs": logs})

@app.route('/api/script/<script_id>/stop', methods=['POST'])
@token_required
def stop_script(script_id):
    """Stop a running script"""
    if script_id not in active_scripts:
        return jsonify({"error": "Script not found"}), 404
    
    if active_scripts[script_id]["status"] == "running":
        # Get the reason from request data
        data = request.get_json() if request.is_json else {}
        reason = data.get('reason', 'Script stopped by user')
        
        # Handle form data as well (for sendBeacon requests)
        if not request.is_json and request.form:
            reason = request.form.get('reason', 'Script stopped by user')
        
        # Set stop flag for the script
        script_stop_flags[script_id] = True
        active_scripts[script_id]["status"] = "stopped"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["stop_reason"] = reason
        
        # Log the stop reason
        log_script_message(script_id, reason, "WARNING")
        
        # Clean up temporary files when script is stopped
        cleanup_temp_files(script_id)
        return jsonify({"status": "stopped", "message": "Script stopped successfully", "reason": reason})
    
    return jsonify({"status": active_scripts[script_id]["status"], "message": "Script not running"})

@app.route('/api/scripts', methods=['GET'])
@token_required
def list_scripts():
    """List all scripts with their status - filtered by user or all for admin"""
    current_user = getattr(request, 'current_user', {})
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
    
    return jsonify(filtered_scripts)

@app.route('/api/scripts/stats', methods=['GET'])
@token_required
def get_script_stats():
    """Get script statistics for the current user or all users for admin"""
    current_user = getattr(request, 'current_user', {})
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
    
    return jsonify({
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
    })

@app.route('/api/script/<script_id>/download-logs', methods=['GET'])
def download_script_logs(script_id):
    """Download logs for a specific script as a text file"""
    if script_id not in script_logs:
        return jsonify({"error": "Script logs not found"}), 404
    
    logs = script_logs.get(script_id, [])
    log_content = "\n".join(logs)
    
    # Create logs file
    log_filename = f"script_{script_id}_logs.txt"
    log_path = os.path.join(LOGS_FOLDER, log_filename)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    return send_file(log_path, as_attachment=True, download_name=log_filename)

@app.route('/api/script/<script_id>/clear-logs', methods=['POST'])
def clear_script_logs(script_id):
    """Clear logs for a specific script"""
    if script_id not in script_logs:
        return jsonify({"error": "Script logs not found"}), 404
    
    script_logs[script_id] = []
    return jsonify({"message": "Logs cleared successfully"})

@app.route('/api/daily-post/validate', methods=['POST'])
def validate_daily_post_files():
    """Validate uploaded files before starting the script"""
    try:
        accounts_file = request.files.get('accounts_file')
        media_file = request.files.get('media_file')
        
        errors = []
        
        # Validate accounts file
        if not accounts_file:
            errors.append("Accounts file is required")
        elif not allowed_file(accounts_file.filename, 'files'):
            errors.append("Invalid accounts file format. Use CSV or Excel")
        else:
            # Try to read the file to validate structure
            try:
                if accounts_file.filename.endswith('.csv'):
                    df = pd.read_csv(accounts_file)
                else:
                    df = pd.read_excel(accounts_file)
                
                df.columns = df.columns.str.strip().str.title()
                required_columns = ["Username", "Password"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    errors.append(f"Missing columns in accounts file: {missing_columns}")
                elif df.empty:
                    errors.append("Accounts file is empty")
                else:
                    valid_accounts = 0
                    for i in range(len(df)):
                        username = df.loc[i, "Username"]
                        password = df.loc[i, "Password"]
                        if pd.notna(username) and pd.notna(password):
                            valid_accounts += 1
                    if valid_accounts == 0:
                        errors.append("No valid accounts found in file")
            except Exception as e:
                errors.append(f"Error reading accounts file: {str(e)}")
        
        # Validate media file
        if not media_file:
            errors.append("Media file is required")
        else:
            is_image = allowed_file(media_file.filename, 'images')
            is_video = allowed_file(media_file.filename, 'videos')
            if not (is_image or is_video):
                errors.append("Invalid media file format. Use supported image/video formats")
        
        if errors:
            return jsonify({"valid": False, "errors": errors}), 400
        
        return jsonify({
            "valid": True, 
            "message": "Files validated successfully",
            "accounts_count": valid_accounts if 'valid_accounts' in locals() else 0,
            "media_type": "video" if is_video else "image"
        })
        
    except Exception as e:
        return jsonify({"valid": False, "errors": [str(e)]}), 500

@app.route('/api/dm-automation/validate', methods=['POST'])
def validate_dm_automation_files():
    """Validate uploaded files before starting the DM automation script"""
    try:
        accounts_file = request.files.get('accounts_file')
        target_file = request.files.get('target_file')
        dm_prompt_file = request.files.get('dm_prompt_file')
        
        errors = []
        warnings = []
        
        # Validate accounts file (required)
        if not accounts_file:
            errors.append("Bot accounts file is required")
        elif not allowed_file(accounts_file.filename, 'files'):
            errors.append("Invalid accounts file format. Use CSV or Excel")
        else:
            # Try to read the file to validate structure
            try:
                if accounts_file.filename.endswith('.csv'):
                    df = pd.read_csv(accounts_file)
                else:
                    df = pd.read_excel(accounts_file)
                
                df.columns = df.columns.str.strip().str.title()
                required_columns = ["Username", "Password"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    errors.append(f"Missing columns in bot accounts file: {missing_columns}")
                elif df.empty:
                    errors.append("Bot accounts file is empty")
                else:
                    valid_accounts = 0
                    for i in range(len(df)):
                        username = df.loc[i, "Username"]
                        password = df.loc[i, "Password"]
                        if pd.notna(username) and pd.notna(password):
                            valid_accounts += 1
                    if valid_accounts == 0:
                        errors.append("No valid bot accounts found in file")
            except Exception as e:
                errors.append(f"Error reading bot accounts file: {str(e)}")
        
        # Validate target file (optional)
        target_accounts = 0
        if target_file:
            if not allowed_file(target_file.filename, 'files'):
                warnings.append("Invalid target file format. Use CSV or Excel")
            else:
                try:
                    if target_file.filename.endswith('.csv'):
                        target_df = pd.read_csv(target_file)
                    else:
                        target_df = pd.read_excel(target_file)
                    
                    target_accounts = len(target_df)
                    if target_accounts == 0:
                        warnings.append("Target file is empty")
                    
                except Exception as e:
                    warnings.append(f"Error reading target file: {str(e)}")
        else:
            warnings.append("No target file provided - will use default target list")
        
        # Validate prompt file (optional)
        if dm_prompt_file:
            if not dm_prompt_file.filename.endswith('.txt'):
                warnings.append("DM prompt file should be a .txt file")
            else:
                try:
                    prompt_content = dm_prompt_file.read().decode('utf-8')
                    if not prompt_content.strip():
                        warnings.append("DM prompt file is empty")
                    dm_prompt_file.seek(0)  # Reset file pointer
                except Exception as e:
                    warnings.append(f"Error reading prompt file: {str(e)}")
        
        if errors:
            return jsonify({"valid": False, "errors": errors, "warnings": warnings}), 400
        
        return jsonify({
            "valid": True,
            "message": "Files validated successfully",
            "bot_accounts_count": valid_accounts if 'valid_accounts' in locals() else 0,
            "target_accounts_count": target_accounts,
            "warnings": warnings
        })
        
    except Exception as e:
        return jsonify({"valid": False, "errors": [str(e)]}), 500

@app.route('/api/script/<script_id>/responses', methods=['GET'])
@token_required
def get_dm_responses(script_id):
    """Get positive responses for a completed DM automation script"""
    try:
        # Check if responses file exists
        responses_file = os.path.join(LOGS_FOLDER, f'dm_responses_{script_id}.json')
        
        if not os.path.exists(responses_file):
            return jsonify({
                "responses": [],
                "message": f"No responses found for this script. Looking for: {responses_file}"
            })
        
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
        
        return jsonify({
            "responses": responses,
            "grouped_responses": grouped_responses,
            "total_responses": len(responses),
            "accounts_with_responses": len(grouped_responses)
        })
        
    except Exception as e:
        logger.error(f"Error fetching responses for script {script_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/warmup/validate', methods=['POST'])
def validate_warmup_files():
    """Validate uploaded files before starting the warmup script"""
    try:
        accounts_file = request.files.get('accounts_file')
        
        errors = []
        warnings = []
        
        # Validate accounts file (required)
        if not accounts_file:
            errors.append("Accounts file is required")
        elif not allowed_file(accounts_file.filename, 'files'):
            errors.append("Invalid accounts file format. Use CSV or Excel")
        else:
            # Try to read the file to validate structure
            try:
                if accounts_file.filename.endswith('.csv'):
                    df = pd.read_csv(accounts_file)
                else:
                    df = pd.read_excel(accounts_file)
                
                df.columns = df.columns.str.strip().str.title()
                required_columns = ["Username", "Password"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    errors.append(f"Missing columns in accounts file: {missing_columns}")
                elif df.empty:
                    errors.append("Accounts file is empty")
                else:
                    valid_accounts = 0
                    for i in range(len(df)):
                        username = df.loc[i, "Username"]
                        password = df.loc[i, "Password"]
                        if pd.notna(username) and pd.notna(password):
                            valid_accounts += 1
                    if valid_accounts == 0:
                        errors.append("No valid accounts found in file")
            except Exception as e:
                errors.append(f"Error reading accounts file: {str(e)}")
        
        if errors:
            return jsonify({"valid": False, "errors": errors, "warnings": warnings}), 400
        
        return jsonify({
            "valid": True, 
            "message": "Files validated successfully",
            "accounts_count": valid_accounts if 'valid_accounts' in locals() else 0,
            "warnings": warnings
        })
        
    except Exception as e:
        return jsonify({"valid": False, "errors": [str(e)]}), 500

# =================== AUTHENTICATION ENDPOINTS ===================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint for both admin and VA users"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        result = user_manager.authenticate_user(username, password)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/auth/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token required'}), 400
        
        result = user_manager.verify_token(token)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    """Logout endpoint"""
    try:
        log_user_activity('logout', f"User {request.current_user['username']} logged out")
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# =================== ADMIN ENDPOINTS ===================

@app.route('/api/admin/users', methods=['GET'])
@token_required
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        users = user_manager.get_all_users()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/admin/users', methods=['POST'])
@token_required
@admin_required
def create_user():
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        name = data.get('name')
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'va')
        
        if not name or not username or not password:
            return jsonify({'success': False, 'message': 'Name, username and password required'}), 400
        
        if role not in ['admin', 'va']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        result = user_manager.create_user(name, username, password, role)
        
        if result['success']:
            log_user_activity('user_created', f"Created user {username} with role {role}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/admin/users/<user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(user_id):
    """Update user (admin only)"""
    try:
        data = request.get_json()
        updates = {}
        
        # Allow updating name, password, is_active
        if 'name' in data:
            updates['name'] = data['name']
        if 'password' in data:
            updates['password'] = data['password']
        if 'is_active' in data:
            updates['is_active'] = data['is_active']
        
        if not updates:
            return jsonify({'success': False, 'message': 'No valid fields to update'}), 400
        
        result = user_manager.update_user(user_id, updates)
        
        if result['success']:
            log_user_activity('user_updated', f"Updated user {user_id}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Update user error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/admin/users/<user_id>/deactivate', methods=['POST'])
@token_required
@admin_required
def deactivate_user(user_id):
    """Deactivate user (admin only)"""
    try:
        result = user_manager.deactivate_user(user_id)
        
        if result['success']:
            log_user_activity('user_deactivated', f"Deactivated user {user_id}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    """Delete user permanently (admin only)"""
    try:
        result = user_manager.delete_user(user_id)
        
        if result['success']:
            log_user_activity('user_deleted', f"Deleted user {user_id}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/admin/activity-logs', methods=['GET'])
@token_required
@admin_required
def get_activity_logs():
    """Get activity logs (admin only)"""
    try:
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 100))
        
        logs = user_manager.get_activity_logs(user_id, limit)
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        logger.error(f"Get activity logs error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/admin/stats', methods=['GET'])
@token_required
@admin_required
def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        users = user_manager.get_all_users()
        logs = user_manager.get_activity_logs(limit=1000)
        
        # Calculate stats
        total_users = len(users)
        active_users = len([u for u in users if u['is_active']])
        va_users = len([u for u in users if u['role'] == 'va'])
        admin_users = len([u for u in users if u['role'] == 'admin'])
        
        # Recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_logins = len([
            log for log in logs 
            if log['action'] == 'login' and 
            datetime.fromisoformat(log['timestamp']) > yesterday
        ])
        
        # Running scripts
        running_scripts = len([s for s in active_scripts.values() if s['status'] == 'running'])
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'va_users': va_users,
            'admin_users': admin_users,
            'recent_logins': recent_logins,
            'running_scripts': running_scripts,
            'total_scripts': len(active_scripts)
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Get admin stats error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# Instagram Accounts Management Endpoints
@app.route('/api/instagram-accounts', methods=['GET'])
@token_required
def get_instagram_accounts():
    """Get all Instagram accounts"""
    try:
        accounts = instagram_accounts_manager.get_all_accounts()
        return jsonify({'success': True, 'accounts': accounts})
    except Exception as e:
        logger.error(f"Get accounts error: {e}")
        return jsonify({'success': False, 'message': 'Failed to retrieve accounts'}), 500

@app.route('/api/instagram-accounts/active', methods=['GET'])
@token_required
def get_active_instagram_accounts():
    """Get only active Instagram accounts"""
    try:
        accounts = instagram_accounts_manager.get_active_accounts()
        return jsonify({'success': True, 'accounts': accounts})
    except Exception as e:
        logger.error(f"Get active accounts error: {e}")
        return jsonify({'success': False, 'message': 'Failed to retrieve active accounts'}), 500

@app.route('/api/instagram-accounts', methods=['POST'])
@admin_required
def add_instagram_account():
    """Add a new Instagram account (Admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        account = instagram_accounts_manager.add_account(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            notes=data.get('notes', '')
        )
        
        # Log activity
        log_user_activity('create_instagram_account', 
                         f"Added Instagram account: {data['username']}")
        
        return jsonify({'success': True, 'account': account})
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Add account error: {e}")
        return jsonify({'success': False, 'message': 'Failed to add account'}), 500

@app.route('/api/instagram-accounts/<account_id>', methods=['PUT'])
@admin_required
def update_instagram_account(account_id):
    """Update an Instagram account (Admin only)"""
    try:
        data = request.get_json()
        
        # Remove empty strings to avoid overwriting with empty values
        updates = {k: v for k, v in data.items() if v != ''}
        
        success = instagram_accounts_manager.update_account(account_id, updates)
        
        if success:
            # Log activity
            log_user_activity('update_instagram_account', 
                             f"Updated Instagram account: {account_id}")
            
            account = instagram_accounts_manager.get_account_by_id(account_id)
            return jsonify({'success': True, 'account': account})
        else:
            return jsonify({'success': False, 'message': 'Account not found'}), 404
            
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Update account error: {e}")
        return jsonify({'success': False, 'message': 'Failed to update account'}), 500

@app.route('/api/instagram-accounts/<account_id>', methods=['DELETE'])
@admin_required
def delete_instagram_account(account_id):
    """Delete an Instagram account (Admin only)"""
    try:
        account = instagram_accounts_manager.get_account_by_id(account_id)
        if not account:
            return jsonify({'success': False, 'message': 'Account not found'}), 404
        
        success = instagram_accounts_manager.delete_account(account_id)
        
        if success:
            # Log activity
            log_user_activity('delete_instagram_account', 
                             f"Deleted Instagram account: {account['username']}")
            
            return jsonify({'success': True, 'message': 'Account deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete account'}), 500
            
    except Exception as e:
        logger.error(f"Delete account error: {e}")
        return jsonify({'success': False, 'message': 'Failed to delete account'}), 500

@app.route('/api/instagram-accounts/import', methods=['POST'])
@admin_required
def import_instagram_accounts():
    """Import Instagram accounts from Excel/CSV file (Admin only)"""
    try:
        if 'accounts_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['accounts_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename, 'files'):
            return jsonify({'success': False, 'message': 'Invalid file type. Please upload CSV or Excel file'}), 400
        
        # Generate script ID for temporary file management
        script_id = generate_script_id()
        
        # Save uploaded file temporarily
        temp_file_path = save_temp_file(file, script_id, "accounts_import")
        
        # Import accounts
        result = instagram_accounts_manager.import_accounts_from_file(temp_file_path)
        
        # Clean up temporary file
        cleanup_temp_files(script_id)
        
        if result['success']:
            # Log activity
            log_user_activity('import_instagram_accounts', 
                             f"Imported {result['added_count']} Instagram accounts")
            
            return jsonify({
                'success': True,
                'message': f"Successfully imported {result['added_count']} accounts",
                'added_count': result['added_count'],
                'skipped_count': result['skipped_count'],
                'skipped_accounts': result['skipped_accounts']
            })
        else:
            return jsonify({'success': False, 'message': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Import accounts error: {e}")
        # Clean up on error
        if 'script_id' in locals():
            cleanup_temp_files(script_id)
        return jsonify({'success': False, 'message': 'Failed to import accounts'}), 500

@app.route('/api/admin/script-logs', methods=['GET'])
@token_required
@admin_required
def get_all_script_logs():
    """Get script execution history for all users (admin only)"""
    try:
        user_id_filter = request.args.get('user_id')
        limit = int(request.args.get('limit', 100))
        
        # Combine current active scripts and completed/failed scripts
        all_scripts = []
        
        # Add active/recent scripts with user info
        for script_id, script_data in active_scripts.items():
            user_id = script_data.get('user_id', 'system')
            
            # Filter by user if specified
            if user_id_filter and user_id != user_id_filter:
                continue
                
            # Get user info
            user_info = None
            if user_id != 'system':
                try:
                    user_info = user_manager.get_user_by_id(user_id)
                except:
                    user_info = None
            
            script_log = {
                'script_id': script_id,
                'user_id': user_id,
                'user_name': user_info.get('name', 'Unknown') if user_info else 'System',
                'user_username': user_info.get('username', 'system') if user_info else 'system',
                'script_type': script_data.get('type', 'unknown'),
                'status': script_data.get('status', 'unknown'),
                'start_time': script_data.get('start_time'),
                'end_time': script_data.get('end_time'),
                'error': script_data.get('error'),
                'stop_reason': script_data.get('stop_reason'),
                'config': script_data.get('config', {}),
                'logs_available': script_id in script_logs and len(script_logs[script_id]) > 0
            }
            all_scripts.append(script_log)
        
        # Sort by start_time (most recent first)
        all_scripts.sort(key=lambda x: x['start_time'] or '', reverse=True)
        
        # Apply limit
        if limit > 0:
            all_scripts = all_scripts[:limit]
        
        return jsonify({'success': True, 'script_logs': all_scripts})
        
    except Exception as e:
        logger.error(f"Get script logs error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
