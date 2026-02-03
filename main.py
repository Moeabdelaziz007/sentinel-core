#!/usr/bin/env python3
"""Sentinel Shield - Main entry point"""

import uvicorn
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("🛡️ Starting Sentinel Shield...")
    print("Access API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )