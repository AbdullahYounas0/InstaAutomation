#!/usr/bin/env python3
"""
Production startup script for Instagram Automation Backend
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set production environment
os.environ['ENVIRONMENT'] = 'production'

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting Instagram Automation API in production mode...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    
    # Run with production settings
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=1,  # Single worker for simplicity, can be increased
        log_level="info",
        access_log=True,
        reload=False  # No reload in production
    )
