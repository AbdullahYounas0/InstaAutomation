#!/usr/bin/env python3
"""
Debug script to test authentication
"""

import json
import bcrypt
from auth import UserManager

def test_authentication():
    """Test authentication with debug information"""
    print("=== Authentication Debug Test ===")
    
    # Initialize user manager
    user_manager = UserManager()
    
    # Load users
    users = user_manager.load_users()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  - {user['username']} ({user['role']}) - Active: {user['is_active']}")
    
    # Test admin credentials
    print("\n=== Testing Admin Credentials ===")
    test_credentials = [
        ("admin", "admin123"),
        ("admin", "admin"),
        ("u2@gmail.com", "123456"),  # Assuming a common password
    ]
    
    for username, password in test_credentials:
        print(f"\nTesting: {username} / {password}")
        result = user_manager.authenticate_user(username, password)
        print(f"Result: {result}")
        
        # If failed, let's check the stored password hash
        for user in users:
            if user['username'] == username:
                print(f"Stored password hash: {user['password']}")
                # Test password verification directly
                try:
                    is_valid = user_manager.verify_password(password, user['password'])
                    print(f"Direct password verification: {is_valid}")
                except Exception as e:
                    print(f"Password verification error: {e}")
                break

if __name__ == "__main__":
    test_authentication()
