import requests
import json

# Test the FastAPI backend
BASE_URL = "http://localhost:5000/api"

print("Testing FastAPI Backend...")
print("=" * 50)

# Test health endpoint
print("1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ Health check passed")
except Exception as e:
    print(f"   ❌ Health check failed: {e}")

print()

# Test CORS endpoint
print("2. Testing CORS endpoint...")
try:
    response = requests.get(f"{BASE_URL}/cors-test")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Status: {data['status']}")
    print(f"   Server Info: {data['server_info']}")
    print("   ✅ CORS test passed")
except Exception as e:
    print(f"   ❌ CORS test failed: {e}")

print()

# Test login endpoint
print("3. Testing login endpoint...")
try:
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        print(f"   Success: {data['success']}")
        print(f"   User: {data['user']['name']} ({data['user']['role']})")
        print(f"   Token: {data['token'][:50]}...")
        print("   ✅ Login test passed")
        
        # Store token for authenticated requests
        token = data['token']
        
        # Test authenticated endpoint
        print()
        print("4. Testing authenticated endpoint...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/scripts", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            scripts = response.json()
            print(f"   Scripts count: {len(scripts)}")
            print("   ✅ Authenticated request passed")
        else:
            print(f"   ❌ Authenticated request failed: {response.text}")
            
    else:
        print(f"   ❌ Login failed: {data.get('message', 'Unknown error')}")
        
except Exception as e:
    print(f"   ❌ Login test failed: {e}")

print()
print("=" * 50)
print("FastAPI Backend Test Complete!")
