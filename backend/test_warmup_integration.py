import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_ACCOUNTS_FILE = "test_accounts.csv"

def create_test_accounts_file():
    """Create a test accounts file for testing"""
    with open(TEST_ACCOUNTS_FILE, 'w') as f:
        f.write("Username,Password\n")
        f.write("test_user1,test_pass1\n")
        f.write("test_user2,test_pass2\n")
    print(f"Created test accounts file: {TEST_ACCOUNTS_FILE}")

def test_warmup_validation():
    """Test the warmup file validation endpoint"""
    print("\n=== Testing Warmup File Validation ===")
    
    if not os.path.exists(TEST_ACCOUNTS_FILE):
        create_test_accounts_file()
    
    with open(TEST_ACCOUNTS_FILE, 'rb') as f:
        files = {'accounts_file': f}
        response = requests.post(f"{BASE_URL}/api/warmup/validate", files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_warmup_start():
    """Test starting the warmup script"""
    print("\n=== Testing Warmup Script Start ===")
    
    if not os.path.exists(TEST_ACCOUNTS_FILE):
        create_test_accounts_file()
    
    # Prepare form data
    data = {
        'warmup_duration': '10',  # 10 minutes for testing
        'max_concurrent': '2',
        'visual_mode': 'false',
        'feed_scroll': 'true',
        'watch_reels': 'true',
        'like_reels': 'false',  # Disable for testing
        'like_posts': 'false',  # Disable for testing
        'explore_page': 'true',
        'random_visits': 'false',
        'activity_delay_min': '1',
        'activity_delay_max': '3',
        'scroll_attempts_min': '2',
        'scroll_attempts_max': '4'
    }
    
    with open(TEST_ACCOUNTS_FILE, 'rb') as f:
        files = {'accounts_file': f}
        response = requests.post(f"{BASE_URL}/api/warmup/start", data=data, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        script_id = response.json().get('script_id')
        print(f"Script ID: {script_id}")
        return script_id
    return None

def test_script_status(script_id):
    """Test getting script status"""
    print(f"\n=== Testing Script Status ===")
    
    response = requests.get(f"{BASE_URL}/api/script/{script_id}/status")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_script_logs(script_id):
    """Test getting script logs"""
    print(f"\n=== Testing Script Logs ===")
    
    response = requests.get(f"{BASE_URL}/api/script/{script_id}/logs")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        logs = response.json().get('logs', [])
        print(f"Number of logs: {len(logs)}")
        if logs:
            print("Recent logs:")
            for log in logs[-5:]:  # Show last 5 logs
                print(f"  {log}")
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_script_stop(script_id):
    """Test stopping a script"""
    print(f"\n=== Testing Script Stop ===")
    
    response = requests.post(f"{BASE_URL}/api/script/{script_id}/stop")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Could not connect to the Flask server. Make sure it's running on localhost:5000")
        return False

def main():
    """Run all tests"""
    print("Instagram Warmup Integration Tests")
    print("=" * 40)
    
    # Test health check first
    if not test_health_check():
        print("❌ Health check failed. Ensure the Flask server is running.")
        return
    
    # Test validation
    if test_warmup_validation():
        print("✅ Warmup validation test passed")
    else:
        print("❌ Warmup validation test failed")
    
    # Test starting script
    script_id = test_warmup_start()
    if script_id:
        print("✅ Warmup start test passed")
        
        # Wait a moment for the script to initialize
        import time
        time.sleep(2)
        
        # Test status
        if test_script_status(script_id):
            print("✅ Script status test passed")
        else:
            print("❌ Script status test failed")
        
        # Test logs
        if test_script_logs(script_id):
            print("✅ Script logs test passed")
        else:
            print("❌ Script logs test failed")
        
        # Test stop
        if test_script_stop(script_id):
            print("✅ Script stop test passed")
        else:
            print("❌ Script stop test failed")
    else:
        print("❌ Warmup start test failed")
    
    # Clean up test file
    if os.path.exists(TEST_ACCOUNTS_FILE):
        os.remove(TEST_ACCOUNTS_FILE)
        print(f"Cleaned up test file: {TEST_ACCOUNTS_FILE}")
    
    print("\n" + "=" * 40)
    print("Tests completed!")

if __name__ == "__main__":
    main()
