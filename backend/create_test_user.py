#!/usr/bin/env python3
"""
Create a test VA user for demonstration
"""

from auth import UserManager

def create_test_user():
    """Create a test VA user"""
    print("=== Creating Test VA User ===")
    
    user_manager = UserManager()
    
    # Create test user
    result = user_manager.create_user(
        name="Test VA User",
        username="testuser",
        password="testpass",
        role="va"
    )
    
    print(f"Result: {result}")
    
    if result['success']:
        print("✅ Test user created successfully")
        
        # Show all users
        users = user_manager.load_users()
        print(f"\nCurrent users ({len(users)}):")
        for user in users:
            print(f"  - {user['id']}: {user['username']} ({user['role']}) - Active: {user['is_active']}")
    else:
        print(f"❌ Failed to create test user: {result['message']}")

if __name__ == "__main__":
    create_test_user()
