#!/usr/bin/env python3
"""
Pytest test to verify first quiz completion flag functionality.
"""

import pytest
import requests
import json
import uuid
from typing import Dict, Any

BACKEND_URL = "http://localhost:8000"


class TestFirstQuizFlag:
    """Test class for first quiz completion flag functionality"""

    @pytest.fixture
    def unique_user(self) -> Dict[str, str]:
        """Fixture to provide a unique test user for each test"""
        return {
            "username": f"test_user_{uuid.uuid4().hex[:8]}",
            "password": "password123"
        }

    @pytest.fixture
    def backend_url(self) -> str:
        """Fixture to provide backend URL"""
        return BACKEND_URL

    def test_new_user_first_quiz_flag_is_false(self, unique_user: Dict[str, str], backend_url: str):
        """Test that a new user has has_completed_first_quiz set to False"""
        # Register user
        register_resp = requests.post(f"{backend_url}/api/auth/signup", json=unique_user)
        assert register_resp.status_code in [200, 201], f"Registration failed with status {register_resp.status_code}: {register_resp.text}"

        # Sign in user
        signin_resp = requests.post(f"{backend_url}/api/auth/signin", json=unique_user)
        assert signin_resp.status_code == 200, f"Sign in failed with status {signin_resp.status_code}: {signin_resp.text}"

        # Verify response structure
        data = signin_resp.json()
        assert "data" in data, "Response should contain 'data' field"
        
        user_data = data["data"]
        assert isinstance(user_data, dict), "User data should be a dictionary"

        # Check first quiz flag
        has_completed = user_data.get("has_completed_first_quiz")
        assert has_completed is not None, "has_completed_first_quiz field should be present in user data"
        assert has_completed is False, f"New user should have has_completed_first_quiz = False, got {has_completed}"

    def test_user_registration_response_structure(self, unique_user: Dict[str, str], backend_url: str):
        """Test that user registration returns proper response structure"""
        register_resp = requests.post(f"{backend_url}/api/auth/signup", json=unique_user)
        
        # Should succeed or indicate user already exists
        assert register_resp.status_code in [200, 201, 400], f"Unexpected registration status: {register_resp.status_code}"
        
        if register_resp.status_code in [200, 201]:
            data = register_resp.json()
            assert isinstance(data, dict), "Registration response should be a dictionary"

    def test_user_signin_response_structure(self, unique_user: Dict[str, str], backend_url: str):
        """Test that user signin returns proper response structure with required fields"""
        # First register the user
        register_resp = requests.post(f"{backend_url}/api/auth/signup", json=unique_user)
        assert register_resp.status_code in [200, 201], "User registration should succeed"

        # Then sign in
        signin_resp = requests.post(f"{backend_url}/api/auth/signin", json=unique_user)
        assert signin_resp.status_code == 200, f"Sign in should succeed, got {signin_resp.status_code}"

        data = signin_resp.json()
        assert "data" in data, "Signin response should contain 'data' field"
        
        user_data = data["data"]
        required_fields = ["username", "has_completed_first_quiz"]
        
        for field in required_fields:
            assert field in user_data, f"User data should contain '{field}' field"

    def test_backend_connectivity(self, backend_url: str):
        """Test that the backend is accessible"""
        try:
            # Try to access a health endpoint or any endpoint
            response = requests.get(f"{backend_url}/health", timeout=5)
            assert True, "Backend should be accessible"
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Cannot connect to backend at {backend_url}. Make sure the backend is running.")
        except requests.exceptions.Timeout:
            pytest.fail(f"Backend at {backend_url} is not responding. Check if services are running properly.")

    @pytest.mark.integration
    def test_full_user_flow_first_quiz_flag(self, unique_user: Dict[str, str], backend_url: str):
        """Integration test for complete user flow with first quiz flag"""
        # Step 1: Register user
        register_resp = requests.post(f"{backend_url}/api/auth/signup", json=unique_user)
        assert register_resp.status_code in [200, 201], "User registration should succeed"

        # Step 2: Sign in and verify initial state
        signin_resp = requests.post(f"{backend_url}/api/auth/signin", json=unique_user)
        assert signin_resp.status_code == 200, "User signin should succeed"
        
        initial_data = signin_resp.json()["data"]
        assert initial_data.get("has_completed_first_quiz") is False, "Initial state should be False"

        # Step 3: Verify the flag persists across multiple logins
        signin_resp2 = requests.post(f"{backend_url}/api/auth/signin", json=unique_user)
        assert signin_resp2.status_code == 200, "Second signin should succeed"
        
        second_data = signin_resp2.json()["data"]
        assert second_data.get("has_completed_first_quiz") is False, "Flag should persist as False"


def test_simple_compatibility():
    """Legacy test function for backward compatibility"""
    user = {
        "username": f"legacy_test_user_{uuid.uuid4().hex[:8]}",
        "password": "password123"
    }
    
    try:
        # Register user
        register_resp = requests.post(f"{BACKEND_URL}/api/auth/signup", json=user)
        assert register_resp.status_code in [200, 201], f"Registration failed: {register_resp.text}"
        
        # Sign in user
        signin_resp = requests.post(f"{BACKEND_URL}/api/auth/signin", json=user)
        assert signin_resp.status_code == 200, f"Signin failed: {signin_resp.text}"
        
        data = signin_resp.json()
        user_data = data.get("data", {})
        has_completed = user_data.get("has_completed_first_quiz")
        
        assert has_completed is False, f"Expected False, got {has_completed}"
        
    except requests.exceptions.ConnectionError:
        pytest.fail(f"Cannot connect to backend at {BACKEND_URL}")


if __name__ == "__main__":
    # Run pytest when executed directly
    pytest.main([__file__, "-v"])
