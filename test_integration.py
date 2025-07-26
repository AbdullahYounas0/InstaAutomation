import requests
import json

def test_frontend_backend_integration():
    """Test the integration between frontend and backend"""
    
    print("🧪 Testing Frontend-Backend Integration...")
    
    # Test 1: File upload endpoint
    print("\n1️⃣ Testing file validation...")
    try:
        with open('test_accounts.csv', 'rb') as f:
            files = {'accounts_file': ('test_accounts.csv', f, 'text/csv')}
            response = requests.post('http://localhost:5000/api/warmup/validate', files=files)
            result = response.json()
            print(f"✅ Validation: {result}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    # Test 2: Start warmup with different configurations
    configs = [
        {
            'name': 'Basic Configuration',
            'data': {
                'warmup_duration': '2',
                'max_concurrent': '1',
                'visual_mode': 'false',
                'feed_scroll': 'true',
                'watch_reels': 'false',
                'like_reels': 'false',
                'like_posts': 'false',
                'explore_page': 'false',
                'random_visits': 'false',
                'activity_delay_min': '1',
                'activity_delay_max': '3',
                'scroll_attempts_min': '1',
                'scroll_attempts_max': '3'
            }
        },
        {
            'name': 'Full Activity Configuration',
            'data': {
                'warmup_duration': '1',
                'max_concurrent': '1',
                'visual_mode': 'true',
                'feed_scroll': 'true',
                'watch_reels': 'true',
                'like_reels': 'true',
                'like_posts': 'true',
                'explore_page': 'true',
                'random_visits': 'true',
                'activity_delay_min': '2',
                'activity_delay_max': '5',
                'scroll_attempts_min': '2',
                'scroll_attempts_max': '5'
            }
        }
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n{i+1}️⃣ Testing {config['name']}...")
        try:
            with open('test_accounts.csv', 'rb') as f:
                files = {'accounts_file': ('test_accounts.csv', f, 'text/csv')}
                response = requests.post('http://localhost:5000/api/warmup/start', 
                                       files=files, data=config['data'])
                
                if response.status_code == 200:
                    result = response.json()
                    script_id = result['script_id']
                    print(f"✅ Started: {script_id}")
                    
                    # Check status
                    status_response = requests.get(f'http://localhost:5000/api/script/{script_id}/status')
                    status = status_response.json()
                    print(f"   Status: {status['status']}")
                    print(f"   Config: Visual={status['config']['visual_mode']}, Duration={status['config']['warmup_duration']}min")
                    
                    # Stop the script
                    stop_response = requests.post(f'http://localhost:5000/api/script/{script_id}/stop')
                    print(f"   Stopped: {stop_response.json()['status']}")
                    
                else:
                    print(f"❌ Failed: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 3: Error handling
    print(f"\n3️⃣ Testing Error Handling...")
    
    # Test with missing file
    try:
        response = requests.post('http://localhost:5000/api/warmup/start', data={'warmup_duration': '1'})
        print(f"Missing file test: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Missing file test failed: {e}")
    
    # Test with invalid duration
    try:
        with open('test_accounts.csv', 'rb') as f:
            files = {'accounts_file': ('test_accounts.csv', f, 'text/csv')}
            data = {'warmup_duration': 'invalid', 'max_concurrent': '1'}
            response = requests.post('http://localhost:5000/api/warmup/start', files=files, data=data)
            print(f"Invalid duration test: {response.status_code}")
    except Exception as e:
        print(f"Invalid duration handled: {e}")

def test_concurrent_scripts():
    """Test running multiple scripts concurrently"""
    print("\n4️⃣ Testing Concurrent Scripts...")
    
    script_ids = []
    
    try:
        # Start multiple scripts
        for i in range(2):
            with open('test_accounts.csv', 'rb') as f:
                files = {'accounts_file': ('test_accounts.csv', f, 'text/csv')}
                data = {
                    'warmup_duration': '1',
                    'max_concurrent': '1',
                    'visual_mode': 'false',
                    'feed_scroll': 'true',
                    'activity_delay_min': '1',
                    'activity_delay_max': '2'
                }
                response = requests.post('http://localhost:5000/api/warmup/start', files=files, data=data)
                
                if response.status_code == 200:
                    script_id = response.json()['script_id']
                    script_ids.append(script_id)
                    print(f"   Started script {i+1}: {script_id}")
                else:
                    print(f"   Failed to start script {i+1}")
        
        # Check all scripts are running
        print(f"   Active scripts: {len(script_ids)}")
        
        # Stop all scripts
        for script_id in script_ids:
            requests.post(f'http://localhost:5000/api/script/{script_id}/stop')
            print(f"   Stopped: {script_id}")
            
    except Exception as e:
        print(f"❌ Concurrent test failed: {e}")

if __name__ == "__main__":
    test_frontend_backend_integration()
    test_concurrent_scripts()
    print("\n🎉 Integration testing completed!")
