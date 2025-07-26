import requests
import time
import threading

def monitor_logs(script_id, duration=30):
    """Monitor logs for a script for specified duration"""
    print(f"📊 Monitoring logs for script {script_id} for {duration} seconds...")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        try:
            response = requests.get(f'http://localhost:5000/api/script/{script_id}/logs')
            if response.status_code == 200:
                logs = response.json().get('logs', [])
                if logs:
                    print(f"   Total logs: {len(logs)}")
                    # Show only new logs (last 2)
                    for log in logs[-2:]:
                        if any(keyword in log.lower() for keyword in ['error', 'failed', 'exception', 'started', 'completed']):
                            print(f"   📝 {log}")
            
            # Check status
            status_response = requests.get(f'http://localhost:5000/api/script/{script_id}/status')
            if status_response.status_code == 200:
                status = status_response.json().get('status', 'unknown')
                if status in ['completed', 'failed', 'stopped']:
                    print(f"   Script ended with status: {status}")
                    break
                    
        except Exception as e:
            print(f"   Error monitoring: {e}")
            
        time.sleep(5)

def test_visual_mode():
    """Test visual mode functionality"""
    print("🎯 Testing Visual Mode Functionality...")
    
    try:
        with open('test_accounts.csv', 'rb') as f:
            files = {'accounts_file': ('test_accounts.csv', f, 'text/csv')}
            data = {
                'warmup_duration': '2',  # 2 minutes
                'max_concurrent': '1',
                'visual_mode': 'true',  # Enable visual mode
                'feed_scroll': 'true',
                'watch_reels': 'false',
                'like_reels': 'false',
                'like_posts': 'false',
                'explore_page': 'false',
                'random_visits': 'false',
                'activity_delay_min': '2',
                'activity_delay_max': '4',
                'scroll_attempts_min': '2',
                'scroll_attempts_max': '4'
            }
            
            response = requests.post('http://localhost:5000/api/warmup/start', files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                script_id = result['script_id']
                print(f"✅ Visual mode script started: {script_id}")
                
                # Monitor in a separate thread
                monitor_thread = threading.Thread(target=monitor_logs, args=(script_id, 60))
                monitor_thread.start()
                
                # Let it run for a bit
                print("⏳ Letting script run to test visual mode...")
                time.sleep(20)
                
                # Stop the script
                stop_response = requests.post(f'http://localhost:5000/api/script/{script_id}/stop')
                print(f"🛑 Script stopped: {stop_response.json()}")
                
                monitor_thread.join(timeout=10)
                
            else:
                print(f"❌ Failed to start visual mode script: {response.text}")
                
    except Exception as e:
        print(f"❌ Visual mode test failed: {e}")

def test_activity_variations():
    """Test different activity combinations"""
    print("\n🎪 Testing Activity Variations...")
    
    activity_sets = [
        {
            'name': 'Feed Only',
            'activities': {'feed_scroll': 'true', 'watch_reels': 'false', 'like_reels': 'false', 
                          'like_posts': 'false', 'explore_page': 'false', 'random_visits': 'false'}
        },
        {
            'name': 'Reels Only',
            'activities': {'feed_scroll': 'false', 'watch_reels': 'true', 'like_reels': 'true',
                          'like_posts': 'false', 'explore_page': 'false', 'random_visits': 'false'}
        },
        {
            'name': 'All Activities',
            'activities': {'feed_scroll': 'true', 'watch_reels': 'true', 'like_reels': 'true',
                          'like_posts': 'true', 'explore_page': 'true', 'random_visits': 'true'}
        }
    ]
    
    for activity_set in activity_sets:
        print(f"\n   Testing {activity_set['name']}...")
        try:
            with open('test_accounts.csv', 'rb') as f:
                files = {'accounts_file': ('test_accounts.csv', f, 'text/csv')}
                data = {
                    'warmup_duration': '1',
                    'max_concurrent': '1',
                    'visual_mode': 'false',
                    'activity_delay_min': '1',
                    'activity_delay_max': '2',
                    'scroll_attempts_min': '1',
                    'scroll_attempts_max': '2',
                    **activity_set['activities']
                }
                
                response = requests.post('http://localhost:5000/api/warmup/start', files=files, data=data)
                
                if response.status_code == 200:
                    script_id = response.json()['script_id']
                    print(f"      ✅ Started: {script_id}")
                    
                    time.sleep(3)  # Let it run briefly
                    
                    # Check configuration
                    status_response = requests.get(f'http://localhost:5000/api/script/{script_id}/status')
                    config = status_response.json()['config']['activities']
                    enabled_activities = [k for k, v in config.items() if v]
                    print(f"      📋 Enabled activities: {enabled_activities}")
                    
                    # Stop
                    requests.post(f'http://localhost:5000/api/script/{script_id}/stop')
                    
                else:
                    print(f"      ❌ Failed: {response.text}")
                    
        except Exception as e:
            print(f"      ❌ Error: {e}")

if __name__ == "__main__":
    test_visual_mode()
    test_activity_variations()
    print("\n🏆 Advanced testing completed!")
