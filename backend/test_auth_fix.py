#!/usr/bin/env python3
"""
Test script to verify the browser close detection authentication fix
"""

import requests
import json

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

def test_stop_endpoint_with_header(token, script_id="test-script-id"):
    """Test stop endpoint with Authorization header (normal case)"""
    print("Testing stop endpoint with Authorization header...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "reason": "Test stop with header"
    }
    
    response = requests.post(f"{BASE_URL}/api/script/{script_id}/stop", 
                           headers=headers, json=data)
    
    print(f"Header test - Status: {response.status_code}")
    if response.status_code != 404:  # 404 is expected for non-existent script
        print(f"Response: {response.text}")
    else:
        print("✓ Authentication passed (got expected 404 for non-existent script)")

def test_stop_endpoint_with_form_data(token, script_id="test-script-id"):
    """Test stop endpoint with form data (sendBeacon case)"""
    print("\nTesting stop endpoint with form data (sendBeacon simulation)...")
    
    form_data = {
        "token": token,
        "reason": "Browser closed by User"
    }
    
    response = requests.post(f"{BASE_URL}/api/script/{script_id}/stop", data=form_data)
    
    print(f"Form data test - Status: {response.status_code}")
    if response.status_code != 404:  # 404 is expected for non-existent script
        print(f"Response: {response.text}")
    else:
        print("✓ Authentication passed (got expected 404 for non-existent script)")

def main():
    print("=== Browser Close Detection Authentication Test ===")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token")
        return
    
    print(f"✓ Got authentication token: {token[:20]}...")
    
    # Test both authentication methods
    test_stop_endpoint_with_header(token)
    test_stop_endpoint_with_form_data(token)
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()
