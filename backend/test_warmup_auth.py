#!/usr/bin/env python3
"""
Test warmup endpoint with proper authentication
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
        f.write("test_user2,test_pass2\n")

def test_authentication_and_warmup():
    """Test authentication and then warmup endpoint"""
    print("=== Testing Authentication + Warmup Flow ===")
    
    # Step 1: Login to get token
    print("\n1. Authenticating...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return False
        
        auth_response = response.json()
        if not auth_response.get('success'):
            print(f"Login failed: {auth_response.get('message')}")
            return False
        
        token = auth_response.get('token')
        print(f"✅ Authentication successful!")
        print(f"Token: {token[:50]}..." if token else "No token received")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the Flask server is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Test warmup endpoint with token
    print("\n2. Testing warmup endpoint with authentication...")
    
    if not os.path.exists(TEST_ACCOUNTS_FILE):
        create_test_accounts_file()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        'warmup_duration_min': '10',
        'warmup_duration_max': '15',
        'scheduler_delay': '0',
        'max_concurrent': '2',
        'visual_mode': 'false',
        'feed_scroll': 'true',
        'watch_reels': 'true',
        'like_reels': 'false',
        'like_posts': 'false',
        'explore_page': 'true',
        'random_visits': 'false',
        'activity_delay_min': '1',
        'activity_delay_max': '3',
        'scroll_attempts_min': '2',
        'scroll_attempts_max': '4'
    }
    
    try:
        with open(TEST_ACCOUNTS_FILE, 'rb') as f:
            files = {'accounts_file': f}
            response = requests.post(f"{BASE_URL}/api/warmup/start", 
                                   data=data, 
                                   files=files, 
                                   headers=headers)
        
        print(f"Warmup Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Warmup endpoint working with authentication!")
            script_id = response.json().get('script_id')
            print(f"Script ID: {script_id}")
            return script_id
        else:
            print(f"❌ Warmup failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Warmup request error: {e}")
        return False

def test_warmup_without_auth():
    """Test warmup endpoint without authentication (should fail)"""
    print("\n=== Testing Warmup Without Auth (Should Fail) ===")
    
    if not os.path.exists(TEST_ACCOUNTS_FILE):
        create_test_accounts_file()
    
    data = {
        'warmup_duration_min': '10',
        'warmup_duration_max': '15',
        'scheduler_delay': '0',
        'max_concurrent': '2',
        'visual_mode': 'false'
    }
    
    try:
        with open(TEST_ACCOUNTS_FILE, 'rb') as f:
            files = {'accounts_file': f}
            response = requests.post(f"{BASE_URL}/api/warmup/start", 
                                   data=data, 
                                   files=files)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected unauthorized request!")
            return True
        else:
            print("❌ Should have returned 401 Unauthorized")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

if __name__ == "__main__":
    print("Instagram Warmup Authentication Test")
    print("====================================")
    
    # Test without auth first (should fail)
    test_warmup_without_auth()
    
    # Test with proper auth
    test_authentication_and_warmup()
    
    # Cleanup
    if os.path.exists(TEST_ACCOUNTS_FILE):
        os.remove(TEST_ACCOUNTS_FILE)
