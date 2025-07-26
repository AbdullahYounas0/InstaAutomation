#!/usr/bin/env python3
"""
Test script to verify DM response collection functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from instagram_dm_automation import DMAutomationEngine

def test_response_detection():
    """Test the positive response detection logic"""
    engine = DMAutomationEngine()
    
    # Test positive responses
    positive_messages = [
        "Yes, I'm interested!",
        "Sounds good, tell me more",
        "How much does it cost?",
        "This is exactly what I need",
        "Can we schedule a call?",
        "I'd like more details please",
        "When can we start?",
        "Perfect timing! Let's talk",
        "What's the price for this service?",
        "I appreciate you reaching out"
    ]
    
    # Test negative responses
    negative_messages = [
        "No thanks",
        "Not interested",
        "This is spam",
        "Stop messaging me",
        "Leave me alone"
    ]
    
    # Test neutral messages
    neutral_messages = [
        "Hi",
        "Ok",
        "Thanks",
        "😊",
        "Cool"
    ]
    
    print("Testing Positive Response Detection:")
    print("=" * 50)
    
    print("\n✅ POSITIVE MESSAGES:")
    for msg in positive_messages:
        result = engine.is_positive_response(msg)
        print(f"  '{msg}' -> {result}")
        assert result == True, f"Failed to detect positive response: {msg}"
    
    print("\n❌ NEGATIVE MESSAGES:")
    for msg in negative_messages:
        result = engine.is_positive_response(msg)
        print(f"  '{msg}' -> {result}")
        assert result == False, f"Incorrectly detected negative as positive: {msg}"
    
    print("\n🔍 NEUTRAL MESSAGES:")
    for msg in neutral_messages:
        result = engine.is_positive_response(msg)
        print(f"  '{msg}' -> {result}")
        # Neutral messages should mostly be False, but some might be True depending on content
    
    print("\n✅ All tests passed! Response detection is working correctly.")

if __name__ == "__main__":
    test_response_detection()
