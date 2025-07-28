#!/usr/bin/env python3
"""
Production Login Credentials Tester for wdyautomation.shop
This script helps you test different login combinations on your live server.
"""

import requests
import json
from datetime import datetime

# Production server URL
BASE_URL = "https://wdyautomation.shop"

def test_login_credentials(username, password):
    """Test login credentials against the live server"""
    
    print(f"\n🔐 Testing credentials: {username}")
    print("-" * 50)
    
    login_url = f"{BASE_URL}/api/auth/login"
    
    payload = {
        "username": username,
        "password": password
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📡 Sending request to: {login_url}")
        response = requests.post(login_url, json=payload, headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ LOGIN SUCCESSFUL!")
                print(f"   User ID: {data['user']['user_id']}")
                print(f"   Username: {data['user']['username']}")
                print(f"   Name: {data['user']['name']}")
                print(f"   Role: {data['user']['role']}")
                print(f"   Active: {data['user']['is_active']}")
                print(f"   Token: {data['token'][:50]}...")
                
                # Test a protected endpoint with the token
                test_protected_endpoint(data['token'])
                
                return {
                    'success': True,
                    'token': data['token'],
                    'user': data['user']
                }
            else:
                print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                return {'success': False, 'message': data.get('message')}
        
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid credentials")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Invalid username or password')}")
            except:
                print("   Error: Invalid username or password")
            return {'success': False, 'message': 'Invalid credentials'}
        
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return {'success': False, 'message': f'HTTP {response.status_code}'}
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - Server might be down")
        return {'success': False, 'message': 'Timeout'}
    except requests.exceptions.ConnectionError:
        print("🌐 Connection error - Check if server is running")
        return {'success': False, 'message': 'Connection error'}
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return {'success': False, 'message': str(e)}

def test_protected_endpoint(token):
    """Test a protected endpoint with the obtained token"""
    print(f"\n🔒 Testing protected endpoint...")
    
    stats_url = f"{BASE_URL}/api/scripts/stats"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(stats_url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Protected endpoint access successful!")
            data = response.json()
            print(f"   Total scripts: {data.get('total_scripts', 0)}")
            print(f"   Running scripts: {data.get('running_scripts', 0)}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")

def test_server_connectivity():
    """Test if the server is reachable"""
    print("🏥 Testing server connectivity...")
    print("=" * 50)
    
    health_url = f"{BASE_URL}/api/health"
    
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is online!")
            print(f"   Status: {data.get('status')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server connectivity failed: {e}")
        return False

def test_custom_credentials():
    """Allow user to input custom credentials"""
    print("\n🔧 Custom Credential Testing")
    print("=" * 50)
    print("Enter your own credentials to test:")
    
    try:
        username = input("👤 Username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return None
            
        password = input("🔑 Password: ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return None
            
        return test_login_credentials(username, password)
    except KeyboardInterrupt:
        print("\n⏹️ Testing cancelled by user")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_users_file():
    """Check if users.json file exists and show user info"""
    print("\n📋 Checking local users.json file...")
    print("=" * 50)
    
    users_files = ['users.json', '../users.json', './users.json']
    
    for users_file in users_files:
        try:
            with open(users_file, 'r') as f:
                users_data = json.load(f)
                
            print(f"✅ Found users file: {users_file}")
            print(f"📊 Total users: {len(users_data.get('users', []))}")
            
            for user in users_data.get('users', []):
                print(f"\n👤 User: {user.get('username', 'Unknown')}")
                print(f"   Name: {user.get('name', 'Unknown')}")
                print(f"   Role: {user.get('role', 'Unknown')}")
                print(f"   Active: {user.get('is_active', 'Unknown')}")
                print(f"   ID: {user.get('user_id', 'Unknown')}")
                
            print(f"\n💡 Try using these usernames with their actual passwords!")
            return users_data
            
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"❌ Error reading {users_file}: {e}")
            continue
    
    print("❌ No users.json file found in current or parent directory")
    print("💡 The server might be using a different user storage system")
    return None

def main():
    """Main function to test various login scenarios"""
    
    print("🚀 WDY Automation Production Login Tester")
    print("=" * 60)
    print(f"🌐 Testing server: {BASE_URL}")
    print(f"⏰ Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # First test server connectivity
    if not test_server_connectivity():
        print("\n💥 Cannot reach server. Exiting...")
        return
    
    # Check local users file
    users_data = check_users_file()
    
    # List of common credentials to test
    credentials_to_test = [
        ("admin", "admin123"),
        ("admin", "password"),
        ("admin", "admin"),
        ("test_va", "password123"),
        ("test_va", "password"),
        ("va_user", "password123"),
        ("user", "password"),
        ("administrator", "password"),
    ]
    
    # Add usernames from users.json if found
    if users_data:
        print(f"\n🔍 Adding usernames from users.json file...")
        for user in users_data.get('users', []):
            username = user.get('username')
            if username:
                # Try with common passwords
                credentials_to_test.extend([
                    (username, "password"),
                    (username, "password123"),
                    (username, f"{username}123"),
                    (username, "admin123"),
                ])
        
        # Remove duplicates
        credentials_to_test = list(set(credentials_to_test))
    
    print(f"\n🎯 Testing {len(credentials_to_test)} credential combinations...")
    
    successful_logins = []
    
    for username, password in credentials_to_test:
        result = test_login_credentials(username, password)
        if result['success']:
            successful_logins.append({
                'username': username,
                'password': password,
                'user_info': result.get('user', {}),
                'token': result.get('token', '')
            })
    
    # If no credentials worked, offer custom input
    if not successful_logins:
        print(f"\n❌ No automatic credentials worked. Let's try custom input...")
        
        while True:
            custom_result = test_custom_credentials()
            if custom_result and custom_result['success']:
                successful_logins.append({
                    'username': custom_result.get('user', {}).get('username', ''),
                    'password': 'custom_input',
                    'user_info': custom_result.get('user', {}),
                    'token': custom_result.get('token', '')
                })
                break
            elif custom_result is None:  # User cancelled
                break
            else:
                retry = input("\n🔄 Try different credentials? (y/N): ").strip().lower()
                if retry != 'y':
                    break
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if successful_logins:
        print(f"✅ Found {len(successful_logins)} working credential(s):")
        for i, login in enumerate(successful_logins, 1):
            print(f"\n{i}. Username: {login['username']}")
            print(f"   Password: {login['password']}")
            print(f"   Role: {login['user_info'].get('role', 'Unknown')}")
            print(f"   Name: {login['user_info'].get('name', 'Unknown')}")
            
            # Save to Postman format
            postman_data = {
                "username": login['username'],
                "password": login['password'],
                "token": login['token'],
                "user_role": login['user_info'].get('role', 'Unknown')
            }
            
            filename = f"postman_credentials_{login['username']}.json"
            with open(filename, 'w') as f:
                json.dump(postman_data, f, indent=2)
            print(f"   💾 Saved to: {filename}")
        
        print(f"\n🎉 SUCCESS! Use any of these credentials in Postman.")
        print(f"📋 Import the Postman collection and use these credentials.")
        
    else:
        print("❌ No working credentials found!")
        print("💡 Possible solutions:")
        print("   1. Check if you have SSH access to the server")
        print("   2. Look for users.json file on the server")
        print("   3. Check server deployment scripts for default users")
        print("   4. Contact server administrator")
        print("   5. Check environment variables on server")
        print("\n🔧 Server Access Commands (if you have SSH):")
        print("   ssh your-user@wdyautomation.shop")
        print("   cd /path/to/your/app")
        print("   cat users.json")
        print("   python create_second_admin.py")
        print("   python reset_passwords.py")
    
    print(f"\n📚 Next steps for Postman:")
    print(f"   1. Import collection: Instagram_Automation_API.postman_collection.json")
    print(f"   2. Import environment: WDY_Automation_Live.postman_environment.json")
    print(f"   3. Set base_url to: {BASE_URL}")
    if successful_logins:
        print(f"   4. Use credentials from above")
    else:
        print(f"   4. Get working credentials from server admin")
    print(f"   5. Run login request to get authentication token")
    
    print(f"\n🌐 Alternative testing method:")
    print(f"   Open Postman → Import → Choose files above → Test manually")

if __name__ == "__main__":
    main()
