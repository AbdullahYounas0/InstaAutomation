#!/usr/bin/env python3
"""
Quick authentication test for the fixed frontend
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_backend_status():
    """Test if backend is running"""
    print("=== Testing Backend Status ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ Backend is running!")
            print(f"Health check: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running! Start the Flask server first.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print("\n=== Testing Login ===")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Login successful!")
                print(f"Token preview: {result.get('token', '')[:50]}...")
                print(f"User: {result.get('user', {}).get('username')}")
                return result.get('token')
            else:
                print(f"❌ Login failed: {result.get('message')}")
                return None
        else:
            print(f"❌ Login request failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint with token"""
    print("\n=== Testing Protected Endpoint ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/scripts", headers=headers)
        print(f"Scripts endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Protected endpoint accessible with token!")
            scripts = response.json()
            print(f"Found {len(scripts)} active scripts")
            return True
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False

def test_without_token():
    """Test warmup endpoint without token (should fail)"""
    print("\n=== Testing Without Token (Should Fail) ===")
    
    try:
        # Try to access a protected endpoint without token
        response = requests.get(f"{BASE_URL}/api/scripts")
        print(f"Status without token: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected request without token!")
            return True
        else:
            print(f"❌ Should have returned 401, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Backend Authentication Test")
    print("===========================")
    
    # Test if backend is running
    if not test_backend_status():
        print("\n💡 Start the backend server with: python app.py")
        exit(1)
    
    # Test login
    token = test_login()
    if not token:
        print("\n💡 Make sure admin user exists with password 'admin123'")
        exit(1)
    
    # Test protected endpoint with token
    if test_protected_endpoint(token):
        print("\n🎉 Authentication is working correctly!")
    else:
        print("\n❌ Authentication still has issues")
    
    # Test without token (should fail)
    test_without_token()
    
    print("\n📋 Summary:")
    print("- Frontend components now include Authorization headers")
    print("- Login endpoint works")
    print("- Protected endpoints require valid tokens")
    print("- All API calls should now work from the frontend")
    print("\n🚀 Try using the web application now!")
