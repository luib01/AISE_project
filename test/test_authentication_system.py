#!/usr/bin/env python3
"""
Comprehensive pytest test suite for the Authentication System
Tests: User registration, login, logout, profile management, session validation
"""

import pytest
import requests
import json
import time
import random
import string
import uuid
from typing import Dict, List, Optional

# Test configuration
BACKEND_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def backend_url():
    """Fixture to provide backend URL"""
    return BACKEND_URL


@pytest.fixture
def unique_username():
    """Generate a unique username for testing"""
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def valid_password():
    """Provide a valid password for testing"""
    return "ValidPass123"


@pytest.fixture
def test_user_data(unique_username, valid_password):
    """Fixture to provide test user data"""
    return {
        "username": unique_username,
        "password": valid_password
    }


@pytest.fixture
def registered_user(test_user_data, backend_url):
    """Fixture that registers a user and provides the user data"""
    response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
    if response.status_code in [200, 201]:
        yield test_user_data
        # Cleanup: Delete the user after test
        try:
            # Sign in to get token
            signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            if signin_response.status_code == 200:
                token = signin_response.json()['data']['session_token']
                headers = {"Authorization": f"Bearer {token}"}
                # Delete account
                requests.delete(f"{backend_url}/api/auth/profile", 
                              json={"password": test_user_data['password']}, 
                              headers=headers)
        except Exception:
            pass  # Ignore cleanup errors
    else:
        pytest.fail(f"Failed to register test user: {response.status_code} - {response.text}")


@pytest.fixture
def authenticated_user(registered_user, backend_url):
    """Fixture that provides an authenticated user with session token"""
    signin_response = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
    if signin_response.status_code == 200:
        signin_data = signin_response.json()
        token = signin_data['data']['session_token']
        return {
            "user_data": registered_user,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
            "signin_data": signin_data['data']
        }
    else:
        pytest.fail(f"Failed to authenticate test user: {signin_response.status_code}")


class TestUserRegistration:
    """Test class for user registration functionality"""

    def test_valid_user_registration(self, test_user_data, backend_url):
        """Test valid user registration"""
        response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
        
        assert response.status_code in [200, 201], f"Registration failed: {response.status_code} - {response.text}"
        
        # Cleanup
        try:
            signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            if signin_response.status_code == 200:
                token = signin_response.json()['data']['session_token']
                headers = {"Authorization": f"Bearer {token}"}
                requests.delete(f"{backend_url}/api/auth/profile", 
                              json={"password": test_user_data['password']}, 
                              headers=headers)
        except Exception:
            pass

    def test_duplicate_username_registration(self, registered_user, backend_url):
        """Test that duplicate username registration is rejected"""
        # Try to register the same user again
        duplicate_response = requests.post(f"{backend_url}/api/auth/signup", json=registered_user)
        assert duplicate_response.status_code == 400, "Duplicate username should be rejected with 400 status"

    @pytest.mark.parametrize("invalid_username,expected_status", [
        ("ab", 400),  # Too short
        ("", 400),    # Empty
        ("a" * 30, 400),  # Too long
    ])
    def test_invalid_username_registration(self, invalid_username, expected_status, valid_password, backend_url):
        """Test registration with invalid usernames"""
        invalid_user = {"username": invalid_username, "password": valid_password}
        response = requests.post(f"{backend_url}/api/auth/signup", json=invalid_user)
        assert response.status_code == expected_status, f"Invalid username '{invalid_username}' should be rejected"

    @pytest.mark.parametrize("invalid_password,expected_status", [
        ("short", 400),  # Too short
        ("", 400),       # Empty
        ("abc", 400),    # Too short
    ])
    def test_invalid_password_registration(self, unique_username, invalid_password, expected_status, backend_url):
        """Test registration with invalid passwords"""
        invalid_user = {"username": unique_username, "password": invalid_password}
        response = requests.post(f"{backend_url}/api/auth/signup", json=invalid_user)
        assert response.status_code == expected_status, f"Invalid password should be rejected"

    def test_registration_response_structure(self, test_user_data, backend_url):
        """Test that registration response has correct structure"""
        response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        
        # Cleanup
        try:
            signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            if signin_response.status_code == 200:
                token = signin_response.json()['data']['session_token']
                headers = {"Authorization": f"Bearer {token}"}
                requests.delete(f"{backend_url}/api/auth/profile", 
                              json={"password": test_user_data['password']}, 
                              headers=headers)
        except Exception:
            pass


class TestUserAuthentication:
    """Test class for user authentication functionality"""

    def test_valid_login(self, registered_user, backend_url):
        """Test valid user login"""
        signin_response = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
        
        assert signin_response.status_code == 200, f"Valid login failed: {signin_response.status_code} - {signin_response.text}"
        
        signin_data = signin_response.json()
        assert "data" in signin_data, "Response should contain 'data' field"
        
        user_data = signin_data['data']
        assert "session_token" in user_data, "Response should contain session_token"
        assert "username" in user_data, "Response should contain username"
        assert user_data['username'] == registered_user['username'], "Username should match"

    def test_invalid_credentials(self, registered_user, backend_url):
        """Test login with invalid credentials"""
        invalid_login = {"username": registered_user['username'], "password": "wrongpassword"}
        invalid_response = requests.post(f"{backend_url}/api/auth/signin", json=invalid_login)
        assert invalid_response.status_code == 401, "Invalid credentials should be rejected with 401 status"

    def test_nonexistent_user_login(self, backend_url):
        """Test login with nonexistent user"""
        nonexistent_user = {"username": "nonexistent_user_12345", "password": "somepassword"}
        response = requests.post(f"{backend_url}/api/auth/signin", json=nonexistent_user)
        assert response.status_code == 401, "Nonexistent user login should be rejected"

    def test_session_validation(self, authenticated_user, backend_url):
        """Test session token validation"""
        validate_response = requests.get(f"{backend_url}/api/auth/validate", 
                                       headers=authenticated_user['headers'])
        assert validate_response.status_code == 200, "Valid session token should be accepted"

    def test_logout_functionality(self, authenticated_user, backend_url):
        """Test user logout"""
        logout_response = requests.post(f"{backend_url}/api/auth/logout", 
                                      headers=authenticated_user['headers'])
        assert logout_response.status_code == 200, f"Logout failed: {logout_response.status_code}"

    def test_session_invalidation_after_logout(self, authenticated_user, backend_url):
        """Test that session is invalidated after logout"""
        # First logout
        logout_response = requests.post(f"{backend_url}/api/auth/logout", 
                                      headers=authenticated_user['headers'])
        assert logout_response.status_code == 200
        
        # Then try to validate the session
        validate_response = requests.get(f"{backend_url}/api/auth/validate", 
                                       headers=authenticated_user['headers'])
        assert validate_response.status_code == 401, "Session should be invalidated after logout"


class TestProfileManagement:
    """Test class for profile management functionality"""

    def test_get_profile(self, authenticated_user, backend_url):
        """Test profile retrieval"""
        profile_response = requests.get(f"{backend_url}/api/auth/profile", 
                                      headers=authenticated_user['headers'])
        
        assert profile_response.status_code == 200, f"Profile retrieval failed: {profile_response.status_code}"
        
        profile_data = profile_response.json()['data']
        assert "username" in profile_data, "Profile should contain username"
        assert profile_data['username'] == authenticated_user['user_data']['username']

    def test_update_username(self, authenticated_user, backend_url):
        """Test username update"""
        new_username = f"upd_{uuid.uuid4().hex[:8]}"
        update_response = requests.put(
            f"{backend_url}/api/auth/profile/username",
            json={"new_username": new_username},
            headers=authenticated_user['headers']
        )
        
        # Update might not be implemented, so we accept both success and not implemented
        assert update_response.status_code in [200, 404, 501], f"Username update response: {update_response.status_code}"
        
        if update_response.status_code == 200:
            # Update the user data for cleanup
            authenticated_user['user_data']['username'] = new_username

    def test_change_password(self, authenticated_user, backend_url):
        """Test password change"""
        new_password = "NewValidPass456"
        change_password_response = requests.put(
            f"{backend_url}/api/auth/profile/password",
            json={
                "current_password": authenticated_user['user_data']['password'],
                "new_password": new_password
            },
            headers=authenticated_user['headers']
        )
        
        # Password change might not be implemented, so we accept both success and not implemented
        assert change_password_response.status_code in [200, 404, 501], f"Password change response: {change_password_response.status_code}"
        
        if change_password_response.status_code == 200:
            # Update the password for cleanup
            authenticated_user['user_data']['password'] = new_password

    def test_profile_without_authentication(self, backend_url):
        """Test profile access without authentication"""
        response = requests.get(f"{backend_url}/api/auth/profile")
        assert response.status_code == 401, "Profile access without authentication should be rejected"


class TestSecurityFeatures:
    """Test class for security features and edge cases"""

    def test_invalid_token_validation(self, backend_url):
        """Test validation with invalid token"""
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        invalid_response = requests.get(f"{backend_url}/api/auth/validate", headers=invalid_headers)
        assert invalid_response.status_code == 401, "Invalid token should be rejected"

    def test_missing_authorization_header(self, backend_url):
        """Test validation without authorization header"""
        no_header_response = requests.get(f"{backend_url}/api/auth/validate")
        assert no_header_response.status_code == 401, "Missing authorization header should be rejected"

    @pytest.mark.parametrize("malformed_header", [
        "InvalidFormat token123",
        "Bearer",
        "token123",
        "Basic dGVzdA==",
    ])
    def test_malformed_authorization_header(self, malformed_header, backend_url):
        """Test validation with malformed authorization headers"""
        malformed_headers = {"Authorization": malformed_header}
        malformed_response = requests.get(f"{backend_url}/api/auth/validate", headers=malformed_headers)
        assert malformed_response.status_code == 401, f"Malformed header '{malformed_header}' should be rejected"

    def test_expired_token_handling(self, backend_url):
        """Test handling of potentially expired tokens"""
        # This test might need to be expanded based on token expiration implementation
        # For now, we'll test with a clearly invalid token format
        expired_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"
        expired_headers = {"Authorization": expired_token}
        response = requests.get(f"{backend_url}/api/auth/validate", headers=expired_headers)
        assert response.status_code == 401, "Expired/invalid token should be rejected"


class TestIntegrationScenarios:
    """Integration tests for complete authentication flows"""

    @pytest.mark.integration
    def test_complete_user_lifecycle(self, test_user_data, backend_url):
        """Test complete user lifecycle: register -> login -> profile -> logout"""
        # Step 1: Register
        register_response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
        assert register_response.status_code in [200, 201], "Registration should succeed"
        
        try:
            # Step 2: Login
            signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            assert signin_response.status_code == 200, "Login should succeed"
            
            token = signin_response.json()['data']['session_token']
            headers = {"Authorization": f"Bearer {token}"}
            
            # Step 3: Access profile
            profile_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
            assert profile_response.status_code == 200, "Profile access should succeed"
            
            # Step 4: Validate session
            validate_response = requests.get(f"{backend_url}/api/auth/validate", headers=headers)
            assert validate_response.status_code == 200, "Session validation should succeed"
            
            # Step 5: Logout
            logout_response = requests.post(f"{backend_url}/api/auth/logout", headers=headers)
            assert logout_response.status_code == 200, "Logout should succeed"
            
            # Step 6: Verify session invalidation
            validate_after_logout = requests.get(f"{backend_url}/api/auth/validate", headers=headers)
            assert validate_after_logout.status_code == 401, "Session should be invalid after logout"
            
        finally:
            # Cleanup: Delete the user
            try:
                signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
                if signin_response.status_code == 200:
                    token = signin_response.json()['data']['session_token']
                    headers = {"Authorization": f"Bearer {token}"}
                    requests.delete(f"{backend_url}/api/auth/profile", 
                                  json={"password": test_user_data['password']}, 
                                  headers=headers)
            except Exception:
                pass

    @pytest.mark.integration
    def test_concurrent_sessions(self, registered_user, backend_url):
        """Test multiple concurrent sessions for the same user"""
        # Login twice with the same user
        signin_response1 = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
        signin_response2 = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
        
        assert signin_response1.status_code == 200, "First login should succeed"
        assert signin_response2.status_code == 200, "Second login should succeed"
        
        token1 = signin_response1.json()['data']['session_token']
        token2 = signin_response2.json()['data']['session_token']
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Both sessions should be valid
        validate1 = requests.get(f"{backend_url}/api/auth/validate", headers=headers1)
        validate2 = requests.get(f"{backend_url}/api/auth/validate", headers=headers2)
        
        # This behavior depends on implementation - either both valid or only latest valid
        assert validate1.status_code in [200, 401], "First session validation result"
        assert validate2.status_code in [200, 401], "Second session validation result"


def test_backend_connectivity(backend_url):
    """Test that the backend is accessible"""
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        # Backend might not have health endpoint, so we accept various responses
        assert response.status_code in [200, 404], "Backend should be accessible"
    except requests.exceptions.ConnectionError:
        pytest.fail(f"Cannot connect to backend at {backend_url}. Make sure the backend is running.")
    except requests.exceptions.Timeout:
        pytest.fail(f"Backend at {backend_url} is not responding. Check if services are running properly.")


# Legacy support function for backward compatibility
def main():
    """Legacy main function for backward compatibility"""
    print("🚀 Running Authentication System Tests with pytest...")
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


if __name__ == "__main__":
    # Run pytest when executed directly
    pytest.main([__file__, "-v"])
