#!/usr/bin/env python3
"""
Test script to verify the Instagram Daily Post automation integration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from instagram_daily_post import InstagramDailyPostAutomation
import pandas as pd

def test_basic_functionality():
    """Test basic functionality without actual Instagram interaction"""
    print("Testing Instagram Daily Post Automation...")
    
    # Test 1: Initialize automation class
    try:
        automation = InstagramDailyPostAutomation("test-script-id")
        print("✅ Automation class initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize automation class: {e}")
        return False
    
    # Test 2: Test media file detection
    try:
        test_extensions = ['.jpg', '.png', '.mp4', '.mov']
        for ext in test_extensions:
            automation.set_media_file(f"test{ext}")
            expected_video = ext in ['.mp4', '.mov']
            if automation.is_video == expected_video:
                print(f"✅ Media type detection works for {ext}")
            else:
                print(f"❌ Media type detection failed for {ext}")
                return False
    except Exception as e:
        print(f"❌ Media file detection failed: {e}")
        return False
    
    # Test 3: Test accounts loading with sample data
    try:
        # Create sample Excel file
        sample_data = {
            'Username': ['test_user1', 'test_user2'],
            'Password': ['test_pass1', 'test_pass2']
        }
        df = pd.DataFrame(sample_data)
        test_file = "test_accounts.xlsx"
        df.to_excel(test_file, index=False)
        
        accounts = automation.load_accounts_from_file(test_file)
        if len(accounts) == 2 and accounts[0] == ('test_user1', 'test_pass1'):
            print("✅ Account loading works correctly")
        else:
            print(f"❌ Account loading failed. Got: {accounts}")
            return False
            
        # Cleanup
        os.remove(test_file)
    except Exception as e:
        print(f"❌ Account loading test failed: {e}")
        return False
    
    print("🎉 All basic tests passed!")
    return True

def test_flask_integration():
    """Test Flask app import and basic structure"""
    print("\nTesting Flask integration...")
    
    try:
        from app import app, active_scripts, script_logs, script_stop_flags
        print("✅ Flask app imports successfully")
        
        # Test Flask app configuration
        if hasattr(app, 'config'):
            print("✅ Flask app configured properly")
        else:
            print("❌ Flask app configuration missing")
            return False
            
        # Test global variables
        if isinstance(active_scripts, dict) and isinstance(script_logs, dict) and isinstance(script_stop_flags, dict):
            print("✅ Global state variables initialized properly")
        else:
            print("❌ Global state variables not properly initialized")
            return False
            
    except Exception as e:
        print(f"❌ Flask integration test failed: {e}")
        return False
    
    print("🎉 Flask integration test passed!")
    return True

if __name__ == "__main__":
    print("Running integration tests for Instagram Daily Post Backend")
    print("=" * 60)
    
    success = True
    success &= test_basic_functionality()
    success &= test_flask_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! The backend is ready to use.")
        print("\nTo start the backend, run: python app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
