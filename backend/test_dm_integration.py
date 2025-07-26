"""
Test script for DM automation integration
"""
import sys
import os
import tempfile
import pandas as pd

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

def create_test_files():
    """Create test files for validation"""
    
    # Create test bot accounts file
    bot_accounts = pd.DataFrame({
        'Username': ['test_bot1', 'test_bot2', 'test_bot3'],
        'Password': ['password1', 'password2', 'password3']
    })
    
    bot_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    bot_accounts.to_csv(bot_file.name, index=False)
    bot_file.close()
    
    # Create test target accounts file
    target_accounts = pd.DataFrame({
        'username': ['target1', 'target2', 'target3'],
        'first_name': ['John', 'Jane', 'Mike'],
        'city': ['New York', 'Los Angeles', 'Chicago'],
        'bio': ['entrepreneur', 'marketing manager', 'business owner']
    })
    
    target_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    target_accounts.to_csv(target_file.name, index=False)
    target_file.close()
    
    # Create test prompt file
    prompt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    prompt_file.write("Hi {first_name}! I noticed you're in {city} working in {bio}. Would love to connect!")
    prompt_file.close()
    
    return bot_file.name, target_file.name, prompt_file.name

def test_dm_automation_import():
    """Test if DM automation module can be imported"""
    try:
        from instagram_dm_automation import DMAutomationEngine, run_dm_automation
        print("✅ DM automation module imported successfully")
        
        # Test engine initialization
        engine = DMAutomationEngine()
        print("✅ DM automation engine initialized successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import DM automation module: {e}")
        return False

def test_file_validation():
    """Test file validation functionality"""
    try:
        bot_file, target_file, prompt_file = create_test_files()
        
        from instagram_dm_automation import DMAutomationEngine
        engine = DMAutomationEngine()
        
        # Test loading accounts
        accounts = engine.load_accounts(bot_file)
        print(f"✅ Loaded {len(accounts)} bot accounts")
        
        # Test loading targets
        targets = engine.load_target_users(target_file)
        print(f"✅ Loaded {len(targets)} target users")
        
        # Test loading prompt
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        prompt = engine.load_dm_prompt(prompt_file)
        print(f"✅ Loaded DM prompt: {len(prompt)} characters")
        
        # Cleanup
        os.unlink(bot_file)
        os.unlink(target_file)
        os.unlink(prompt_file)
        
        return True
    except Exception as e:
        print(f"❌ File validation test failed: {e}")
        return False

def test_message_generation():
    """Test AI message generation (without actual API call)"""
    try:
        from instagram_dm_automation import DMAutomationEngine
        engine = DMAutomationEngine()
        
        # Mock user data
        user_data = {
            'username': 'test_user',
            'first_name': 'John',
            'city': 'New York',
            'bio': 'entrepreneur'
        }
        
        prompt_template = "Create a message for {first_name} in {city} who works in {bio}"
        
        # This will use the fallback message since no AI client is setup
        message = engine.generate_message(user_data, prompt_template)
        print(f"✅ Generated fallback message: {message[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Message generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing DM Automation Integration")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_dm_automation_import),
        ("File Validation Test", test_file_validation),
        ("Message Generation Test", test_message_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! DM automation is ready.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main()
