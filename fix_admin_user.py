#!/usr/bin/env python3

"""
Fix Admin User Script - Ensures admin user exists with proper password hash
This addresses the most common cause of 401 errors
"""

import json
import bcrypt
import os
from datetime import datetime

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_admin_user():
    """Create or update admin user with proper password hash"""
    users_file = 'users.json'
    
    # Create admin user data
    admin_password = "admin123"  # Default password
    hashed_password = hash_password(admin_password)
    
    admin_user = {
        "id": "admin-001",
        "name": "Administrator",
        "username": "admin",
        "password": hashed_password,
        "role": "admin",
        "created_at": datetime.now().isoformat(),
        "is_active": True,
        "last_login": None
    }
    
    # Load existing users or create new list
    users = []
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            users = []
    
    # Check if admin already exists
    admin_exists = False
    for i, user in enumerate(users):
        if user.get('username') == 'admin' or user.get('role') == 'admin':
            users[i] = admin_user  # Update existing admin
            admin_exists = True
            print("✅ Updated existing admin user")
            break
    
    if not admin_exists:
        users.append(admin_user)
        print("✅ Created new admin user")
    
    # Save users file
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"✅ Admin user saved to {users_file}")
    print(f"   Username: admin")
    print(f"   Password: {admin_password}")
    print(f"   Password Hash: {hashed_password[:50]}...")

def create_activity_logs():
    """Create empty activity logs file"""
    activity_file = 'activity_logs.json'
    if not os.path.exists(activity_file):
        with open(activity_file, 'w') as f:
            json.dump([], f)
        print(f"✅ Created {activity_file}")

def create_instagram_accounts():
    """Create empty instagram accounts file"""
    accounts_file = 'instagram_accounts.json'
    if not os.path.exists(accounts_file):
        with open(accounts_file, 'w') as f:
            json.dump([], f)
        print(f"✅ Created {accounts_file}")

def main():
    print("🔧 FIXING ADMIN USER AND FILES")
    print("==============================")
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Run this script from the backend directory")
        print("   cd /var/www/insta-automation/backend")
        print("   python3 fix_admin_user.py")
        return False
    
    try:
        create_admin_user()
        create_activity_logs()
        create_instagram_accounts()
        
        print("\n🎉 ADMIN USER FIX COMPLETE!")
        print("===========================")
        print("✅ Admin user created/updated with proper password hash")
        print("✅ Required JSON files created")
        print("\n🔑 Login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n📝 Next steps:")
        print("   1. Restart the backend service: sudo systemctl restart insta-automation")
        print("   2. Test login at your website")
        print("   3. Change the default password after first login")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()
