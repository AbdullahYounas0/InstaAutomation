#!/usr/bin/env python3
"""
Create a second admin user for testing deletion
"""

from auth import UserManager

def create_second_admin():
    """Create a second admin user"""
    print("=== Creating Second Admin User ===")
    
    user_manager = UserManager()
    
    # Create second admin
    result = user_manager.create_user(
        name="Secondary Admin",
        username="admin2",
        password="admin2pass",
        role="admin"
    )
    
    print(f"Result: {result}")
    
    if result['success']:
        print("✅ Second admin created successfully")
        
        # Show all users
        users = user_manager.load_users()
        print(f"\nCurrent users ({len(users)}):")
        for user in users:
            print(f"  - {user['id']}: {user['username']} ({user['role']}) - Active: {user['is_active']}")
            
        # Test that now we can delete one admin
        admin_users = [u for u in users if u['role'] == 'admin']
        if len(admin_users) >= 2:
            second_admin_id = admin_users[1]['id']
            print(f"\n=== Testing Admin Deletion (now that we have 2) ===")
            print(f"Attempting to delete: {second_admin_id}")
            delete_result = user_manager.delete_user(second_admin_id)
            print(f"Delete result: {delete_result}")
            
            if delete_result['success']:
                print("✅ Admin deletion worked (we had multiple admins)")
                # Recreate the admin for future tests
                user_manager.create_user(
                    name="Secondary Admin",
                    username="admin2", 
                    password="admin2pass",
                    role="admin"
                )
                print("✅ Recreated second admin for testing")
    else:
        print(f"❌ Failed to create second admin: {result['message']}")

if __name__ == "__main__":
    create_second_admin()
