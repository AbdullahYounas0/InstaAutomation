#!/usr/bin/env python3
"""
Test script for geolocation functionality
"""

from auth import UserManager
import sys

def test_geolocation():
    """Test geolocation with various IP addresses"""
    um = UserManager()
    
    test_ips = [
        '127.0.0.1',  # Local
        'system',     # System
        '8.8.8.8',    # Google DNS (US)
        '1.1.1.1',    # Cloudflare (US)
        '208.67.222.222',  # OpenDNS (US)
    ]
    
    print("Testing geolocation functionality:")
    print("-" * 50)
    
    for ip in test_ips:
        try:
            location = um.get_location_from_ip(ip)
            print(f"IP: {ip:15} -> {location['city']}, {location['country']} ({location['country_code']})")
        except Exception as e:
            print(f"IP: {ip:15} -> Error: {e}")
    
    print("-" * 50)
    print("Geolocation test completed!")

if __name__ == "__main__":
    test_geolocation()
