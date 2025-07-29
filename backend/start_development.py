#!/usr/bin/env python3
"""
Development startup script for Instagram Automation Backend
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set development environment
os.environ['ENVIRONMENT'] = 'development'

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.environ.get('HOST', 'localhost')
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting Instagram Automation API in development mode...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    
    # Run with development settings
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level="debug",
        access_log=True,
        reload=True  # Enable reload in development
    )
