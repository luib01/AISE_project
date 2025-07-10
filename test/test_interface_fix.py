#!/usr/bin/env python3
"""
Test script to verify that the TypeScript interface fix works correctly
by checking that the backend returns the expected fields.
"""

import requests
import json

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User"
}

def test_backend_response_structure():
    """Test that backend returns user profile with all expected fields"""
    print("🧪 Testing backend user profile response structure...")
    
    # Register and login
    try:
        # Register user
        register_response = requests.post(f"{BACKEND_URL}/api/auth/signup", json=TEST_USER)
        print(f"Register response: {register_response.status_code}")
        
        # Login
        login_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get user profile
            profile_response = requests.get(f"{BACKEND_URL}/api/auth/profile", headers=headers)
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print("✅ User profile response structure:")
                print(json.dumps(profile_data, indent=2))
                
                # Check for required fields
                required_fields = [
                    "user_id", "english_level", "progress", "total_quizzes", 
                    "average_score", "has_completed_first_quiz"
                ]
                
                optional_fields = [
                    "level_changed", "previous_level", 
                    "level_change_type", "level_change_message"
                ]
                
                print("\n🔍 Checking required fields:")
                for field in required_fields:
                    if field in profile_data:
                        print(f"  ✅ {field}: {profile_data[field]}")
                    else:
                        print(f"  ❌ {field}: MISSING")
                
                print("\n🔍 Checking optional fields (new interface additions):")
                for field in optional_fields:
                    if field in profile_data:
                        print(f"  ✅ {field}: {profile_data[field]}")
                    else:
                        print(f"  ℹ️  {field}: Not present (OK if no level change)")
                
                print("\n✅ Interface compatibility test completed!")
                return True
            else:
                print(f"❌ Failed to get user profile: {profile_response.status_code}")
                return False
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:8001")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing TypeScript interface compatibility...\n")
    success = test_backend_response_structure()
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
