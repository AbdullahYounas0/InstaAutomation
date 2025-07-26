import requests
import time

# Test the warmup API endpoint
def test_warmup_api():
    url = "http://localhost:5000/api/warmup/start"
    
    # Prepare test data
    files = {
        'accounts_file': ('test_accounts.csv', open('test_accounts.csv', 'rb'), 'text/csv')
    }
    
    data = {
        'warmup_duration': '1',  # 1 minute for quick testing
        'max_concurrent': '1',
        'visual_mode': 'false',
        'feed_scroll': 'true',
        'watch_reels': 'false',
        'like_reels': 'false', 
        'like_posts': 'false',
        'explore_page': 'false',
        'random_visits': 'false',
        'activity_delay_min': '1',
        'activity_delay_max': '2',
        'scroll_attempts_min': '1',
        'scroll_attempts_max': '2'
    }
    
    try:
        print("🚀 Testing warmup API endpoint...")
        response = requests.post(url, files=files, data=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            script_id = response.json().get('script_id')
            print(f"✅ Script started successfully! Script ID: {script_id}")
            
            # Test status endpoint
            test_status_endpoint(script_id)
            
            # Test logs endpoint  
            test_logs_endpoint(script_id)
            
            # Test stop endpoint
            time.sleep(5)  # Wait a bit
            test_stop_endpoint(script_id)
            
        else:
            print(f"❌ Failed to start script: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    finally:
        files['accounts_file'][1].close()

def test_status_endpoint(script_id):
    try:
        print(f"\n📊 Testing status endpoint for script {script_id}...")
        response = requests.get(f"http://localhost:5000/api/script/{script_id}/status")
        print(f"Status Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error testing status endpoint: {e}")

def test_logs_endpoint(script_id):
    try:
        print(f"\n📝 Testing logs endpoint for script {script_id}...")
        response = requests.get(f"http://localhost:5000/api/script/{script_id}/logs")
        logs = response.json().get('logs', [])
        print(f"Logs count: {len(logs)}")
        if logs:
            print("Recent logs:")
            for log in logs[-3:]:  # Show last 3 logs
                print(f"  - {log}")
    except Exception as e:
        print(f"❌ Error testing logs endpoint: {e}")

def test_stop_endpoint(script_id):
    try:
        print(f"\n🛑 Testing stop endpoint for script {script_id}...")
        response = requests.post(f"http://localhost:5000/api/script/{script_id}/stop")
        print(f"Stop Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error testing stop endpoint: {e}")

def test_validation_endpoint():
    try:
        print(f"\n✅ Testing validation endpoint...")
        files = {
            'accounts_file': ('test_accounts.csv', open('test_accounts.csv', 'rb'), 'text/csv')
        }
        response = requests.post("http://localhost:5000/api/warmup/validate", files=files)
        print(f"Validation Response: {response.json()}")
        files['accounts_file'][1].close()
    except Exception as e:
        print(f"❌ Error testing validation endpoint: {e}")

if __name__ == "__main__":
    print("🧪 Starting comprehensive warmup API tests...")
    test_validation_endpoint()
    test_warmup_api()
    print("\n✨ Testing completed!")
