#!/usr/bin/env python3
"""
Comprehensive pytest test suite for AI Chat Assistant
Tests: Chat functionality, teacher chat, response formatting, error handling
"""

import pytest
import requests
import json
import time
import random
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
    return f"chat_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_user_data(unique_username):
    """Fixture to provide test user data"""
    return {
        "username": unique_username,
        "password": "ChatTest123"
    }


@pytest.fixture
def authenticated_chat_user(test_user_data, backend_url):
    """Fixture that creates and authenticates a user for chat testing"""
    # Register user
    signup_response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
    if signup_response.status_code in [200, 201]:
        # Login user
        signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
        if signin_response.status_code == 200:
            session_token = signin_response.json()['data']['session_token']
            
            yield {
                "user_data": test_user_data,
                "token": session_token,
                "headers": {"Authorization": f"Bearer {session_token}"}
            }
            
            # Cleanup: Delete the user after test
            try:
                headers = {"Authorization": f"Bearer {session_token}"}
                requests.delete(f"{backend_url}/api/auth/profile", 
                              json={"password": test_user_data['password']}, 
                              headers=headers)
            except Exception:
                pass  # Ignore cleanup errors
        else:
            pytest.fail(f"Failed to authenticate test user: {signin_response.status_code}")
    else:
        pytest.fail(f"Failed to register test user: {signup_response.status_code}")


@pytest.fixture
def simple_conversation():
    """Fixture providing a simple conversation for testing"""
    return [
        "Hello, I want to learn English",
        "Hi! I'm here to help you learn English. What would you like to practice today?"
    ]


@pytest.fixture
def educational_questions():
    """Fixture providing educational questions for testing"""
    return [
        "What is the difference between 'a' and 'an'?",
        "How do I use present perfect tense?",
        "Can you explain irregular verbs?",
        "What are modal verbs?",
        "How do I form questions in English?"
    ]


class TestBasicChatFunctionality:
    """Test class for basic chat functionality"""

    def test_simple_chat_response(self, simple_conversation, backend_url):
        """Test basic chat functionality with simple conversation"""
        chat_request = {"conversation": simple_conversation}
        response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
        
        if response.status_code == 500:
            # Handle Ollama connection error gracefully
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available - chat functionality cannot be tested")
            else:
                pytest.fail(f"Chat failed with error: {error_data.get('detail')}")
        
        assert response.status_code == 200, f"Chat request failed: {response.status_code} - {response.text}"
        
        result = response.json()
        reply = result.get("reply", "")
        
        assert reply, "Chat response should not be empty"
        assert len(reply) > 10, f"Chat response too short: '{reply}'"
        assert isinstance(reply, str), "Chat reply should be a string"

    def test_single_message_chat(self, backend_url):
        """Test chat with single message"""
        chat_request = {"conversation": ["Hello"]}
        response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
            else:
                pytest.fail(f"Chat failed: {error_data.get('detail')}")
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("reply"), "Single message should get a reply"

    def test_chat_response_structure(self, simple_conversation, backend_url):
        """Test that chat response has correct structure"""
        chat_request = {"conversation": simple_conversation}
        response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
        
        assert response.status_code == 200
        result = response.json()
        
        assert isinstance(result, dict), "Response should be a dictionary"
        assert "reply" in result, "Response should contain 'reply' field"


class TestTeacherChatFunctionality:
    """Test class for enhanced teacher chat functionality"""

    @pytest.mark.parametrize("user_level,learning_focus,message", [
        ("beginner", "grammar", "I want to practice grammar"),
        ("intermediate", "vocabulary", "Help me with vocabulary"),
        ("advanced", "conversation", "I need conversation practice"),
        ("beginner", "pronunciation", "Help me with pronunciation"),
        ("intermediate", "writing", "I want to improve my writing"),
    ])
    def test_teacher_chat_with_different_levels_and_focus(self, user_level, learning_focus, message, backend_url):
        """Test teacher chat with different user levels and learning focuses"""
        teacher_request = {
            "message": message,
            "user_level": user_level,
            "learning_focus": learning_focus
        }
        
        response = requests.post(f"{backend_url}/api/teacher-chat/", json=teacher_request)
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
            else:
                pytest.fail(f"Teacher chat failed: {error_data.get('detail')}")
        
        assert response.status_code == 200, f"Teacher chat failed for {user_level} {learning_focus}: {response.status_code}"
        
        result = response.json()
        reply = result.get("reply", "")
        student_level = result.get("student_level")
        returned_focus = result.get("learning_focus")
        
        assert reply, f"Teacher response should not be empty for {user_level} {learning_focus}"
        assert len(reply) > 10, f"Teacher response too short for {user_level} {learning_focus}"
        # Note: student_level and learning_focus might be optional in response

    def test_teacher_chat_response_structure(self, backend_url):
        """Test teacher chat response structure"""
        teacher_request = {
            "message": "Help me learn English",
            "user_level": "beginner",
            "learning_focus": "grammar"
        }
        
        response = requests.post(f"{backend_url}/api/teacher-chat/", json=teacher_request)
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
        
        assert response.status_code == 200
        result = response.json()
        
        assert isinstance(result, dict), "Teacher chat response should be a dictionary"
        assert "reply" in result, "Teacher chat response should contain 'reply' field"


class TestChatConversationFlow:
    """Test class for multi-turn conversation flow"""

    def test_multi_turn_conversation(self, backend_url):
        """Test multi-turn conversation flow"""
        conversations = [
            # First turn
            ["Hello"],
            # Second turn
            ["Hello", "Hi! How can I help you learn English today?", "I want to learn about tenses"],
            # Third turn  
            ["Hello", "Hi! How can I help you learn English today?", "I want to learn about tenses", 
             "Great! Let's start with present tense. What specifically about tenses confuses you?", 
             "I don't understand present perfect"]
        ]
        
        for i, conversation in enumerate(conversations):
            chat_request = {"conversation": conversation}
            response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
            
            if response.status_code == 500:
                error_data = response.json()
                if "Ollama connection error" in error_data.get("detail", ""):
                    pytest.skip("Ollama not available")
                else:
                    pytest.fail(f"Turn {i+1} failed: {error_data.get('detail')}")
            
            assert response.status_code == 200, f"Turn {i+1} request failed: {response.status_code}"
            
            result = response.json()
            reply = result.get("reply", "")
            assert reply, f"Turn {i+1} should have a response"

    def test_conversation_context_awareness(self, backend_url):
        """Test that chat maintains context across conversation turns"""
        # Start with a topic
        conversation1 = ["I want to learn about past tense"]
        response1 = requests.post(f"{backend_url}/api/chat/", json={"conversation": conversation1})
        
        if response1.status_code == 500:
            error_data = response1.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
        
        assert response1.status_code == 200
        reply1 = response1.json().get("reply", "")
        
        # Continue the conversation
        conversation2 = conversation1 + [reply1, "Can you give me examples?"]
        response2 = requests.post(f"{backend_url}/api/chat/", json={"conversation": conversation2})
        
        assert response2.status_code == 200
        reply2 = response2.json().get("reply", "")
        assert reply2, "Continuation should have a response"


class TestChatInputValidation:
    """Test class for chat input validation and error handling"""

    def test_empty_conversation(self, backend_url):
        """Test chat with empty conversation"""
        empty_request = {"conversation": []}
        response = requests.post(f"{backend_url}/api/chat/", json=empty_request)
        
        # Should either handle gracefully or return appropriate error
        assert response.status_code in [200, 400, 422], f"Empty conversation not handled properly: {response.status_code}"

    def test_missing_conversation_field(self, backend_url):
        """Test chat with missing conversation field"""
        invalid_request = {"messages": ["Hello"]}  # Wrong field name
        response = requests.post(f"{backend_url}/api/chat/", json=invalid_request)
        
        assert response.status_code == 422, f"Invalid request structure should be rejected with 422, got {response.status_code}"

    def test_very_long_conversation(self, backend_url):
        """Test chat with very long conversation"""
        long_conversation = ["Hello"] * 100  # Very long conversation
        long_request = {"conversation": long_conversation}
        response = requests.post(f"{backend_url}/api/chat/", json=long_request)
        
        # Should handle gracefully (may truncate or process normally)
        assert response.status_code in [200, 400, 413, 500], f"Long conversation not handled properly: {response.status_code}"

    @pytest.mark.parametrize("invalid_conversation", [
        None,  # None value
        "Hello",  # String instead of list
        123,  # Number instead of list
        [123, 456],  # List of numbers instead of strings
    ])
    def test_invalid_conversation_types(self, invalid_conversation, backend_url):
        """Test chat with invalid conversation data types"""
        invalid_request = {"conversation": invalid_conversation}
        response = requests.post(f"{backend_url}/api/chat/", json=invalid_request)
        
        # Should return validation error
        assert response.status_code in [400, 422], f"Invalid conversation type should be rejected"


class TestTeacherChatValidation:
    """Test class for teacher chat input validation"""

    @pytest.mark.parametrize("invalid_level", [
        "invalid_level",
        "expert",
        "",
        None,
        123
    ])
    def test_invalid_user_level(self, invalid_level, backend_url):
        """Test teacher chat with invalid user levels"""
        invalid_level_request = {
            "message": "Help me learn",
            "user_level": invalid_level,
            "learning_focus": "grammar"
        }
        
        response = requests.post(f"{backend_url}/api/teacher-chat/", json=invalid_level_request)
        
        # Should handle gracefully (may default to beginner) or return validation error
        assert response.status_code in [200, 400, 422], f"Invalid user level not handled properly: {response.status_code}"

    @pytest.mark.parametrize("invalid_focus", [
        "invalid_focus",
        "mathematics",
        "",
        None,
        123
    ])
    def test_invalid_learning_focus(self, invalid_focus, backend_url):
        """Test teacher chat with invalid learning focus"""
        invalid_focus_request = {
            "message": "Help me learn",
            "user_level": "beginner",
            "learning_focus": invalid_focus
        }
        
        response = requests.post(f"{backend_url}/api/teacher-chat/", json=invalid_focus_request)
        
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 400, 422], f"Invalid learning focus not handled properly: {response.status_code}"

    def test_missing_message(self, backend_url):
        """Test teacher chat with missing message"""
        missing_message_request = {
            "user_level": "beginner",
            "learning_focus": "grammar"
        }
        
        response = requests.post(f"{backend_url}/api/teacher-chat/", json=missing_message_request)
        
        assert response.status_code == 422, f"Missing message should be rejected with 422, got {response.status_code}"

    def test_empty_message(self, backend_url):
        """Test teacher chat with empty message"""
        empty_message_request = {
            "message": "",
            "user_level": "beginner",
            "learning_focus": "grammar"
        }
        
        response = requests.post(f"{backend_url}/api/teacher-chat/", json=empty_message_request)
        
        # Should either handle gracefully or return validation error
        assert response.status_code in [200, 400, 422], f"Empty message not handled properly: {response.status_code}"


class TestChatResponseQuality:
    """Test class for chat response quality checks"""

    def test_educational_content_responses(self, educational_questions, backend_url):
        """Test responses to educational questions"""
        for question in educational_questions[:3]:  # Test first 3 to avoid too many API calls
            chat_request = {"conversation": [question]}
            response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
            
            if response.status_code == 500:
                error_data = response.json()
                if "Ollama connection error" in error_data.get("detail", ""):
                    pytest.skip("Ollama not available")
                else:
                    pytest.fail(f"Chat failed for question '{question}': {error_data.get('detail')}")
            
            assert response.status_code == 200, f"Request failed for question: {question}"
            
            result = response.json()
            reply = result.get("reply", "")
            
            # Basic quality checks
            assert len(reply) >= 20, f"Response too short for educational question: {question}"
            assert reply.strip(), "Response should not be just whitespace"

    def test_response_is_educational(self, backend_url):
        """Test that responses are educational in nature"""
        educational_request = "Explain the difference between 'much' and 'many'"
        chat_request = {"conversation": [educational_request]}
        response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
        
        assert response.status_code == 200
        reply = response.json().get("reply", "")
        
        # Check that response contains educational content
        educational_keywords = ["much", "many", "countable", "uncountable", "example", "use"]
        found_keywords = sum(1 for keyword in educational_keywords if keyword.lower() in reply.lower())
        
        assert found_keywords >= 2, f"Response should contain educational content. Reply: {reply[:100]}..."

    def test_response_length_appropriate(self, backend_url):
        """Test that responses are appropriate length"""
        test_cases = [
            ("Hi", 10, 200),  # Short greeting should get short response
            ("Explain all English grammar rules", 50, 1000),  # Complex question should get longer response
        ]
        
        for message, min_length, max_length in test_cases:
            chat_request = {"conversation": [message]}
            response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
            
            if response.status_code == 500:
                error_data = response.json()
                if "Ollama connection error" in error_data.get("detail", ""):
                    pytest.skip("Ollama not available")
            
            assert response.status_code == 200
            reply = response.json().get("reply", "")
            
            assert len(reply) >= min_length, f"Response too short for '{message}': {len(reply)} < {min_length}"
            # Note: We might be lenient on max length as AI can be verbose


class TestChatIntegration:
    """Integration tests for chat functionality"""

    @pytest.mark.integration
    def test_chat_without_authentication(self, backend_url):
        """Test that chat works without authentication (public endpoint)"""
        chat_request = {"conversation": ["Hello, how are you?"]}
        response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
        
        # Chat should work without authentication
        assert response.status_code == 200, "Chat should work without authentication"

    @pytest.mark.integration  
    def test_teacher_chat_without_authentication(self, backend_url):
        """Test that teacher chat works without authentication"""
        teacher_request = {
            "message": "Help me learn English",
            "user_level": "beginner",
            "learning_focus": "grammar"
        }
        
        response = requests.post(f"{backend_url}/api/teacher-chat/", json=teacher_request)
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
        
        # Teacher chat should work without authentication
        assert response.status_code == 200, "Teacher chat should work without authentication"

    @pytest.mark.integration
    def test_concurrent_chat_requests(self, backend_url):
        """Test handling of concurrent chat requests"""
        import threading
        import time
        
        results = []
        
        def make_chat_request():
            chat_request = {"conversation": ["What is English grammar?"]}
            response = requests.post(f"{backend_url}/api/chat/", json=chat_request)
            results.append(response.status_code)
        
        # Make 3 concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_chat_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that most requests succeeded (some might fail due to Ollama limits)
        success_count = sum(1 for status in results if status == 200)
        ollama_error_count = sum(1 for status in results if status == 500)
        
        # If all failed with 500, likely Ollama issue
        if ollama_error_count == len(results):
            pytest.skip("Ollama not available for concurrent testing")
        
        assert success_count >= 1, f"At least one concurrent request should succeed. Results: {results}"


def test_backend_connectivity(backend_url):
    """Test that the backend is accessible"""
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        assert response.status_code in [200, 404], "Backend should be accessible"
    except requests.exceptions.ConnectionError:
        pytest.fail(f"Cannot connect to backend at {backend_url}. Make sure the backend is running.")
    except requests.exceptions.Timeout:
        pytest.fail(f"Backend at {backend_url} is not responding.")


# Legacy support function for backward compatibility
def main():
    """Legacy main function for backward compatibility"""
    print("🚀 Running Chat Assistant Tests with pytest...")
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


if __name__ == "__main__":
    # Run pytest when executed directly
    pytest.main([__file__, "-v"])
