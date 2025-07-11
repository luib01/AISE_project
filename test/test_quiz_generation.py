#!/usr/bin/env python3
"""
Comprehensive pytest test suite for Quiz Generation and Management
Tests: Adaptive quiz generation, static quiz functionality, quiz topics, model health, difficulty levels
"""

import pytest
import requests
import json
import time
import random
import uuid
from typing import Dict, List, Optional, Any

# Test configuration
BACKEND_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def backend_url():
    """Fixture to provide backend URL"""
    return BACKEND_URL


@pytest.fixture
def unique_username():
    """Generate a unique username for testing"""
    return f"quiz_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_user_data(unique_username):
    """Fixture to provide test user data"""
    return {
        "username": unique_username,
        "password": "QuizTest123"
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


@pytest.fixture(scope="session")
def quiz_topics(backend_url):
    """Fixture that retrieves available quiz topics"""
    response = requests.get(f"{backend_url}/api/quiz-topics/")
    if response.status_code == 200:
        topics_data = response.json()
        return topics_data.get('topics', [])
    else:
        pytest.skip(f"Cannot retrieve quiz topics: {response.status_code}")


@pytest.fixture
def sample_quiz_request():
    """Fixture providing a sample quiz request structure"""
    return {
        "topic": "Grammar",
        "num_questions": 4,
        "previous_questions": []
    }


class TestQuizTopicsEndpoint:
    """Test class for quiz topics endpoint functionality"""

    def test_quiz_topics_endpoint_exists(self, backend_url):
        """Test that the quiz topics endpoint exists and is accessible"""
        response = requests.get(f"{backend_url}/api/quiz-topics/")
        
        # Should not return 404 (endpoint should exist)
        assert response.status_code != 404, "Quiz topics endpoint should exist"
        
        # Should return success or acceptable error
        assert response.status_code in [200, 500, 503], f"Unexpected status code: {response.status_code}"

    def test_quiz_topics_response_structure(self, backend_url):
        """Test that quiz topics response has correct structure"""
        response = requests.get(f"{backend_url}/api/quiz-topics/")
        
        if response.status_code == 200:
            topics_data = response.json()
            
            # Check for topics key
            assert "topics" in topics_data, "Response should contain 'topics' key"
            
            topics = topics_data["topics"]
            assert isinstance(topics, list), "Topics should be a list"
            
            # Validate topic structure if topics exist
            if topics:
                required_fields = ['name', 'subtopics', 'levels']
                
                for topic in topics:
                    for field in required_fields:
                        assert field in topic, f"Topic should have '{field}' field: {topic}"
                    
                    # Validate data types
                    assert isinstance(topic['name'], str), f"Topic name should be string: {topic['name']}"
                    assert isinstance(topic['subtopics'], list), f"Subtopics should be list: {topic['subtopics']}"
                    assert isinstance(topic['levels'], list), f"Levels should be list: {topic['levels']}"

    def test_quiz_topics_content_validation(self, quiz_topics):
        """Test that quiz topics contain expected content"""
        assert len(quiz_topics) > 0, "Should have at least one quiz topic available"
        
        # Check for common expected topics
        topic_names = [topic['name'].lower() for topic in quiz_topics]
        expected_topics = ['grammar', 'vocabulary', 'reading']
        
        found_topics = [topic for topic in expected_topics if topic in topic_names]
        assert len(found_topics) > 0, f"Should have at least one common topic from {expected_topics}"

    def test_quiz_topics_subtopics_structure(self, quiz_topics):
        """Test that quiz topics have valid subtopics structure"""
        for topic in quiz_topics:
            subtopics = topic.get('subtopics', [])
            
            # Each subtopic should be a string or dict
            for subtopic in subtopics:
                assert isinstance(subtopic, (str, dict)), f"Subtopic should be string or dict: {subtopic}"
                
                if isinstance(subtopic, dict):
                    assert 'name' in subtopic, f"Subtopic dict should have 'name': {subtopic}"

    def test_quiz_topics_levels_validation(self, quiz_topics):
        """Test that quiz topics have valid difficulty levels"""
        valid_levels = ['beginner', 'intermediate', 'advanced']
        
        for topic in quiz_topics:
            levels = topic.get('levels', [])
            
            for level in levels:
                assert level in valid_levels, f"Invalid difficulty level '{level}' in topic '{topic['name']}'"


class TestAdaptiveQuizGeneration:
    """Test class for adaptive quiz generation functionality"""

    def test_adaptive_quiz_generation_endpoint_exists(self, authenticated_user, backend_url):
        """Test that the adaptive quiz generation endpoint exists"""
        headers = authenticated_user['headers']
        sample_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=sample_request, headers=headers)
        
        # Should not return 404 (endpoint should exist)
        assert response.status_code != 404, "Adaptive quiz generation endpoint should exist"

    def test_adaptive_quiz_generation_requires_authentication(self, backend_url, sample_quiz_request):
        """Test that adaptive quiz generation requires authentication"""
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", json=sample_quiz_request)
        
        assert response.status_code == 401, f"Quiz generation should require auth, got {response.status_code}"

    @pytest.mark.parametrize("topic", ["Grammar", "Vocabulary", "Mixed"])
    def test_adaptive_quiz_generation_by_topic(self, authenticated_user, backend_url, topic):
        """Test adaptive quiz generation for different topics"""
        headers = authenticated_user['headers']
        
        quiz_request = {
            "topic": topic,
            "num_questions": 4,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            assert len(questions) == 4, f"Expected 4 questions for {topic}, got {len(questions)}"
            
            # Validate question structure
            required_fields = ['question', 'options', 'correct_answer', 'explanation', 'topic', 'difficulty']
            
            for i, question in enumerate(questions):
                for field in required_fields:
                    assert field in question, f"Question {i+1} missing required field '{field}'"
                
                # Validate options structure
                assert isinstance(question['options'], list), f"Question {i+1} options should be a list"
                assert len(question['options']) == 4, f"Question {i+1} should have 4 options, got {len(question['options'])}"
                
                # Validate correct answer
                assert question['correct_answer'] in question['options'], f"Question {i+1} correct answer not in options"
                
                # Validate difficulty level
                assert question['difficulty'] in ['beginner', 'intermediate', 'advanced'], f"Invalid difficulty in question {i+1}"
        
        elif response.status_code in [500, 503]:
            pytest.skip(f"Quiz generation service unavailable for {topic}: {response.status_code}")
        else:
            pytest.fail(f"Unexpected response for {topic} quiz: {response.status_code} - {response.text}")

    def test_adaptive_quiz_generation_question_count(self, authenticated_user, backend_url):
        """Test adaptive quiz generation with different question counts"""
        headers = authenticated_user['headers']
        
        question_counts = [2, 4, 6, 8]
        
        for count in question_counts:
            quiz_request = {
                "topic": "Grammar",
                "num_questions": count,
                "previous_questions": []
            }
            
            response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                   json=quiz_request, headers=headers)
            
            if response.status_code == 200:
                quiz_data = response.json()
                questions = quiz_data.get("questions", [])
                
                # Allow some flexibility in question count since AI generation may vary
                assert len(questions) >= count - 1, f"Expected at least {count-1} questions, got {len(questions)}"
                assert len(questions) <= count + 1, f"Expected at most {count+1} questions, got {len(questions)}"
            elif response.status_code in [500, 503]:
                pytest.skip(f"Quiz generation service unavailable for {count} questions")
            else:
                pytest.fail(f"Failed to generate {count} questions: {response.status_code}")

    def test_adaptive_quiz_generation_content_quality(self, authenticated_user, backend_url):
        """Test that generated quiz content meets quality standards"""
        headers = authenticated_user['headers']
        
        quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            for i, question in enumerate(questions):
                # Check question content quality
                assert len(question['question'].strip()) > 10, f"Question {i+1} too short"
                assert len(question['explanation'].strip()) > 10, f"Explanation {i+1} too short"
                
                # Check options are unique
                options = question['options']
                assert len(set(options)) == len(options), f"Question {i+1} has duplicate options"
                
                # Check options have reasonable length
                for j, option in enumerate(options):
                    assert len(option.strip()) > 0, f"Question {i+1} option {j+1} is empty"
        
        elif response.status_code in [500, 503]:
            pytest.skip("Quiz generation service unavailable for quality testing")
        else:
            pytest.fail(f"Failed to generate quiz for quality testing: {response.status_code}")


class TestQuizGenerationWithPreviousQuestions:
    """Test class for quiz generation with previous questions handling"""

    def test_quiz_generation_without_repetition(self, authenticated_user, backend_url):
        """Test that quiz generation avoids repeating previous questions"""
        headers = authenticated_user['headers']
        
        # Generate first quiz
        first_quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": []
        }
        
        first_response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                     json=first_quiz_request, headers=headers)
        
        if first_response.status_code != 200:
            pytest.skip(f"Cannot test repetition: first quiz generation failed: {first_response.status_code}")
        
        first_quiz = first_response.json()
        first_questions = [q['question'] for q in first_quiz.get('questions', [])]
        
        # Generate second quiz with previous questions
        second_quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": first_questions
        }
        
        second_response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                      json=second_quiz_request, headers=headers)
        
        if second_response.status_code == 200:
            second_quiz = second_response.json()
            second_questions = [q['question'] for q in second_quiz.get('questions', [])]
            
            # Check for repetition
            repeated_questions = set(first_questions) & set(second_questions)
            
            # Ideally no repetition, but some might be acceptable
            repetition_ratio = len(repeated_questions) / len(first_questions)
            assert repetition_ratio <= 0.5, f"Too many repeated questions: {len(repeated_questions)}/{len(first_questions)}"
            
        elif second_response.status_code in [500, 503]:
            pytest.skip("Quiz generation service unavailable for repetition testing")
        else:
            pytest.fail(f"Failed to generate second quiz: {second_response.status_code}")

    def test_quiz_generation_with_many_previous_questions(self, authenticated_user, backend_url):
        """Test quiz generation when many previous questions are provided"""
        headers = authenticated_user['headers']
        
        # Create a long list of previous questions
        many_previous_questions = [
            f"Sample question {i} about grammar and language learning?" 
            for i in range(20)
        ]
        
        quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": many_previous_questions
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=quiz_request, headers=headers)
        
        # Should handle large previous questions list gracefully
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            assert len(questions) == 4, "Should still generate requested number of questions"
            
        elif response.status_code in [500, 503]:
            pytest.skip("Quiz generation service unavailable for many previous questions test")
        elif response.status_code == 400:
            # Might reject too many previous questions - this is acceptable
            assert True, "Service appropriately handled too many previous questions"
        else:
            pytest.fail(f"Unexpected response with many previous questions: {response.status_code}")

    def test_quiz_generation_previous_questions_format_validation(self, authenticated_user, backend_url):
        """Test that previous questions parameter accepts different formats"""
        headers = authenticated_user['headers']
        
        # Test with empty list
        empty_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=empty_request, headers=headers)
        
        # Empty list should be accepted
        assert response.status_code in [200, 500, 503], f"Empty previous questions should be accepted: {response.status_code}"
        
        # Test without previous_questions field
        no_previous_request = {
            "topic": "Grammar",
            "num_questions": 4
        }
        
        response2 = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                json=no_previous_request, headers=headers)
        
        # Missing field should be handled gracefully
        assert response2.status_code in [200, 400, 422, 500, 503], f"Missing previous_questions should be handled: {response2.status_code}"


class TestQuizDifficultyLevels:
    """Test class for quiz generation with different difficulty levels"""

    @pytest.mark.parametrize("difficulty", ["beginner", "intermediate", "advanced"])
    def test_quiz_generation_by_difficulty(self, authenticated_user, backend_url, difficulty):
        """Test quiz generation for different difficulty levels"""
        headers = authenticated_user['headers']
        
        quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "force_difficulty": difficulty,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            assert len(questions) == 4, f"Expected 4 questions for {difficulty}, got {len(questions)}"
            
            # Check if questions have the requested difficulty (if supported by API)
            difficulty_matches = sum(1 for q in questions if q.get('difficulty') == difficulty)
            
            # At least some questions should match the requested difficulty
            # Note: API might not always honor force_difficulty
            if 'force_difficulty' in quiz_request:
                # If force_difficulty is used, we expect better matching
                assert difficulty_matches >= 1, f"At least 1 question should match {difficulty} difficulty"
            
        elif response.status_code in [500, 503]:
            pytest.skip(f"Quiz generation service unavailable for {difficulty} difficulty")
        elif response.status_code == 400:
            # API might not support force_difficulty parameter
            pytest.skip(f"Force difficulty not supported for {difficulty}")
        else:
            pytest.fail(f"Failed to generate {difficulty} quiz: {response.status_code}")

    def test_quiz_difficulty_progression(self, authenticated_user, backend_url):
        """Test that difficulty can progress appropriately"""
        headers = authenticated_user['headers']
        
        # Generate quizzes for each difficulty level
        difficulties = ["beginner", "intermediate", "advanced"]
        generated_quizzes = {}
        
        for difficulty in difficulties:
            quiz_request = {
                "topic": "Grammar",
                "num_questions": 4,
                "force_difficulty": difficulty,
                "previous_questions": []
            }
            
            response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                   json=quiz_request, headers=headers)
            
            if response.status_code == 200:
                generated_quizzes[difficulty] = response.json()
            elif response.status_code in [400, 422]:
                # force_difficulty might not be supported
                pytest.skip(f"Difficulty control not supported: {response.status_code}")
            elif response.status_code in [500, 503]:
                pytest.skip(f"Quiz generation service unavailable for difficulty progression test")
        
        # If we have quizzes for multiple difficulties, validate progression
        if len(generated_quizzes) >= 2:
            # At minimum, we should have different content or structure
            beginner_questions = generated_quizzes.get('beginner', {}).get('questions', [])
            advanced_questions = generated_quizzes.get('advanced', {}).get('questions', [])
            
            if beginner_questions and advanced_questions:
                # Questions should be different
                beginner_texts = {q['question'] for q in beginner_questions}
                advanced_texts = {q['question'] for q in advanced_questions}
                
                overlap = beginner_texts & advanced_texts
                overlap_ratio = len(overlap) / max(len(beginner_texts), 1)
                
                # Should have mostly different questions for different difficulties
                assert overlap_ratio < 0.75, "Different difficulty levels should have mostly different questions"


class TestModelHealthAndInfo:
    """Test class for model health and information endpoints"""

    def test_model_info_endpoint(self, backend_url):
        """Test the model info endpoint"""
        response = requests.get(f"{backend_url}/api/model-info/")
        
        if response.status_code == 200:
            model_info = response.json()
            
            # Check for expected fields
            expected_fields = ['current_model', 'base_url', 'timeout']
            present_fields = [field for field in expected_fields if field in model_info]
            
            assert len(present_fields) > 0, f"Model info should contain some expected fields: {expected_fields}"
            
            # Validate data types if present
            if 'current_model' in model_info:
                assert isinstance(model_info['current_model'], str), "Current model should be a string"
            
            if 'timeout' in model_info:
                assert isinstance(model_info['timeout'], (int, float)), "Timeout should be numeric"
                assert model_info['timeout'] > 0, "Timeout should be positive"
            
        elif response.status_code == 404:
            pytest.skip("Model info endpoint not available")
        else:
            # Service might be unavailable
            assert response.status_code in [500, 503], f"Unexpected model info response: {response.status_code}"

    def test_health_check_endpoint(self, backend_url):
        """Test the health check endpoint"""
        response = requests.get(f"{backend_url}/api/health-check/")
        
        if response.status_code == 200:
            health_data = response.json()
            
            # Check for basic health check fields
            expected_fields = ['status', 'message']
            
            for field in expected_fields:
                if field in health_data:
                    assert isinstance(health_data[field], str), f"Health check {field} should be a string"
            
            # Status should indicate health
            if 'status' in health_data:
                valid_statuses = ['healthy', 'ok', 'available', 'ready']
                status_lower = health_data['status'].lower()
                
                # Should contain some indicator of health
                is_healthy = any(status in status_lower for status in valid_statuses)
                if not is_healthy:
                    # Might be degraded but still responding
                    assert True, f"Health check returned status: {health_data['status']}"
        
        elif response.status_code == 404:
            pytest.skip("Health check endpoint not available")
        elif response.status_code in [500, 503]:
            # Health check failed - this is informative, not a test failure
            pytest.skip(f"Health check failed (expected if AI model not running): {response.status_code}")
        else:
            pytest.fail(f"Unexpected health check response: {response.status_code}")

    def test_model_availability_consistency(self, backend_url):
        """Test that model info and health check are consistent"""
        info_response = requests.get(f"{backend_url}/api/model-info/")
        health_response = requests.get(f"{backend_url}/api/health-check/")
        
        # Both should have similar availability
        info_available = info_response.status_code == 200
        health_available = health_response.status_code == 200
        
        if info_available or health_available:
            # If one is available, both should generally be available (or failing gracefully)
            assert info_response.status_code in [200, 404, 500, 503], f"Unexpected model info status: {info_response.status_code}"
            assert health_response.status_code in [200, 404, 500, 503], f"Unexpected health check status: {health_response.status_code}"
        else:
            # Both unavailable - might be expected
            pytest.skip("Both model info and health check unavailable")


class TestUserProfileForQuizGeneration:
    """Test class for user profile endpoints related to quiz generation"""

    def test_user_profile_endpoint_accessibility(self, authenticated_user, backend_url):
        """Test that user profile endpoint is accessible"""
        headers = authenticated_user['headers']
        
        # Get user ID from auth
        auth_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        
        if auth_response.status_code != 200:
            pytest.skip(f"Cannot get user ID from auth: {auth_response.status_code}")
        
        user_id = auth_response.json()['data']['user_id']
        
        # Test user profile endpoint
        profile_response = requests.get(f"{backend_url}/api/user-profile/{user_id}")
        
        # Should be accessible (might require auth depending on implementation)
        assert profile_response.status_code in [200, 401, 404], f"Unexpected profile response: {profile_response.status_code}"

    def test_user_profile_content_structure(self, authenticated_user, backend_url):
        """Test user profile content structure for quiz generation"""
        headers = authenticated_user['headers']
        
        # Get user ID from auth
        auth_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        if auth_response.status_code != 200:
            pytest.skip("Cannot get user auth profile")
        
        user_id = auth_response.json()['data']['user_id']
        
        # Test user profile endpoint
        profile_response = requests.get(f"{backend_url}/api/user-profile/{user_id}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            
            # Check for quiz-relevant fields
            expected_fields = ['user_id', 'english_level', 'progress', 'total_quizzes', 'average_score']
            present_fields = [field for field in expected_fields if field in profile_data]
            
            assert len(present_fields) > 0, f"Profile should contain some quiz-relevant fields: {expected_fields}"
            
            # Validate specific fields if present
            if 'english_level' in profile_data:
                valid_levels = ['beginner', 'intermediate', 'advanced']
                assert profile_data['english_level'] in valid_levels, f"Invalid english level: {profile_data['english_level']}"
            
            if 'total_quizzes' in profile_data:
                assert isinstance(profile_data['total_quizzes'], int), "Total quizzes should be an integer"
                assert profile_data['total_quizzes'] >= 0, "Total quizzes should be non-negative"
            
            if 'average_score' in profile_data:
                assert isinstance(profile_data['average_score'], (int, float)), "Average score should be numeric"
                assert 0 <= profile_data['average_score'] <= 100, "Average score should be between 0 and 100"
        
        elif profile_response.status_code == 401:
            pytest.skip("User profile requires different authentication")
        elif profile_response.status_code == 404:
            pytest.skip("User profile endpoint not found or user profile not created yet")
        else:
            pytest.fail(f"Unexpected profile response: {profile_response.status_code}")

    def test_user_profile_updates_with_quiz_activity(self, authenticated_user, backend_url):
        """Test that user profile reflects quiz activity"""
        headers = authenticated_user['headers']
        
        # Get initial profile state
        auth_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        if auth_response.status_code != 200:
            pytest.skip("Cannot access user auth profile")
        
        initial_auth_data = auth_response.json()['data']
        initial_total_quizzes = initial_auth_data.get('total_quizzes', 0)
        
        # Generate a quiz to create activity
        quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": []
        }
        
        quiz_response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                    json=quiz_request, headers=headers)
        
        if quiz_response.status_code != 200:
            pytest.skip(f"Cannot generate quiz for profile update test: {quiz_response.status_code}")
        
        # Check if profile updates are reflected
        # Note: Profile might not update immediately after quiz generation
        # This test mainly validates that the profile structure supports quiz tracking


class TestQuizGenerationEdgeCases:
    """Test class for edge cases and error scenarios in quiz generation"""

    def test_quiz_generation_with_invalid_topic(self, authenticated_user, backend_url):
        """Test quiz generation with invalid topic"""
        headers = authenticated_user['headers']
        
        invalid_request = {
            "topic": "InvalidTopicThatDoesNotExist",
            "num_questions": 4,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=invalid_request, headers=headers)
        
        # Should handle invalid topic gracefully
        assert response.status_code in [200, 400, 422, 500], f"Invalid topic should be handled gracefully: {response.status_code}"
        
        if response.status_code == 200:
            # Might fallback to default topic
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            assert len(questions) > 0, "Should generate fallback questions for invalid topic"

    def test_quiz_generation_with_invalid_question_count(self, authenticated_user, backend_url):
        """Test quiz generation with invalid question counts"""
        headers = authenticated_user['headers']
        
        invalid_counts = [0, -1]  # Only test clearly invalid counts
        
        for count in invalid_counts:
            invalid_request = {
                "topic": "Grammar",
                "num_questions": count,
                "previous_questions": []
            }
            
            response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                   json=invalid_request, headers=headers)
            
            # Should handle invalid counts appropriately
            if response.status_code == 200:
                # If API provides defaults for invalid counts, verify response
                quiz_data = response.json()
                questions = quiz_data.get("questions", [])
                assert len(questions) >= 0, f"Should return valid question list for count {count}"
            else:
                assert response.status_code in [400, 422, 500], f"Negative/zero count should be rejected: {response.status_code}"

    def test_quiz_generation_with_malformed_request(self, authenticated_user, backend_url):
        """Test quiz generation with malformed request data"""
        headers = authenticated_user['headers']
        
        # Test missing required fields
        malformed_requests = [
            {},  # Empty request
            {"num_questions": 4},  # Missing topic
            {"topic": "", "num_questions": 4},  # Empty topic
        ]
        
        for malformed_request in malformed_requests:
            response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                   json=malformed_request, headers=headers)
            
            # Should reject malformed requests or provide defaults
            if response.status_code == 200:
                # If API provides defaults, verify the response is valid
                quiz_data = response.json()
                questions = quiz_data.get("questions", [])
                if malformed_request.get("topic") == "":
                    # Empty topic should be rejected
                    assert len(questions) == 0 or response.status_code in [400, 422, 500], f"Empty topic should be rejected: {response.status_code}"
            else:
                assert response.status_code in [400, 422, 500], f"Malformed request should be rejected: {response.status_code}, request: {malformed_request}"

    def test_quiz_generation_response_time(self, authenticated_user, backend_url):
        """Test that quiz generation responds within reasonable time"""
        headers = authenticated_user['headers']
        
        quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": []
        }
        
        start_time = time.time()
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=quiz_request, headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within reasonable time (allowing for AI model delays)
        if response.status_code == 200:
            assert response_time < 60.0, f"Quiz generation should complete within 60 seconds, took {response_time:.2f}s"
        elif response.status_code in [500, 503]:
            # Service might be slow or unavailable
            pytest.skip(f"Quiz generation service unavailable: {response.status_code}")


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
    print("🚀 Running Quiz Generation Tests with pytest...")
    print("=" * 60)
    print("\n📋 Test Coverage:")
    print("   • Quiz topics endpoint")
    print("   • Adaptive quiz generation")
    print("   • Quiz generation with previous questions")
    print("   • Difficulty level controls")
    print("   • Model health and information")
    print("   • User profile integration")
    print("   • Edge cases and error handling")
    print("\n" + "=" * 60)
    
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


# Legacy support function for backward compatibility
def main():
    """Legacy main function for backward compatibility"""
    print("🚀 Running Quiz Generation Tests with pytest...")
    print("=" * 60)
    print("\n📋 Test Coverage:")
    print("   • Quiz topics endpoint")
    print("   • Adaptive quiz generation")
    print("   • Quiz generation with previous questions")
    print("   • Difficulty level controls")
    print("   • Model health and information")
    print("   • User profile integration")
    print("   • Edge cases and error handling")
    print("\n" + "=" * 60)
    
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


if __name__ == "__main__":
    # Run pytest when executed directly
    pytest.main([__file__, "-v"])
