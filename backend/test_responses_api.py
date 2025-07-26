#!/usr/bin/env python3
"""
Test script to verify the simplified responses API endpoint
"""

import requests
import json

def test_simplified_responses_api():
    """Test the /api/script/<script_id>/responses endpoint with simplified data"""
    
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        print("Testing Simplified DM Responses API")
        print("=" * 50)
        
        # Login to get token
        print("1. Logging in...")
        login_response = requests.post(login_url, json=login_data)
        
        if login_response.status_code == 200:
            token = login_response.json().get('token')
            print(f"   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return
        
        # Test the responses endpoint
        print("\n2. Testing simplified responses endpoint...")
        script_id = "test_script_123"
        responses_url = f"http://localhost:5000/api/script/{script_id}/responses"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(responses_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API call successful!")
            print(f"   📊 Total responses: {data.get('total_responses', 0)}")
            print(f"   👥 Accounts with responses: {data.get('accounts_with_responses', 0)}")
            
            if data.get('responses'):
                print(f"\n3. Sample responses (simplified format):")
                for i, resp in enumerate(data['responses'][:3], 1):  # Show first 3
                    print(f"   {i}. Bot: {resp['account']}")
                    print(f"      Responder: @{resp['responder']}")
                    print(f"      Message: {resp['message'][:80]}...")
                    print(f"      Time: {resp['timestamp']}")
                    print()
            
            print(f"✅ Simplified API endpoint working correctly!")
            print(f"📝 Data format: Bot Account | Responder | Message | Timestamp")
            
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_simplified_responses_api()
