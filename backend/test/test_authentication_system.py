#!/usr/bin/env python3
"""
Comprehensive test suite for the Authentication System
Tests: User registration, login, logout, profile management, session validation
"""

import requests
import json
import time
import random
import string

# Test configuration
BACKEND_URL = "http://localhost:8000"

class AuthenticationTester:
    def __init__(self):
        self.test_users = []
        self.session_tokens = {}
    
    def generate_random_username(self):
        """Generate a random username for testing (3-20 chars, alphanumeric + underscore)"""
        # Create shorter, compliant username
        random_num = random.randint(100, 999)
        return f"test_{random_num}"
    
    def cleanup_test_users(self):
        """Clean up test users created during testing"""
        print("🧹 Cleaning up test users...")
        for user_data in self.test_users:
            try:
                username = user_data['username']
                password = user_data['password']
                
                # Sign in to get token
                signin_response = requests.post(f"{BACKEND_URL}/api/auth/signin", 
                                              json={"username": username, "password": password})
                if signin_response.status_code == 200:
                    token = signin_response.json()['data']['session_token']
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # Delete account
                    delete_response = requests.delete(f"{BACKEND_URL}/api/auth/profile", 
                                                    json={"password": password}, headers=headers)
                    if delete_response.status_code == 200:
                        print(f"   ✅ Deleted test user: {username}")
                    else:
                        print(f"   ⚠️ Failed to delete test user: {username}")
            except Exception as e:
                print(f"   ⚠️ Error deleting user {user_data.get('username', 'unknown')}: {e}")
    
    def test_user_registration(self):
        """Test user registration functionality"""
        print("🧪 Testing User Registration...")
        
        # Test 1: Valid registration
        username = self.generate_random_username()
        password = "ValidPass123"
        user_data = {"username": username, "password": password}
        
        response = requests.post(f"{BACKEND_URL}/api/auth/signup", json=user_data)
        
        if response.status_code == 200:
            print("   ✅ Valid registration successful")
            self.test_users.append(user_data)
        else:
            print(f"   ❌ Valid registration failed: {response.status_code} - {response.text}")
            return False
        
        # Test 2: Duplicate username
        duplicate_response = requests.post(f"{BACKEND_URL}/api/auth/signup", json=user_data)
        if duplicate_response.status_code == 400:
            print("   ✅ Duplicate username properly rejected")
        else:
            print(f"   ❌ Duplicate username not properly handled: {duplicate_response.status_code}")
        
        # Test 3: Invalid username (too short)
        invalid_user = {"username": "ab", "password": "ValidPass123"}
        invalid_response = requests.post(f"{BACKEND_URL}/api/auth/signup", json=invalid_user)
        if invalid_response.status_code == 400:
            print("   ✅ Invalid username (too short) properly rejected")
        else:
            print(f"   ❌ Invalid username not properly handled: {invalid_response.status_code}")
        
        # Test 4: Invalid password (too short)
        invalid_pass = {"username": self.generate_random_username(), "password": "short"}
        invalid_pass_response = requests.post(f"{BACKEND_URL}/api/auth/signup", json=invalid_pass)
        if invalid_pass_response.status_code == 400:
            print("   ✅ Invalid password (too short) properly rejected")
        else:
            print(f"   ❌ Invalid password not properly handled: {invalid_pass_response.status_code}")
        
        return True
    
    def test_user_authentication(self):
        """Test user login and logout functionality"""
        print("🧪 Testing User Authentication...")
        
        if not self.test_users:
            print("   ❌ No test users available for authentication testing")
            return False
        
        user_data = self.test_users[0]
        
        # Test 1: Valid login
        signin_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json=user_data)
        
        if signin_response.status_code == 200:
            signin_data = signin_response.json()
            token = signin_data['data']['session_token']
            username = signin_data['data']['username']
            self.session_tokens[username] = token
            print("   ✅ Valid login successful")
            print(f"      Token received: {token[:20]}...")
        else:
            print(f"   ❌ Valid login failed: {signin_response.status_code} - {signin_response.text}")
            return False
        
        # Test 2: Invalid credentials
        invalid_login = {"username": user_data['username'], "password": "wrongpassword"}
        invalid_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json=invalid_login)
        if invalid_response.status_code == 401:
            print("   ✅ Invalid credentials properly rejected")
        else:
            print(f"   ❌ Invalid credentials not properly handled: {invalid_response.status_code}")
        
        # Test 3: Session validation
        headers = {"Authorization": f"Bearer {token}"}
        validate_response = requests.get(f"{BACKEND_URL}/api/auth/validate", headers=headers)
        if validate_response.status_code == 200:
            print("   ✅ Session validation successful")
        else:
            print(f"   ❌ Session validation failed: {validate_response.status_code}")
        
        # Test 4: Logout
        logout_response = requests.post(f"{BACKEND_URL}/api/auth/logout", headers=headers)
        if logout_response.status_code == 200:
            print("   ✅ Logout successful")
        else:
            print(f"   ❌ Logout failed: {logout_response.status_code}")
        
        # Test 5: Session invalidation after logout
        validate_after_logout = requests.get(f"{BACKEND_URL}/api/auth/validate", headers=headers)
        if validate_after_logout.status_code == 401:
            print("   ✅ Session properly invalidated after logout")
        else:
            print(f"   ❌ Session not invalidated after logout: {validate_after_logout.status_code}")
        
        return True
    
    def test_profile_management(self):
        """Test profile viewing and management functionality"""
        print("🧪 Testing Profile Management...")
        
        if not self.test_users:
            print("   ❌ No test users available for profile testing")
            return False
        
        user_data = self.test_users[0]
        
        # Login first
        signin_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json=user_data)
        if signin_response.status_code != 200:
            print("   ❌ Failed to login for profile testing")
            return False
        
        token = signin_response.json()['data']['session_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Get profile
        profile_response = requests.get(f"{BACKEND_URL}/api/auth/profile", headers=headers)
        if profile_response.status_code == 200:
            profile_data = profile_response.json()['data']
            print("   ✅ Profile retrieval successful")
            print(f"      Username: {profile_data.get('username')}")
            print(f"      English Level: {profile_data.get('english_level')}")
            print(f"      Total Quizzes: {profile_data.get('total_quizzes')}")
        else:
            print(f"   ❌ Profile retrieval failed: {profile_response.status_code}")
            return False
        
        # Test 2: Update username
        new_username = f"upd_{random.randint(100, 999)}"
        update_username_response = requests.put(
            f"{BACKEND_URL}/api/auth/profile/username",
            json={"new_username": new_username},
            headers=headers
        )
        if update_username_response.status_code == 200:
            print("   ✅ Username update successful")
            user_data['username'] = new_username  # Update for cleanup
        else:
            print(f"   ❌ Username update failed: {update_username_response.status_code}")
        
        # Test 3: Change password
        new_password = "NewValidPass456"
        change_password_response = requests.put(
            f"{BACKEND_URL}/api/auth/profile/password",
            json={"current_password": user_data['password'], "new_password": new_password},
            headers=headers
        )
        if change_password_response.status_code == 200:
            print("   ✅ Password change successful")
            user_data['password'] = new_password  # Update for cleanup
        else:
            print(f"   ❌ Password change failed: {change_password_response.status_code}")
        
        return True
    
    def test_security_features(self):
        """Test security features and edge cases"""
        print("🧪 Testing Security Features...")
        
        # Test 1: Invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        invalid_response = requests.get(f"{BACKEND_URL}/api/auth/validate", headers=invalid_headers)
        if invalid_response.status_code == 401:
            print("   ✅ Invalid token properly rejected")
        else:
            print(f"   ❌ Invalid token not properly handled: {invalid_response.status_code}")
        
        # Test 2: Missing authorization header
        no_header_response = requests.get(f"{BACKEND_URL}/api/auth/validate")
        if no_header_response.status_code == 401:
            print("   ✅ Missing authorization header properly handled")
        else:
            print(f"   ❌ Missing authorization header not properly handled: {no_header_response.status_code}")
        
        # Test 3: Malformed authorization header
        malformed_headers = {"Authorization": "InvalidFormat token123"}
        malformed_response = requests.get(f"{BACKEND_URL}/api/auth/validate", headers=malformed_headers)
        if malformed_response.status_code == 401:
            print("   ✅ Malformed authorization header properly rejected")
        else:
            print(f"   ❌ Malformed authorization header not properly handled: {malformed_response.status_code}")
        
        return True
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting Authentication System Tests...\n")
        
        success_count = 0
        total_tests = 4
        
        try:
            if self.test_user_registration():
                success_count += 1
            print()
            
            if self.test_user_authentication():
                success_count += 1
            print()
            
            if self.test_profile_management():
                success_count += 1
            print()
            
            if self.test_security_features():
                success_count += 1
            print()
            
        except Exception as e:
            print(f"❌ Unexpected error during testing: {e}")
        
        finally:
            self.cleanup_test_users()
        
        print(f"\n📊 Authentication Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🎉 All authentication tests passed!")
            return True
        else:
            print("⚠️ Some authentication tests failed. Check the output above for details.")
            return False

def main():
    """Main test function"""
    tester = AuthenticationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    main()
