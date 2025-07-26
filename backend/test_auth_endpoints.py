import requests
import json

# Test the Instagram accounts endpoints with authentication
base_url = "http://127.0.0.1:5000"

print("Testing with authentication...")

# First, login as admin to get token
login_data = {
    "username": "admin",
    "password": "admin123"
}

try:
    # Login
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json().get('token')
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        print("Testing authenticated endpoints...")
        
        # Test 1: GET all accounts
        response = requests.get(f"{base_url}/api/instagram-accounts", headers=headers)
        print(f"GET /api/instagram-accounts: {response.status_code}")
        print(f"Response: {response.text}")
        
        print("\n" + "="*30 + "\n")
        
        # Test 2: POST new account
        test_account = {
            "username": "test_user123",
            "password": "test_password123",
            "email": "test@example.com"
        }
        
        response = requests.post(f"{base_url}/api/instagram-accounts", 
                               json=test_account, headers=headers)
        print(f"POST /api/instagram-accounts: {response.status_code}")
        print(f"Response: {response.text}")
        
        print("\n" + "="*30 + "\n")
        
        # Test 3: Import from CSV
        try:
            with open('test_accounts.csv', 'rb') as f:
                files = {'accounts_file': f}
                auth_headers = {'Authorization': f'Bearer {token}'}
                response = requests.post(f"{base_url}/api/instagram-accounts/import", 
                                       files=files, headers=auth_headers)
                print(f"POST /api/instagram-accounts/import: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Import error: {e}")
            
    else:
        print(f"Login failed: {response.text}")
        
except Exception as e:
    print(f"Test error: {e}")
