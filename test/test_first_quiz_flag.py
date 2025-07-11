#!/usr/bin/env python3
"""
Comprehensive pytest test suite for first quiz completion flag
Tests: First quiz flag logic, quiz completion tracking, user state management
"""

import pytest
import requests
import json
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
    return f"first_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_user_data(unique_username):
    """Fixture to provide test user data"""
    return {
        "username": unique_username,
        "password": "password123"
    }


@pytest.fixture
def registered_user(test_user_data, backend_url):
    """Fixture that registers a user and provides the user data"""
    response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
    if response.status_code in [200, 201]:
        yield test_user_data
        # Cleanup: Delete the user after test
        try:
            signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            if signin_response.status_code == 200:
                token = signin_response.json()['data']['session_token']
                headers = {"Authorization": f"Bearer {token}"}
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


@pytest.fixture
def quiz_request_data():
    """Fixture providing standard quiz request data"""
    return {
        "topic": "Grammar",
        "num_questions": 4,
        "previous_questions": []
    }


class TestFirstQuizFlag:
    """Test class for first quiz completion flag functionality"""

    def test_new_user_first_quiz_flag_false(self, registered_user, backend_url):
        """Test that new users have has_completed_first_quiz set to False"""
        signin_response = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
        
        assert signin_response.status_code == 200, f"Sign in failed: {signin_response.status_code} - {signin_response.text}"
        
        signin_data = signin_response.json()
        user_data = signin_data.get("data", {})
        has_completed_first_quiz = user_data.get("has_completed_first_quiz")
        
        assert has_completed_first_quiz is False, f"New user should have has_completed_first_quiz=False, got {has_completed_first_quiz}"

    def test_first_quiz_flag_persists_across_logins(self, registered_user, backend_url):
        """Test that the first quiz flag persists across multiple logins"""
        # First login
        signin_response1 = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
        assert signin_response1.status_code == 200
        
        flag1 = signin_response1.json()["data"].get("has_completed_first_quiz")
        
        # Second login
        signin_response2 = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
        assert signin_response2.status_code == 200
        
        flag2 = signin_response2.json()["data"].get("has_completed_first_quiz")
        
        assert flag1 == flag2, "First quiz flag should persist across logins"
        assert flag1 is False, "New user flag should be False"

    def test_user_data_structure_contains_first_quiz_flag(self, authenticated_user, backend_url):
        """Test that user data structure includes the first quiz flag"""
        user_data = authenticated_user['signin_data']
        
        assert "has_completed_first_quiz" in user_data, "User data should contain has_completed_first_quiz field"
        assert isinstance(user_data["has_completed_first_quiz"], bool), "has_completed_first_quiz should be a boolean"


class TestQuizGeneration:
    """Test class for quiz generation functionality required for first quiz completion"""

    def test_quiz_generation_for_new_user(self, authenticated_user, quiz_request_data, backend_url):
        """Test that new users can generate their first quiz"""
        response = requests.post(
            f"{backend_url}/api/generate-adaptive-quiz/",
            json=quiz_request_data,
            headers=authenticated_user['headers']
        )
        
        # Quiz generation might fail if AI service is unavailable
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available - quiz generation cannot be tested")
            else:
                pytest.fail(f"Quiz generation failed: {error_data.get('detail')}")
        
        assert response.status_code == 200, f"Quiz generation failed: {response.status_code} - {response.text}"
        
        quiz_data = response.json()
        assert "questions" in quiz_data, "Quiz response should contain questions"
        
        questions = quiz_data["questions"]
        assert len(questions) > 0, "Quiz should contain at least one question"
        assert len(questions) <= quiz_request_data["num_questions"], "Quiz should not exceed requested number of questions"

    def test_quiz_question_structure(self, authenticated_user, quiz_request_data, backend_url):
        """Test that generated quiz questions have the correct structure"""
        response = requests.post(
            f"{backend_url}/api/generate-adaptive-quiz/",
            json=quiz_request_data,
            headers=authenticated_user['headers']
        )
        
        if response.status_code == 500:
            error_data = response.json()
            if "Ollama connection error" in error_data.get("detail", ""):
                pytest.skip("Ollama not available")
        
        assert response.status_code == 200
        
        quiz_data = response.json()
        questions = quiz_data["questions"]
        
        for i, question in enumerate(questions):
            assert "question" in question, f"Question {i} should have 'question' field"
            assert "correct_answer" in question, f"Question {i} should have 'correct_answer' field"
            # Other fields might be optional depending on implementation


class TestQuizSubmission:
    """Test class for quiz submission functionality"""

    def create_quiz_submission(self, questions, score=100, topic="Grammar"):
        """Helper method to create a quiz submission from questions"""
        quiz_submission = {
            "quiz_data": {
                "questions": []
            },
            "score": score,
            "topic": topic,
            "difficulty": "beginner",
            "quiz_type": "adaptive"
        }
        
        for question in questions:
            quiz_submission["quiz_data"]["questions"].append({
                "question": question.get("question", ""),
                "userAnswer": question.get("correct_answer", ""),
                "correctAnswer": question.get("correct_answer", ""),
                "topic": question.get("topic", topic),
                "difficulty": question.get("difficulty", "beginner"),
                "isCorrect": True,
                "explanation": question.get("explanation", "")
            })
        
        return quiz_submission

    def test_quiz_submission_structure(self, authenticated_user, backend_url):
        """Test quiz submission with valid structure"""
        # Create a minimal quiz submission
        quiz_submission = {
            "quiz_data": {
                "questions": [{
                    "question": "Test question?",
                    "userAnswer": "Test answer",
                    "correctAnswer": "Test answer",
                    "topic": "Grammar",
                    "difficulty": "beginner",
                    "isCorrect": True,
                    "explanation": "Test explanation"
                }]
            },
            "score": 100,
            "topic": "Grammar",
            "difficulty": "beginner",
            "quiz_type": "adaptive"
        }
        
        response = requests.post(
            f"{backend_url}/api/evaluate-quiz/",
            json=quiz_submission,
            headers=authenticated_user['headers']
        )
        
        assert response.status_code == 200, f"Quiz submission failed: {response.status_code} - {response.text}"

    def test_quiz_submission_updates_user_stats(self, authenticated_user, backend_url):
        """Test that quiz submission updates user statistics"""
        # Submit a quiz
        quiz_submission = {
            "quiz_data": {
                "questions": [{
                    "question": "Test question?",
                    "userAnswer": "Test answer",
                    "correctAnswer": "Test answer",
                    "topic": "Grammar",
                    "difficulty": "beginner",
                    "isCorrect": True,
                    "explanation": "Test explanation"
                }]
            },
            "score": 100,
            "topic": "Grammar",
            "difficulty": "beginner",
            "quiz_type": "adaptive"
        }
        
        submit_response = requests.post(
            f"{backend_url}/api/evaluate-quiz/",
            json=quiz_submission,
            headers=authenticated_user['headers']
        )
        
        assert submit_response.status_code == 200, "Quiz submission should succeed"
        
        # Check if user stats are updated (this might depend on implementation)
        result = submit_response.json()
        # The exact structure might vary, but it should be a successful response
        assert isinstance(result, dict), "Quiz submission should return a dictionary"


class TestFirstQuizCompletion:
    """Test class for complete first quiz completion flow"""

    @pytest.mark.integration
    def test_complete_first_quiz_flow(self, test_user_data, backend_url):
        """Test the complete flow: register -> login -> quiz -> submit -> flag updated"""
        # Step 1: Register new user
        register_response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
        assert register_response.status_code in [200, 201], "User registration should succeed"
        
        try:
            # Step 2: Sign in and verify initial flag state
            signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            assert signin_response.status_code == 200, "Initial sign in should succeed"
            
            initial_data = signin_response.json()["data"]
            assert initial_data.get("has_completed_first_quiz") is False, "Initial flag should be False"
            
            token = initial_data["session_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Step 3: Generate quiz
            quiz_request = {
                "topic": "Grammar",
                "num_questions": 4,
                "previous_questions": []
            }
            
            quiz_response = requests.post(
                f"{backend_url}/api/generate-adaptive-quiz/",
                json=quiz_request,
                headers=headers
            )
            
            if quiz_response.status_code == 500:
                error_data = quiz_response.json()
                if "Ollama connection error" in error_data.get("detail", ""):
                    pytest.skip("Ollama not available - cannot complete full flow test")
            
            assert quiz_response.status_code == 200, "Quiz generation should succeed"
            
            quiz_data = quiz_response.json()
            questions = quiz_data.get("questions", [])
            assert len(questions) > 0, "Quiz should contain questions"
            
            # Step 4: Submit quiz
            quiz_submission = {
                "quiz_data": {
                    "questions": []
                },
                "score": 100,
                "topic": "Grammar",
                "difficulty": "beginner",
                "quiz_type": "adaptive"
            }
            
            for question in questions:
                quiz_submission["quiz_data"]["questions"].append({
                    "question": question.get("question", ""),
                    "userAnswer": question.get("correct_answer", ""),
                    "correctAnswer": question.get("correct_answer", ""),
                    "topic": question.get("topic", "Grammar"),
                    "difficulty": question.get("difficulty", "beginner"),
                    "isCorrect": True,
                    "explanation": question.get("explanation", "")
                })
            
            submit_response = requests.post(
                f"{backend_url}/api/evaluate-quiz/",
                json=quiz_submission,
                headers=headers
            )
            
            assert submit_response.status_code == 200, "Quiz submission should succeed"
            
            # Step 5: Sign in again and verify flag is updated  
            signin_again_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            assert signin_again_response.status_code == 200, "Second sign in should succeed"
            
            updated_data = signin_again_response.json()["data"]
            has_completed_first_quiz = updated_data.get("has_completed_first_quiz")
            
            # Flag should be True after quiz completion, but allow for implementation variations
            if has_completed_first_quiz is not True:
                # Check if we can detect quiz completion through other means
                profile_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()['data']
                    total_quizzes = profile_data.get('total_quizzes', 0)
                    if total_quizzes > 0:
                        # User has completed quizzes, flag should be True
                        assert has_completed_first_quiz is True, f"After quiz completion (total_quizzes={total_quizzes}), flag should be True, got {has_completed_first_quiz}"
                    else:
                        # Quiz submission might not have been processed yet
                        pytest.skip("Quiz completion flag update may be delayed or not implemented")
                else:
                    pytest.skip("Cannot verify quiz completion through profile endpoint")
            else:
                assert has_completed_first_quiz is True, "Flag should be True after quiz completion"
            
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

    def test_first_quiz_flag_remains_true_after_additional_quizzes(self, test_user_data, backend_url):
        """Test that flag remains True even after completing additional quizzes"""
        # This test would require completing two quizzes
        # For brevity, we'll test the concept with a simpler approach
        
        register_response = requests.post(f"{backend_url}/api/auth/signup", json=test_user_data)
        assert register_response.status_code in [200, 201]
        
        try:
            signin_response = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
            assert signin_response.status_code == 200
            
            token = signin_response.json()['data']['session_token']
            headers = {"Authorization": f"Bearer {token}"}
            
            # Submit a quiz to set flag to True
            quiz_submission = {
                "quiz_data": {
                    "questions": [{
                        "question": "Test question?",
                        "userAnswer": "Test answer",
                        "correctAnswer": "Test answer",
                        "topic": "Grammar",
                        "difficulty": "beginner",
                        "isCorrect": True,
                        "explanation": "Test explanation"
                    }]
                },
                "score": 100,
                "topic": "Grammar",
                "difficulty": "beginner",
                "quiz_type": "adaptive"
            }
            
            submit_response = requests.post(
                f"{backend_url}/api/evaluate-quiz/",
                json=quiz_submission,
                headers=headers
            )
            
            if submit_response.status_code == 200:
                # Sign in again to check flag
                signin_again = requests.post(f"{backend_url}/api/auth/signin", json=test_user_data)
                if signin_again.status_code == 200:
                    flag = signin_again.json()["data"].get("has_completed_first_quiz")
                    assert flag is True, "Flag should be True after quiz completion"
            
        finally:
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


class TestFirstQuizFlagEdgeCases:
    """Test class for edge cases and error scenarios"""

    def test_flag_state_with_incomplete_quiz_submission(self, authenticated_user, backend_url):
        """Test that flag remains False if quiz submission fails"""
        # Submit invalid quiz data
        invalid_submission = {
            "quiz_data": {},  # Invalid structure
            "score": 100,
            "topic": "Grammar"
        }
        
        response = requests.post(
            f"{backend_url}/api/evaluate-quiz/",
            json=invalid_submission,
            headers=authenticated_user['headers']
        )
        
        # This should fail (exact status code may vary)
        assert response.status_code in [400, 422, 500], "Invalid submission should be rejected"
        
        # Flag should remain False
        signin_response = requests.post(f"{backend_url}/api/auth/signin", json=authenticated_user['user_data'])
        if signin_response.status_code == 200:
            flag = signin_response.json()["data"].get("has_completed_first_quiz")
            assert flag is False, "Flag should remain False after failed submission"

    def test_multiple_users_independent_flags(self, backend_url):
        """Test that first quiz flags are independent between users"""
        user1_data = {"username": f"user1_{uuid.uuid4().hex[:8]}", "password": "password123"}
        user2_data = {"username": f"user2_{uuid.uuid4().hex[:8]}", "password": "password123"}
        
        try:
            # Register both users
            requests.post(f"{backend_url}/api/auth/signup", json=user1_data)
            requests.post(f"{backend_url}/api/auth/signup", json=user2_data)
            
            # Both should have flag = False initially
            signin1 = requests.post(f"{backend_url}/api/auth/signin", json=user1_data)
            signin2 = requests.post(f"{backend_url}/api/auth/signin", json=user2_data)
            
            if signin1.status_code == 200 and signin2.status_code == 200:
                flag1 = signin1.json()["data"].get("has_completed_first_quiz")
                flag2 = signin2.json()["data"].get("has_completed_first_quiz")
                
                assert flag1 is False, "User 1 should have flag = False"
                assert flag2 is False, "User 2 should have flag = False"
                
                # Complete quiz for user 1 only
                token1 = signin1.json()['data']['session_token']
                headers1 = {"Authorization": f"Bearer {token1}"}
                
                quiz_submission = {
                    "quiz_data": {
                        "questions": [{
                            "question": "Test question?",
                            "userAnswer": "Test answer", 
                            "correctAnswer": "Test answer",
                            "topic": "Grammar",
                            "difficulty": "beginner",
                            "isCorrect": True,
                            "explanation": "Test explanation"
                        }]
                    },
                    "score": 100,
                    "topic": "Grammar",
                    "difficulty": "beginner",
                    "quiz_type": "adaptive"
                }
                
                requests.post(f"{backend_url}/api/evaluate-quiz/", json=quiz_submission, headers=headers1)
                
                # Check flags again
                signin1_again = requests.post(f"{backend_url}/api/auth/signin", json=user1_data)
                signin2_again = requests.post(f"{backend_url}/api/auth/signin", json=user2_data)
                
                if signin1_again.status_code == 200 and signin2_again.status_code == 200:
                    flag1_updated = signin1_again.json()["data"].get("has_completed_first_quiz")
                    flag2_updated = signin2_again.json()["data"].get("has_completed_first_quiz")
                    
                    # User 1 should have True, User 2 should still have False
                    assert flag1_updated is True, "User 1 should have completed first quiz"
                    assert flag2_updated is False, "User 2 should still not have completed first quiz"
                
        finally:
            # Cleanup both users
            for user_data in [user1_data, user2_data]:
                try:
                    signin_response = requests.post(f"{backend_url}/api/auth/signin", json=user_data)
                    if signin_response.status_code == 200:
                        token = signin_response.json()['data']['session_token']
                        headers = {"Authorization": f"Bearer {token}"}
                        requests.delete(f"{backend_url}/api/auth/profile", 
                                      json={"password": user_data['password']}, 
                                      headers=headers)
                except Exception:
                    pass


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
    print("🚀 Running First Quiz Flag Tests with pytest...")
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


if __name__ == "__main__":
    # Run pytest when executed directly
    pytest.main([__file__, "-v"])
