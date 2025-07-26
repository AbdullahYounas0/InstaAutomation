#!/usr/bin/env python3
"""
Script to reset user passwords for debugging
"""

import json
from auth import UserManager

def reset_user_password():
    """Reset user passwords to known values"""
    print("=== User Password Reset ===")
    
    user_manager = UserManager()
    users = user_manager.load_users()
    
    # Reset passwords
    for user in users:
        if user['username'] == 'admin':
            # Keep admin password as admin123
            user['password'] = user_manager.hash_password('admin123')
            print(f"Admin password set to: admin123")
        elif user['username'] == 'u2@gmail.com':
            # Set VA password to a known value
            user['password'] = user_manager.hash_password('123456')
            print(f"VA user {user['username']} password set to: 123456")
    
    # Save updated users
    user_manager.save_users(users)
    print("\nPasswords updated successfully!")
    
    # Test the credentials
    print("\n=== Testing Updated Credentials ===")
    test_credentials = [
        ("admin", "admin123"),
        ("u2@gmail.com", "123456"),
    ]
    
    for username, password in test_credentials:
        print(f"\nTesting: {username} / {password}")
        result = user_manager.authenticate_user(username, password)
        if result['success']:
            print("✅ Authentication successful!")
        else:
            print(f"❌ Authentication failed: {result['message']}")

if __name__ == "__main__":
    reset_user_password()
