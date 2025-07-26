#!/usr/bin/env python3
"""
Test the improved stop functionality in Instagram warmup
"""

import requests
import json
import os
import time
import threading

BASE_URL = "http://localhost:5000"
TEST_ACCOUNTS_FILE = "test_accounts.csv"

def create_test_accounts_file():
    """Create a test accounts file"""
    with open(TEST_ACCOUNTS_FILE, 'w') as f:
        f.write("username,password\n")
        f.write("test_user1,test_pass1\n")
        f.write("test_user2,test_pass2\n")

def test_immediate_stop():
    """Test that stop button works immediately during script execution"""
    print("=== Testing Immediate Stop Functionality ===")
    
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
    
    # Step 2: Start warmup script
    print("\n2. Starting warmup script...")
    
    if not os.path.exists(TEST_ACCOUNTS_FILE):
        create_test_accounts_file()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        'warmup_duration_min': '5',  # 5 minutes - long enough to test stopping
        'warmup_duration_max': '10', 
        'scheduler_delay': '0',
        'max_concurrent': '1',
        'visual_mode': 'false',
        'feed_scroll': 'true',
        'watch_reels': 'false',  # Disable other activities for faster testing
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
        
        if response.status_code == 200:
            result = response.json()
            script_id = result.get('script_id')
            print(f"✅ Script started! Script ID: {script_id}")
        else:
            print(f"❌ Failed to start script: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Start script error: {e}")
        return False
    
    # Step 3: Wait a bit, then test immediate stop
    print(f"\n3. Waiting 3 seconds, then testing immediate stop...")
    time.sleep(3)
    
    stop_start_time = time.time()
    
    try:
        response = requests.post(f"{BASE_URL}/api/script/{script_id}/stop", 
                               headers=headers)
        
        if response.status_code == 200:
            stop_end_time = time.time()
            stop_duration = stop_end_time - stop_start_time
            print(f"✅ Stop request successful in {stop_duration:.2f} seconds")
            
            # Step 4: Check if script actually stopped quickly
            print(f"\n4. Checking script status after stop...")
            time.sleep(2)  # Wait a moment for the script to process the stop
            
            status_response = requests.get(f"{BASE_URL}/api/script/{script_id}/status", 
                                         headers=headers)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                script_status = status_data.get('status')
                print(f"Script status after stop: {script_status}")
                
                if script_status == "stopped":
                    print("✅ Script stopped immediately as expected!")
                    
                    # Get final logs
                    logs_response = requests.get(f"{BASE_URL}/api/script/{script_id}/logs", 
                                               headers=headers)
                    if logs_response.status_code == 200:
                        logs = logs_response.json().get('logs', [])
                        print(f"\nFinal logs (last 3):")
                        for log in logs[-3:]:
                            print(f"  {log}")
                    
                    return True
                else:
                    print(f"❌ Script status is '{script_status}', expected 'stopped'")
                    return False
            else:
                print(f"❌ Failed to get script status: {status_response.status_code}")
                return False
                
        else:
            print(f"❌ Stop request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Stop request error: {e}")
        return False

def test_error_handling():
    """Test that errors don't prevent immediate stopping"""
    print("\n\n=== Testing Error Handling with Stop ===")
    print("This test uses invalid accounts to trigger errors, then tests stopping")
    
    # Create file with invalid accounts
    invalid_accounts_file = "invalid_accounts.csv"
    with open(invalid_accounts_file, 'w') as f:
        f.write("username,password\n")
        f.write("invalid_user_123456,invalid_pass_123456\n")
    
    try:
        # Login
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        token = response.json().get('token')
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Start with invalid accounts
        data = {
            'warmup_duration_min': '2',
            'warmup_duration_max': '3',
            'scheduler_delay': '0',
            'max_concurrent': '1',
            'visual_mode': 'false',
            'feed_scroll': 'true',
            'watch_reels': 'false',
            'like_reels': 'false',
            'like_posts': 'false',
            'explore_page': 'false',
            'random_visits': 'false'
        }
        
        with open(invalid_accounts_file, 'rb') as f:
            files = {'accounts_file': f}
            response = requests.post(f"{BASE_URL}/api/warmup/start", 
                                   data=data, 
                                   files=files, 
                                   headers=headers)
        
        if response.status_code == 200:
            script_id = response.json().get('script_id')
            print(f"✅ Script started with invalid accounts: {script_id}")
            
            # Wait briefly then stop
            time.sleep(2)
            stop_response = requests.post(f"{BASE_URL}/api/script/{script_id}/stop", 
                                        headers=headers)
            
            if stop_response.status_code == 200:
                print("✅ Stop worked even with invalid accounts causing errors!")
                return True
            else:
                print(f"❌ Stop failed: {stop_response.status_code}")
                return False
        else:
            print(f"❌ Failed to start script with invalid accounts: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
    finally:
        if os.path.exists(invalid_accounts_file):
            os.remove(invalid_accounts_file)

if __name__ == "__main__":
    print("Enhanced Stop Functionality Test")
    print("===============================")
    
    try:
        # Check if backend is running
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print("❌ Backend is not running! Start the Flask server first.")
            exit(1)
        
        print("✅ Backend is running")
        
        # Run tests
        test1_passed = test_immediate_stop()
        test2_passed = test_error_handling()
        
        print("\n" + "="*50)
        if test1_passed and test2_passed:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Stop button works immediately")
            print("✅ Error handling doesn't prevent stopping")
            print("✅ Enhanced stop functionality is working correctly")
        else:
            print("❌ Some tests failed:")
            print(f"   Immediate Stop: {'✅' if test1_passed else '❌'}")
            print(f"   Error Handling: {'✅' if test2_passed else '❌'}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend connection failed! Make sure the Flask server is running.")
        exit(1)
    
    finally:
        # Cleanup
        if os.path.exists(TEST_ACCOUNTS_FILE):
            os.remove(TEST_ACCOUNTS_FILE)
