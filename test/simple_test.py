#!/usr/bin/env python3
"""
Simple test to verify first quiz completion flag functionality.
"""

import requests
import json

BACKEND_URL = "http://localhost:8000"

def test_simple():
    print("🧪 Simple test for first quiz flag...")
    
    # Test user
    user = {
        "username": "simple_test_user",
        "password": "password123"
    }
    
    try:
        # 1. Register user
        print("1. Registering user...")
        register_resp = requests.post(f"{BACKEND_URL}/api/auth/signup", json=user)
        print(f"   Status: {register_resp.status_code}")
        
        # 2. Sign in user
        print("2. Signing in user...")
        signin_resp = requests.post(f"{BACKEND_URL}/api/auth/signin", json=user)
        print(f"   Status: {signin_resp.status_code}")
        
        if signin_resp.status_code == 200:
            data = signin_resp.json()
            user_data = data.get("data", {})
            
            print(f"   User data: {json.dumps(user_data, indent=2)}")
            
            has_completed = user_data.get("has_completed_first_quiz", "NOT FOUND")
            print(f"   has_completed_first_quiz: {has_completed}")
            
            if has_completed == False:
                print("   ✅ SUCCESS: New user correctly shows has_completed_first_quiz = False")
                return True
            else:
                print("   ❌ ERROR: New user should have has_completed_first_quiz = False")
                return False
        else:
            print(f"   ❌ Sign in failed: {signin_resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_simple()
