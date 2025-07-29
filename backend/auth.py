"""
Authentication and User Management Module
Handles admin and VA user authentication, user management, and session tracking
"""

import jwt
import bcrypt
import json
import os
import requests
from datetime import datetime, timedelta
from functools import wraps
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

# For compatibility during migration, we'll handle both Flask and FastAPI
try:
    from fastapi import HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Fallback for Flask
    try:
        from flask import request, jsonify
    except ImportError:
        pass

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
TOKEN_EXPIRATION_HOURS = 24
USERS_FILE = 'users.json'
ACTIVITY_LOG_FILE = 'activity_logs.json'

if FASTAPI_AVAILABLE:
    security = HTTPBearer()

# Enhanced logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add handler if not already present
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class UserManager:
    def __init__(self):
        self.users_file = USERS_FILE
        self.activity_log_file = ACTIVITY_LOG_FILE
        self.ensure_files_exist()
        self.ensure_admin_exists()
        self.migrate_logs_if_needed()
    
    def ensure_files_exist(self):
        """Ensure users.json and activity_logs.json exist"""
        logger.info("Ensuring required files exist")
        
        if not os.path.exists(self.users_file):
            logger.info(f"Creating users file: {self.users_file}")
            with open(self.users_file, 'w') as f:
                json.dump([], f)
        else:
            logger.debug(f"Users file already exists: {self.users_file}")
        
        if not os.path.exists(self.activity_log_file):
            logger.info(f"Creating activity log file: {self.activity_log_file}")
            with open(self.activity_log_file, 'w') as f:
                json.dump([], f)
        else:
            logger.debug(f"Activity log file already exists: {self.activity_log_file}")
    
    def migrate_logs_if_needed(self):
        """Add location data to existing logs that don't have it"""
        logger.info("Checking if log migration is needed")
        try:
            logs = self.load_activity_logs()
            modified = False
            migration_count = 0
            
            for log in logs:
                if 'city' not in log or 'country' not in log:
                    location = self.get_location_from_ip(log.get('ip_address', 'system'))
                    log['city'] = location['city']
                    log['country'] = location['country']
                    log['country_code'] = location['country_code']
                    modified = True
                    migration_count += 1
            
            if modified:
                self.save_activity_logs(logs)
                logger.info(f"Successfully migrated {migration_count} logs with location data")
            else:
                logger.debug("No log migration needed - all logs already have location data")
        except Exception as e:
            logger.error(f"Error migrating logs: {e}")
            print(f"Error migrating logs: {e}")
    
    def ensure_admin_exists(self):
        """Ensure default admin user exists"""
        logger.info("Checking if admin user exists")
        users = self.load_users()
        admin_exists = any(user['role'] == 'admin' for user in users)
        
        if not admin_exists:
            logger.info("No admin user found, creating default admin user")
            # Create default admin user
            admin_user = {
                'id': 'admin-001',
                'name': 'Administrator',
                'username': 'admin',
                'password': self.hash_password('admin123'),
                'role': 'admin',
                'created_at': datetime.now().isoformat(),
                'is_active': True,
                'last_login': None
            }
            users.append(admin_user)
            self.save_users(users)
            logger.info("Default admin user created successfully with username 'admin'")
        else:
            logger.debug("Admin user already exists")
    
    def load_users(self):
        """Load users from JSON file"""
        try:
            logger.debug(f"Loading users from {self.users_file}")
            with open(self.users_file, 'r') as f:
                users = json.load(f)
                logger.debug(f"Successfully loaded {len(users)} users")
                return users
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading users file: {e}. Returning empty list")
            return []
    
    def save_users(self, users):
        """Save users to JSON file"""
        try:
            logger.debug(f"Saving {len(users)} users to {self.users_file}")
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            logger.debug("Users saved successfully")
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            raise
    
    def load_activity_logs(self):
        """Load activity logs from JSON file"""
        try:
            logger.debug(f"Loading activity logs from {self.activity_log_file}")
            with open(self.activity_log_file, 'r') as f:
                logs = json.load(f)
                logger.debug(f"Successfully loaded {len(logs)} activity logs")
                return logs
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading activity logs file: {e}. Returning empty list")
            return []
    
    def save_activity_logs(self, logs):
        """Save activity logs to JSON file"""
        try:
            logger.debug(f"Saving {len(logs)} activity logs to {self.activity_log_file}")
            with open(self.activity_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            logger.debug("Activity logs saved successfully")
        except Exception as e:
            logger.error(f"Error saving activity logs: {e}")
            raise
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        logger.debug("Hashing password")
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        logger.debug("Verifying password")
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, name, username, password, role='va'):
        """Create new user"""
        logger.info(f"Attempting to create new user: {username} with role: {role}")
        users = self.load_users()
        
        # Check if username already exists
        if any(user['username'] == username for user in users):
            logger.warning(f"Username already exists: {username}")
            return {'success': False, 'message': 'Username already exists'}
        
        # Generate user ID
        user_id = f"{role}-{len(users) + 1:03d}"
        logger.debug(f"Generated user ID: {user_id}")
        
        new_user = {
            'user_id': user_id,
            'name': name,
            'username': username,
            'password': self.hash_password(password),
            'role': role,
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'last_login': None
        }
        
        users.append(new_user)
        self.save_users(users)
        
        # Log activity
        self.log_activity('system', 'user_created', f"User {username} created by admin")
        logger.info(f"User created successfully: {username} (ID: {user_id})")
        
        return {'success': True, 'message': 'User created successfully', 'user_id': user_id}
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        logger.info(f"Authentication attempt for username: {username}")
        users = self.load_users()
        
        for user in users:
            if user['username'] == username and user.get('is_active', True):
                logger.debug(f"Found active user: {username}")
                if self.verify_password(password, user['password']):
                    # Handle migration from 'id' to 'user_id'
                    user_id = user.get('user_id', user.get('id', f"migrated_{username}"))
                    logger.info(f"Password verification successful for user: {username} (ID: {user_id})")
                    
                    # Update last login
                    user['last_login'] = datetime.now().isoformat()
                    self.save_users(users)
                    
                    # Log activity
                    self.log_activity(user_id, 'login', f"User {username} logged in")
                    
                    # Generate token
                    token = self.generate_token(user, user_id)
                    
                    return {
                        'success': True,
                        'token': token,
                        'user': {
                            'user_id': user_id,
                            'id': user_id,  # For backward compatibility
                            'name': user['name'],
                            'username': user['username'],
                            'role': user['role']
                        }
                    }
                else:
                    logger.warning(f"Password verification failed for user: {username}")
            elif user['username'] == username and not user.get('is_active', True):
                logger.warning(f"Inactive user attempted login: {username}")
        
        logger.warning(f"Authentication failed for username: {username}")
        return {'success': False, 'message': 'Invalid credentials'}
    
    def generate_token(self, user, user_id=None):
        """Generate JWT token"""
        if user_id is None:
            user_id = user.get('user_id', user.get('id', f"migrated_{user['username']}"))
        
        logger.debug(f"Generating token for user: {user['username']} (ID: {user_id})")
        payload = {
            'user_id': user_id,
            'username': user['username'],
            'name': user['name'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        logger.debug(f"Token generated successfully for user: {user['username']}")
        return token
    
    def verify_token(self, token):
        """Verify JWT token"""
        logger.debug("Verifying JWT token")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            logger.debug(f"Token verified successfully for user: {payload.get('username')}")
            return {'success': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token expired")
            return {'success': False, 'message': 'Token expired'}
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed: Invalid token - {e}")
            return {'success': False, 'message': 'Invalid token'}
    
    def get_all_users(self):
        """Get all users (admin only)"""
        logger.info("Retrieving all users")
        users = self.load_users()
        logger.debug(f"Found {len(users)} users in database")
        
        # Remove password field for security and map user_id to id for frontend compatibility
        result = []
        for user in users:
            user_dict = {k: v for k, v in user.items() if k != 'password'}
            # Map user_id to id for frontend compatibility
            if 'user_id' in user_dict:
                user_dict['id'] = user_dict.pop('user_id')
            result.append(user_dict)
        
        logger.debug(f"Returning {len(result)} users (passwords removed)")
        return result
    
    def update_user(self, user_id, updates):
        """Update user information"""
        logger.info(f"Updating user: {user_id} with updates: {list(updates.keys())}")
        users = self.load_users()
        
        for user in users:
            if user['user_id'] == user_id:
                logger.debug(f"Found user to update: {user['username']}")
                # Handle password update
                if 'password' in updates:
                    logger.debug("Updating user password")
                    updates['password'] = self.hash_password(updates['password'])
                
                # Update fields
                user.update(updates)
                self.save_users(users)
                
                # Log activity
                self.log_activity('admin', 'user_updated', f"User {user['username']} updated")
                logger.info(f"User updated successfully: {user['username']} (ID: {user_id})")
                
                return {'success': True, 'message': 'User updated successfully'}
        
        logger.warning(f"User not found for update: {user_id}")
        return {'success': False, 'message': 'User not found'}
    
    def deactivate_user(self, user_id):
        """Deactivate user"""
        logger.info(f"Deactivating user: {user_id}")
        users = self.load_users()
        
        for user in users:
            if user['user_id'] == user_id:
                logger.debug(f"Found user to deactivate: {user['username']}")
                user['is_active'] = False
                self.save_users(users)
                
                # Log activity
                self.log_activity('admin', 'user_deactivated', f"User {user['username']} deactivated")
                logger.info(f"User deactivated successfully: {user['username']} (ID: {user_id})")
                
                return {'success': True, 'message': 'User deactivated successfully'}
        
        logger.warning(f"User not found for deactivation: {user_id}")
        return {'success': False, 'message': 'User not found'}
    
    def delete_user(self, user_id):
        """Delete user permanently"""
        logger.info(f"Deleting user permanently: {user_id}")
        users = self.load_users()
        
        # Find user to delete
        user_to_delete = None
        for user in users:
            if user['user_id'] == user_id:
                user_to_delete = user
                logger.debug(f"Found user to delete: {user['username']}")
                break
        
        if not user_to_delete:
            logger.warning(f"User not found for deletion: {user_id}")
            return {'success': False, 'message': 'User not found'}
        
        # Prevent deletion of the last admin
        if user_to_delete['role'] == 'admin':
            admin_count = sum(1 for u in users if u['role'] == 'admin')
            logger.debug(f"Admin count check: {admin_count} admin(s) found")
            if admin_count <= 1:
                logger.warning(f"Attempted to delete the last admin user: {user_to_delete['username']}")
                return {'success': False, 'message': 'Cannot delete the last admin user'}
        
        # Remove user from list
        users = [user for user in users if user['user_id'] != user_id]
        self.save_users(users)
        
        # Log activity
        self.log_activity('admin', 'user_deleted', f"User {user_to_delete['username']} deleted permanently")
        logger.info(f"User deleted successfully: {user_to_delete['username']} (ID: {user_id})")
        
        return {'success': True, 'message': 'User deleted successfully'}
    
    def get_location_from_ip(self, ip_address):
        """Get location information from IP address using a free API"""
        logger.debug(f"Getting location for IP: {ip_address}")
        
        if ip_address in ['127.0.0.1', 'localhost', 'system']:
            logger.debug("Local IP detected, returning local location")
            return {
                'city': 'Local',
                'country': 'Local',
                'country_code': 'LC'
            }
        
        try:
            # Using ip-api.com free service (no API key required)
            logger.debug(f"Making API request to get location for IP: {ip_address}")
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    location = {
                        'city': data.get('city', 'Unknown'),
                        'country': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'UN')
                    }
                    logger.debug(f"Location found: {location['city']}, {location['country']}")
                    return location
                else:
                    logger.warning(f"IP API returned failure status for IP: {ip_address}")
            else:
                logger.warning(f"IP API request failed with status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting location for IP {ip_address}: {e}")
        
        logger.debug("Returning unknown location as fallback")
        return {
            'city': 'Unknown',
            'country': 'Unknown',
            'country_code': 'UN'
        }
    
    def log_activity(self, user_id, action, details, ip_address='system'):
        """Log user activity"""
        logger.debug(f"Logging activity - User: {user_id}, Action: {action}, IP: {ip_address}")
        try:
            logs = self.load_activity_logs()
            location = self.get_location_from_ip(ip_address)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'action': action,
                'details': details,
                'ip_address': ip_address,
                'city': location['city'],
                'country': location['country'],
                'country_code': location['country_code']
            }
            
            logs.append(log_entry)
            logger.debug(f"Activity logged: {action} for user {user_id}")
            
            # Keep only last 1000 logs
            if len(logs) > 1000:
                logs = logs[-1000:]
                logger.debug("Trimmed activity logs to keep last 1000 entries")
            
            self.save_activity_logs(logs)
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def get_activity_logs(self, user_id=None, limit=100):
        """Get activity logs"""
        logger.debug(f"Retrieving activity logs - User: {user_id}, Limit: {limit}")
        logs = self.load_activity_logs()
        
        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]
            logger.debug(f"Filtered logs for user {user_id}: {len(logs)} entries")
        
        # Return most recent logs first
        result = sorted(logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
        logger.debug(f"Returning {len(result)} activity log entries")
        return result

# Initialize user manager
logger.info("Initializing UserManager")
user_manager = UserManager()
logger.info("UserManager initialized successfully")

# FastAPI dependency functions (only if FastAPI is available)
if FASTAPI_AVAILABLE:
    async def verify_token_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """FastAPI dependency to verify JWT token"""
        logger.debug("Verifying token via dependency")
        
        if not credentials:
            logger.warning("Token verification failed: Token is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = user_manager.verify_token(credentials.credentials)
        
        if not result['success']:
            logger.warning(f"Token verification failed: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result['message'],
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user still exists and is active
        users = user_manager.load_users()
        user_id = result['payload']['user_id']
        user = next((u for u in users if u.get('user_id', u.get('id')) == user_id), None)
        
        if not user or not user.get('is_active', True):
            logger.warning(f"User authentication failed: User {user_id} not found or inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return result['payload']

    async def admin_required_dependency(current_user: dict = Depends(verify_token_dependency)):
        """FastAPI dependency to require admin role"""
        if current_user['role'] != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user

# Decorators for authentication (Flask compatibility)
def token_required(f):
    """Decorator to require valid token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        # If no token in header, check form data (for sendBeacon requests)
        if not token and request.form and 'token' in request.form:
            token = request.form['token']
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        # Verify token
        result = user_manager.verify_token(token)
        if not result['success']:
            return jsonify({'message': result['message']}), 401
        
        # Add user info to request context
        request.current_user = result['payload']
        request.user_id = result['payload']['user_id']  # Add for backward compatibility
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user['role'] != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated

def log_user_activity(action, details, user_id=None, ip_address='system'):
    """Helper function to log user activity"""
    logger.debug(f"Logging user activity: {action} for user {user_id}")
    if user_id:
        user_manager.log_activity(user_id, action, details, ip_address)
    else:
        user_manager.log_activity('system', action, details, ip_address)
