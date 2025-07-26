import requests
import json

# Test the Instagram accounts endpoints
base_url = "http://127.0.0.1:5000"

# Test data
test_account = {
    "username": "test_user123",
    "password": "test_password123",
    "email": "test@example.com"
}

print("Testing Instagram accounts endpoints...")

# Test 1: GET all accounts (should work without auth for testing)
try:
    response = requests.get(f"{base_url}/api/instagram-accounts")
    print(f"GET /api/instagram-accounts: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"GET request error: {e}")

print("\n" + "="*50 + "\n")

# Test 2: POST new account (will fail without auth but should show the exact error)
try:
    response = requests.post(f"{base_url}/api/instagram-accounts", 
                           json=test_account,
                           headers={'Content-Type': 'application/json'})
    print(f"POST /api/instagram-accounts: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"POST request error: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Test import endpoint with actual file
try:
    with open('test_accounts.csv', 'rb') as f:
        files = {'accounts_file': f}
        response = requests.post(f"{base_url}/api/instagram-accounts/import", files=files)
        print(f"POST /api/instagram-accounts/import: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Import request error: {e}")
