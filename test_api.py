#!/usr/bin/env python3
"""
Test script for the AI Assistant API
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, timeout=10):
    """Test a single API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                json_response = response.json()
                print(f"   Response: {json.dumps(json_response, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   Response: {response.text[:200]}...")
        
        return response.status_code < 400
        
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Connection refused (server not running?)")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ {method} {endpoint} - Request timed out")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {str(e)}")
        return False

def main():
    print("🧪 Testing AI Assistant API Endpoints")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        ("GET", "/", None),
        ("GET", "/health", None),
        ("GET", "/status", None),
        ("POST", "/command", {
            "command": "Hello, what can you help me with?",
            "context": {"test": True}
        }),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data in tests:
        if test_endpoint(method, endpoint, data):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
    
    print("\n📖 For interactive API documentation, visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()