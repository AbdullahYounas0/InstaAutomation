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
from flask import request, jsonify, current_app

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
TOKEN_EXPIRATION_HOURS = 24
USERS_FILE = 'users.json'
ACTIVITY_LOG_FILE = 'activity_logs.json'

class UserManager:
    def __init__(self):
        self.users_file = USERS_FILE
        self.activity_log_file = ACTIVITY_LOG_FILE
        self.ensure_files_exist()
        self.ensure_admin_exists()
        self.migrate_logs_if_needed()
    
    def ensure_files_exist(self):
        """Ensure users.json and activity_logs.json exist"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump([], f)
        
        if not os.path.exists(self.activity_log_file):
            with open(self.activity_log_file, 'w') as f:
                json.dump([], f)
    
    def migrate_logs_if_needed(self):
        """Add location data to existing logs that don't have it"""
        try:
            logs = self.load_activity_logs()
            modified = False
            
            for log in logs:
                if 'city' not in log or 'country' not in log:
                    location = self.get_location_from_ip(log.get('ip_address', 'system'))
                    log['city'] = location['city']
                    log['country'] = location['country']
                    log['country_code'] = location['country_code']
                    modified = True
            
            if modified:
                self.save_activity_logs(logs)
                print("Migrated existing logs with location data")
        except Exception as e:
            print(f"Error migrating logs: {e}")
    
    def ensure_admin_exists(self):
        """Ensure default admin user exists"""
        users = self.load_users()
        admin_exists = any(user['role'] == 'admin' for user in users)
        
        if not admin_exists:
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
    
    def load_users(self):
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_users(self, users):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def load_activity_logs(self):
        """Load activity logs from JSON file"""
        try:
            with open(self.activity_log_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_activity_logs(self, logs):
        """Save activity logs to JSON file"""
        with open(self.activity_log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, name, username, password, role='va'):
        """Create new user"""
        users = self.load_users()
        
        # Check if username already exists
        if any(user['username'] == username for user in users):
            return {'success': False, 'message': 'Username already exists'}
        
        # Generate user ID
        user_id = f"{role}-{len(users) + 1:03d}"
        
        new_user = {
            'id': user_id,
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
        
        return {'success': True, 'message': 'User created successfully', 'user_id': user_id}
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        users = self.load_users()
        
        for user in users:
            if user['username'] == username and user['is_active']:
                if self.verify_password(password, user['password']):
                    # Update last login
                    user['last_login'] = datetime.now().isoformat()
                    self.save_users(users)
                    
                    # Log activity
                    self.log_activity(user['id'], 'login', f"User {username} logged in")
                    
                    # Generate token
                    token = self.generate_token(user)
                    
                    return {
                        'success': True,
                        'token': token,
                        'user': {
                            'id': user['id'],
                            'name': user['name'],
                            'username': user['username'],
                            'role': user['role']
                        }
                    }
        
        return {'success': False, 'message': 'Invalid credentials'}
    
    def generate_token(self, user):
        """Generate JWT token"""
        payload = {
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return {'success': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'message': 'Invalid token'}
    
    def get_all_users(self):
        """Get all users (admin only)"""
        users = self.load_users()
        # Remove password field for security
        return [{k: v for k, v in user.items() if k != 'password'} for user in users]
    
    def update_user(self, user_id, updates):
        """Update user information"""
        users = self.load_users()
        
        for user in users:
            if user['id'] == user_id:
                # Handle password update
                if 'password' in updates:
                    updates['password'] = self.hash_password(updates['password'])
                
                # Update fields
                user.update(updates)
                self.save_users(users)
                
                # Log activity
                self.log_activity('admin', 'user_updated', f"User {user['username']} updated")
                
                return {'success': True, 'message': 'User updated successfully'}
        
        return {'success': False, 'message': 'User not found'}
    
    def deactivate_user(self, user_id):
        """Deactivate user"""
        users = self.load_users()
        
        for user in users:
            if user['id'] == user_id:
                user['is_active'] = False
                self.save_users(users)
                
                # Log activity
                self.log_activity('admin', 'user_deactivated', f"User {user['username']} deactivated")
                
                return {'success': True, 'message': 'User deactivated successfully'}
        
        return {'success': False, 'message': 'User not found'}
    
    def delete_user(self, user_id):
        """Delete user permanently"""
        users = self.load_users()
        
        # Find user to delete
        user_to_delete = None
        for user in users:
            if user['id'] == user_id:
                user_to_delete = user
                break
        
        if not user_to_delete:
            return {'success': False, 'message': 'User not found'}
        
        # Prevent deletion of the last admin
        if user_to_delete['role'] == 'admin':
            admin_count = sum(1 for u in users if u['role'] == 'admin')
            if admin_count <= 1:
                return {'success': False, 'message': 'Cannot delete the last admin user'}
        
        # Remove user from list
        users = [user for user in users if user['id'] != user_id]
        self.save_users(users)
        
        # Log activity
        self.log_activity('admin', 'user_deleted', f"User {user_to_delete['username']} deleted permanently")
        
        return {'success': True, 'message': 'User deleted successfully'}
    
    def get_location_from_ip(self, ip_address):
        """Get location information from IP address using a free API"""
        if ip_address in ['127.0.0.1', 'localhost', 'system']:
            return {
                'city': 'Local',
                'country': 'Local',
                'country_code': 'LC'
            }
        
        try:
            # Using ip-api.com free service (no API key required)
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return {
                        'city': data.get('city', 'Unknown'),
                        'country': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'UN')
                    }
        except Exception as e:
            print(f"Error getting location for IP {ip_address}: {e}")
        
        return {
            'city': 'Unknown',
            'country': 'Unknown',
            'country_code': 'UN'
        }
    
    def log_activity(self, user_id, action, details):
        """Log user activity"""
        logs = self.load_activity_logs()
        
        ip_address = request.remote_addr if request else 'system'
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
        
        # Keep only last 1000 logs
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        self.save_activity_logs(logs)
    
    def get_activity_logs(self, user_id=None, limit=100):
        """Get activity logs"""
        logs = self.load_activity_logs()
        
        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]
        
        # Return most recent logs first
        return sorted(logs, key=lambda x: x['timestamp'], reverse=True)[:limit]

# Initialize user manager
user_manager = UserManager()

# Decorators for authentication
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

def log_user_activity(action, details):
    """Helper function to log user activity"""
    if hasattr(request, 'current_user'):
        user_manager.log_activity(request.current_user['user_id'], action, details)
