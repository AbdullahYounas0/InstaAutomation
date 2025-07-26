import requests
import json
import traceback

# Detailed test for debugging
base_url = "http://127.0.0.1:5000"

print("Testing Instagram accounts with detailed error logging...")

# Login first
login_data = {
    "username": "admin",
    "password": "admin123"
}

try:
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get('token')
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # Test adding account with very simple data
        test_account = {
            "username": "simple_test",
            "password": "simple_pass"
        }
        
        print("Testing POST with minimal data...")
        response = requests.post(f"{base_url}/api/instagram-accounts", 
                               json=test_account, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")
        
        # Also test if the account exists check works
        print("\nTesting duplicate username...")
        response2 = requests.post(f"{base_url}/api/instagram-accounts", 
                                json=test_account, headers=headers)
        print(f"Status: {response2.status_code}")
        print(f"Response: {response2.text}")
        
except Exception as e:
    print(f"Test error: {e}")
    traceback.print_exc()
