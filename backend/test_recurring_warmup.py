#!/usr/bin/env python3
"""
Test script to demonstrate the new recurring warmup functionality
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_recurring_warmup(token):
    """Test the recurring warmup functionality"""
    print("=== Testing Recurring Warmup Functionality ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # First, get available accounts
    accounts_response = requests.get(f"{BASE_URL}/api/instagram-accounts/active", headers=headers)
    if accounts_response.status_code != 200:
        print("No accounts available for testing")
        return
    
    accounts = accounts_response.json().get("accounts", [])
    if not accounts:
        print("No Instagram accounts found for testing")
        return
    
    # Use first account for testing
    test_account_id = accounts[0]["id"]
    print(f"Using account: {accounts[0]['username']}")
    
    # Test data for recurring warmup (short durations for testing)
    form_data = {
        "account_ids": json.dumps([test_account_id]),
        "warmup_duration_min": "1",  # 1 minute for quick testing
        "warmup_duration_max": "2",  # 2 minutes for quick testing
        "scheduler_delay": "1",      # 1 hour recurring delay (but we'll stop it quickly)
        "visual_mode": "false",
        "feed_scroll": "true",
        "watch_reels": "false",
        "like_reels": "false",
        "like_posts": "false",
        "explore_page": "false",
        "random_visits": "false",
        "activity_delay_min": "1",
        "activity_delay_max": "2",
        "scroll_attempts_min": "1",
        "scroll_attempts_max": "2"
    }
    
    # Start recurring warmup
    print("\n🚀 Starting recurring warmup test...")
    response = requests.post(f"{BASE_URL}/api/warmup/start", data=form_data, headers=headers)
    
    if response.status_code == 200:
        script_id = response.json()["script_id"]
        print(f"✅ Recurring warmup started with script_id: {script_id}")
        
        # Monitor for a short time
        print("\n📊 Monitoring script status...")
        for i in range(10):  # Monitor for ~10 seconds
            status_response = requests.get(f"{BASE_URL}/api/script/{script_id}/status", headers=headers)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Status: {status_data.get('status', 'unknown')}")
                
                # Get recent logs
                logs_response = requests.get(f"{BASE_URL}/api/script/{script_id}/logs", headers=headers)
                if logs_response.status_code == 200:
                    logs = logs_response.json().get("logs", [])
                    if logs:
                        print(f"Latest log: {logs[-1]}")
            
            time.sleep(1)
        
        # Stop the script
        print(f"\n⏹️ Stopping script {script_id}...")
        stop_response = requests.post(f"{BASE_URL}/api/script/{script_id}/stop", headers=headers)
        if stop_response.status_code == 200:
            print("✅ Script stopped successfully")
        else:
            print(f"❌ Failed to stop script: {stop_response.text}")
            
    else:
        print(f"❌ Failed to start warmup: {response.status_code} - {response.text}")

def test_single_warmup(token):
    """Test the single (non-recurring) warmup functionality"""
    print("\n=== Testing Single Warmup Functionality ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Get available accounts
    accounts_response = requests.get(f"{BASE_URL}/api/instagram-accounts/active", headers=headers)
    accounts = accounts_response.json().get("accounts", [])
    
    if not accounts:
        print("No Instagram accounts found for testing")
        return
    
    test_account_id = accounts[0]["id"]
    
    # Test data for single warmup
    form_data = {
        "account_ids": json.dumps([test_account_id]),
        "warmup_duration_min": "1",  # 1 minute for quick testing
        "warmup_duration_max": "1",  # 1 minute for quick testing
        "scheduler_delay": "0",      # 0 = single run mode
        "visual_mode": "false",
        "feed_scroll": "true",
        "watch_reels": "false",
        "like_reels": "false",
        "like_posts": "false",
        "explore_page": "false",
        "random_visits": "false",
        "activity_delay_min": "1",
        "activity_delay_max": "2",
        "scroll_attempts_min": "1",
        "scroll_attempts_max": "2"
    }
    
    # Start single warmup
    print("🎯 Starting single warmup test...")
    response = requests.post(f"{BASE_URL}/api/warmup/start", data=form_data, headers=headers)
    
    if response.status_code == 200:
        script_id = response.json()["script_id"]
        print(f"✅ Single warmup started with script_id: {script_id}")
        
        # Monitor until completion
        print("📊 Monitoring until completion...")
        while True:
            status_response = requests.get(f"{BASE_URL}/api/script/{script_id}/status", headers=headers)
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status', 'unknown')
                print(f"Status: {status}")
                
                if status in ['completed', 'error', 'stopped']:
                    print(f"✅ Single warmup finished with status: {status}")
                    break
            
            time.sleep(2)
    else:
        print(f"❌ Failed to start single warmup: {response.status_code} - {response.text}")

def main():
    print("=== Recurring Warmup Functionality Test ===")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to authenticate")
        return
    
    print(f"✅ Authenticated successfully")
    
    # Test single mode first
    test_single_warmup(token)
    
    # Wait a bit
    print("\n⏳ Waiting 5 seconds between tests...")
    time.sleep(5)
    
    # Test recurring mode
    test_recurring_warmup(token)
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()
