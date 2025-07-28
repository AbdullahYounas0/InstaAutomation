#!/usr/bin/env python3
"""
CORS Test Script
Tests the CORS implementation of the Flask backend
"""

import requests
import json
import sys

def test_cors():
    """Test CORS functionality"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing CORS Implementation...")
    print("=" * 50)
    
    # Test 1: Basic CORS test endpoint
    print("\n1. Testing CORS test endpoint...")
    try:
        response = requests.get(f"{base_url}/api/cors-test", 
                              headers={'Origin': 'http://localhost:3000'})
        if response.status_code == 200:
            data = response.json()
            print("✅ CORS test endpoint working")
            print(f"   Status: {data['status']}")
            print(f"   Method: {data['method']}")
            print(f"   Origin: {data['origin']}")
        else:
            print(f"❌ CORS test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ CORS test error: {e}")
    
    # Test 2: Preflight request
    print("\n2. Testing preflight request...")
    try:
        response = requests.options(f"{base_url}/api/cors-test",
                                  headers={
                                      'Origin': 'http://localhost:3000',
                                      'Access-Control-Request-Method': 'POST',
                                      'Access-Control-Request-Headers': 'Content-Type,Authorization'
                                  })
        if response.status_code == 200:
            print("✅ Preflight request successful")
            print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
            print(f"   Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'Not set')}")
        else:
            print(f"❌ Preflight failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Preflight error: {e}")
    
    # Test 3: Health check with CORS
    print("\n3. Testing health check with CORS...")
    try:
        response = requests.get(f"{base_url}/api/health",
                              headers={'Origin': 'http://localhost:3000'})
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check with CORS working")
            print(f"   Status: {data['status']}")
            print(f"   CORS Origin Header: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 4: POST request with CORS
    print("\n4. Testing POST request with CORS...")
    try:
        response = requests.post(f"{base_url}/api/cors-test",
                               headers={
                                   'Origin': 'http://localhost:3000',
                                   'Content-Type': 'application/json'
                               },
                               json={'test': 'data'})
        if response.status_code == 200:
            data = response.json()
            print("✅ POST request with CORS working")
            print(f"   Status: {data['status']}")
            print(f"   Method: {data['method']}")
        else:
            print(f"❌ POST request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ POST request error: {e}")
    
    # Test 5: Invalid origin
    print("\n5. Testing invalid origin...")
    try:
        response = requests.get(f"{base_url}/api/cors-test",
                              headers={'Origin': 'https://malicious-site.com'})
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        if cors_origin and cors_origin != 'https://malicious-site.com':
            print("✅ Invalid origin properly rejected")
            print(f"   CORS Origin Header: {cors_origin}")
        elif not cors_origin:
            print("✅ Invalid origin properly rejected (no CORS header)")
        else:
            print("⚠️  WARNING: Invalid origin was allowed!")
    except Exception as e:
        print(f"❌ Invalid origin test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 CORS testing completed!")
    print("\nTo run this test:")
    print("1. Start your Flask backend: python app.py")
    print("2. Run this test: python test_cors.py")

if __name__ == "__main__":
    test_cors()
