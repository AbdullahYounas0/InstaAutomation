import requests
import json
import random

# Test with unique username
base_url = "http://127.0.0.1:5000"

print("Testing with unique username...")

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
        
        # Test adding account with unique username
        unique_id = random.randint(1000, 9999)
        test_account = {
            "username": f"test_user_{unique_id}",
            "password": "test_password123",
            "email": f"test{unique_id}@example.com"
        }
        
        print(f"Testing POST with unique username: {test_account['username']}")
        response = requests.post(f"{base_url}/api/instagram-accounts", 
                               json=test_account, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Account creation successful!")
            
            # Test getting all accounts
            print("\nTesting GET all accounts...")
            response = requests.get(f"{base_url}/api/instagram-accounts", headers=headers)
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Number of accounts: {len(data.get('accounts', []))}")
            
            # Test import functionality
            print("\nTesting CSV import...")
            try:
                with open('test_accounts.csv', 'rb') as f:
                    files = {'accounts_file': f}
                    auth_headers = {'Authorization': f'Bearer {token}'}
                    response = requests.post(f"{base_url}/api/instagram-accounts/import", 
                                           files=files, headers=auth_headers)
                    print(f"Import Status: {response.status_code}")
                    print(f"Import Response: {response.text}")
            except Exception as e:
                print(f"Import error: {e}")
        
except Exception as e:
    print(f"Test error: {e}")
