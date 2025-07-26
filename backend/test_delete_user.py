#!/usr/bin/env python3
"""
Test the delete user functionality
"""

from auth import UserManager

def test_delete_user():
    """Test delete user functionality"""
    print("=== Delete User Test ===")
    
    user_manager = UserManager()
    
    # Show current users
    users = user_manager.load_users()
    print(f"Current users ({len(users)}):")
    for user in users:
        print(f"  - {user['id']}: {user['username']} ({user['role']}) - Active: {user['is_active']}")
    
    # Test cases
    print("\n=== Test Cases ===")
    
    # Test 1: Try to delete admin (should fail - last admin protection)
    admin_users = [u for u in users if u['role'] == 'admin']
    if len(admin_users) == 1:
        admin_id = admin_users[0]['id']
        print(f"\nTest 1: Trying to delete last admin ({admin_id})")
        result = user_manager.delete_user(admin_id)
        print(f"Result: {result}")
        expected = "Cannot delete the last admin user"
        print(f"✅ Passed" if expected in result.get('message', '') else f"❌ Failed")
    
    # Test 2: Try to delete non-existent user
    print(f"\nTest 2: Trying to delete non-existent user")
    result = user_manager.delete_user('fake-user-999')
    print(f"Result: {result}")
    expected = "User not found"
    print(f"✅ Passed" if expected in result.get('message', '') else f"❌ Failed")
    
    # Test 3: Try to delete VA user (should work)
    va_users = [u for u in users if u['role'] == 'va']
    if va_users:
        va_id = va_users[0]['id']
        va_username = va_users[0]['username']
        print(f"\nTest 3: Trying to delete VA user ({va_id}: {va_username})")
        result = user_manager.delete_user(va_id)
        print(f"Result: {result}")
        
        if result.get('success'):
            print("✅ Delete successful")
            # Verify user was actually deleted
            updated_users = user_manager.load_users()
            deleted_user_exists = any(u['id'] == va_id for u in updated_users)
            print(f"User still exists: {deleted_user_exists}")
            print(f"✅ User properly removed" if not deleted_user_exists else f"❌ User still exists!")
        else:
            print(f"❌ Delete failed: {result.get('message')}")

if __name__ == "__main__":
    test_delete_user()
