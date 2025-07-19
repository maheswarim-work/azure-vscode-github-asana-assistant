#!/usr/bin/env python3
"""
Quick server runner for testing the AI Assistant API
"""

import uvicorn
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("🚀 Starting Azure VSCode GitHub Asana Assistant API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("⚡ Hot reload enabled - code changes will restart server")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    uvicorn.run(
        "assistant.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    )