#!/usr/bin/env python3
"""
API Endpoint Test Script
Tests all the Daily Post API endpoints to ensure they work correctly with the frontend.
"""

import requests
import pandas as pd
import os
import time
from io import BytesIO

# Backend URL
BASE_URL = "http://localhost:5000/api"

def create_test_files():
    """Create test files for API testing"""
    print("Creating test files...")
    
    # Create test accounts file
    accounts_data = {
        'Username': ['test_user_1', 'test_user_2', 'test_user_3'],
        'Password': ['test_pass_1', 'test_pass_2', 'test_pass_3']
    }
    df = pd.DataFrame(accounts_data)
    accounts_file = "test_accounts.xlsx"
    df.to_excel(accounts_file, index=False)
    
    # Create a simple test image (1x1 pixel PNG)
    import struct
    
    def create_test_png():
        # Minimal PNG file (1x1 transparent pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
        return png_data
    
    image_file = "test_image.png"
    with open(image_file, 'wb') as f:
        f.write(create_test_png())
    
    return accounts_file, image_file

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_validation_endpoint(accounts_file, image_file):
    """Test the file validation endpoint"""
    print("\n🔍 Testing validation endpoint...")
    try:
        with open(accounts_file, 'rb') as af, open(image_file, 'rb') as if_:
            files = {
                'accounts_file': (accounts_file, af, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                'media_file': (image_file, if_, 'image/png')
            }
            response = requests.post(f"{BASE_URL}/daily-post/validate", files=files)
            
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Validation passed: {data['accounts_count']} accounts, {data['media_type']} media")
            return True
        else:
            print(f"❌ Validation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def test_scripts_list_endpoint():
    """Test the scripts list endpoint"""
    print("\n🔍 Testing scripts list endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/scripts")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scripts list retrieved: {len(data)} active scripts")
            return True
        else:
            print(f"❌ Scripts list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Scripts list error: {e}")
        return False

def test_start_endpoint_validation():
    """Test the start endpoint with validation (but don't actually start)"""
    print("\n🔍 Testing start endpoint validation...")
    
    # Test with missing files
    try:
        response = requests.post(f"{BASE_URL}/daily-post/start", data={})
        if response.status_code == 400:
            data = response.json()
            if "required" in data.get("error", "").lower():
                print("✅ Start endpoint correctly validates missing files")
                return True
        print(f"❌ Start endpoint validation failed: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Start endpoint validation error: {e}")
        return False

def test_script_endpoints_with_fake_id():
    """Test script endpoints with a fake ID to check error handling"""
    print("\n🔍 Testing script endpoints error handling...")
    fake_id = "fake-script-id-12345"
    
    # Test status endpoint
    try:
        response = requests.get(f"{BASE_URL}/script/{fake_id}/status")
        if response.status_code == 404:
            print("✅ Status endpoint correctly handles non-existent script")
        else:
            print(f"❌ Status endpoint error handling failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False
    
    # Test logs endpoint
    try:
        response = requests.get(f"{BASE_URL}/script/{fake_id}/logs")
        if response.status_code == 200:  # Logs endpoint returns empty logs for non-existent scripts
            data = response.json()
            if data.get("logs") == []:
                print("✅ Logs endpoint correctly handles non-existent script")
            else:
                print(f"❌ Logs endpoint returned unexpected data: {data}")
                return False
        else:
            print(f"❌ Logs endpoint error handling failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Logs endpoint error: {e}")
        return False
    
    # Test stop endpoint
    try:
        response = requests.post(f"{BASE_URL}/script/{fake_id}/stop")
        if response.status_code == 404:
            print("✅ Stop endpoint correctly handles non-existent script")
        else:
            print(f"❌ Stop endpoint error handling failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stop endpoint error: {e}")
        return False
    
    return True

def cleanup_test_files(accounts_file, image_file):
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    try:
        if os.path.exists(accounts_file):
            os.remove(accounts_file)
        if os.path.exists(image_file):
            os.remove(image_file)
        print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    """Run all API endpoint tests"""
    print("🚀 Starting Daily Post API Endpoint Tests")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not running or not responding correctly")
            print("Please start the backend with: python app.py")
            return
    except Exception as e:
        print("❌ Cannot connect to backend")
        print("Please make sure the backend is running on http://localhost:5000")
        print("Start it with: python app.py")
        return
    
    print("✅ Backend is running and accessible")
    
    # Create test files
    accounts_file, image_file = create_test_files()
    
    try:
        # Run tests
        tests = [
            ("Health Check", test_health_endpoint),
            ("File Validation", lambda: test_validation_endpoint(accounts_file, image_file)),
            ("Scripts List", test_scripts_list_endpoint),
            ("Start Endpoint Validation", test_start_endpoint_validation),
            ("Script Endpoints Error Handling", test_script_endpoints_with_fake_id)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if test_func():
                passed += 1
            else:
                break  # Stop on first failure for safety
        
        print("\n" + "=" * 60)
        if passed == total:
            print(f"🎉 All {total} tests passed! The API endpoints are working correctly.")
            print("\nThe backend is ready to work with the React frontend!")
        else:
            print(f"❌ {passed}/{total} tests passed. Please check the errors above.")
    
    finally:
        # Always cleanup
        cleanup_test_files(accounts_file, image_file)

if __name__ == "__main__":
    main()
