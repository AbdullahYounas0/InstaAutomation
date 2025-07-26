#!/usr/bin/env python3
"""
Test the visual mode functionality in warmup endpoint
"""

import requests
import json
import os

BASE_URL = "http://localhost:5000"
TEST_ACCOUNTS_FILE = "test_accounts.csv"

def create_test_accounts_file():
    """Create a test accounts file"""
    with open(TEST_ACCOUNTS_FILE, 'w') as f:
        f.write("username,password\n")
        f.write("test_user1,test_pass1\n")

def test_visual_mode():
    """Test warmup endpoint with visual mode enabled and disabled"""
    print("=== Testing Visual Mode Parameter ===")
    
    # Step 1: Login to get token
    print("\n1. Authenticating...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.text}")
            return False
        
        auth_response = response.json()
        if not auth_response.get('success'):
            print(f"❌ Login failed: {auth_response.get('message')}")
            return False
        
        token = auth_response.get('token')
        print("✅ Authentication successful!")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Test with visual_mode = false
    print("\n2. Testing with Visual Mode DISABLED...")
    test_visual_mode_setting(token, False)
    
    # Step 3: Test with visual_mode = true  
    print("\n3. Testing with Visual Mode ENABLED...")
    test_visual_mode_setting(token, True)
    
    return True

def test_visual_mode_setting(token, visual_mode):
    """Test warmup with specific visual mode setting"""
    
    if not os.path.exists(TEST_ACCOUNTS_FILE):
        create_test_accounts_file()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        'warmup_duration_min': '1',  # Very short for testing
        'warmup_duration_max': '2',
        'scheduler_delay': '0',
        'max_concurrent': '1',
        'visual_mode': str(visual_mode).lower(),
        'feed_scroll': 'true',
        'watch_reels': 'false',
        'like_reels': 'false',
        'like_posts': 'false',
        'explore_page': 'false',
        'random_visits': 'false',
        'activity_delay_min': '1',
        'activity_delay_max': '2',
        'scroll_attempts_min': '1',
        'scroll_attempts_max': '2'
    }
    
    try:
        with open(TEST_ACCOUNTS_FILE, 'rb') as f:
            files = {'accounts_file': f}
            response = requests.post(f"{BASE_URL}/api/warmup/start", 
                                   data=data, 
                                   files=files, 
                                   headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            script_id = result.get('script_id')
            print(f"✅ Visual Mode {'ENABLED' if visual_mode else 'DISABLED'} - Script started!")
            print(f"Script ID: {script_id}")
            
            # Get the script config to verify visual_mode was stored correctly
            config_response = requests.get(f"{BASE_URL}/api/script/{script_id}/status", 
                                         headers=headers)
            if config_response.status_code == 200:
                config = config_response.json().get('config', {})
                stored_visual_mode = config.get('visual_mode', False)
                print(f"Visual Mode stored in config: {stored_visual_mode}")
                
                if stored_visual_mode == visual_mode:
                    print(f"✅ Visual mode setting correctly stored!")
                else:
                    print(f"❌ Visual mode mismatch: expected {visual_mode}, got {stored_visual_mode}")
            
            # Stop the script quickly
            stop_response = requests.post(f"{BASE_URL}/api/script/{script_id}/stop", 
                                        headers=headers)
            if stop_response.status_code == 200:
                print(f"✅ Script stopped successfully")
                
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    print("Visual Mode Test for Instagram Warmup")
    print("=====================================")
    
    try:
        # Check if backend is running
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print("❌ Backend is not running! Start the Flask server first.")
            exit(1)
        
        print("✅ Backend is running")
        
        # Run the test
        if test_visual_mode():
            print("\n🎉 Visual mode test completed!")
        else:
            print("\n❌ Visual mode test failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend connection failed! Make sure the Flask server is running.")
        exit(1)
    
    finally:
        # Cleanup
        if os.path.exists(TEST_ACCOUNTS_FILE):
            os.remove(TEST_ACCOUNTS_FILE)
