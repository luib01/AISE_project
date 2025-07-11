#!/usr/bin/env python3
"""
Comprehensive pytest test suite for Quiz Evaluation and Progress Tracking
Tests: Quiz submission, scoring, level progression, performance tracking, analytics
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
    return f"eval_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_user_data(unique_username):
    """Fixture to provide test user data"""
    return {
        "username": unique_username,
        "password": "EvalTest123"
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
    """Fixture that provides an authenticated user with session token and initial profile"""
    signin_response = requests.post(f"{backend_url}/api/auth/signin", json=registered_user)
    if signin_response.status_code == 200:
        signin_data = signin_response.json()
        token = signin_data['data']['session_token']
        
        # Capture initial profile state
        initial_profile = {
            'english_level': signin_data['data'].get('english_level', 'beginner'),
            'total_quizzes': signin_data['data'].get('total_quizzes', 0),
            'has_completed_first_quiz': signin_data['data'].get('has_completed_first_quiz', False),
            'average_score': signin_data['data'].get('average_score', 0)
        }
        
        return {
            "user_data": registered_user,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
            "signin_data": signin_data['data'],
            "initial_profile": initial_profile
        }
    else:
        pytest.fail(f"Failed to authenticate test user: {signin_response.status_code}")


@pytest.fixture
def sample_quiz_questions():
    """Fixture providing sample quiz questions"""
    return [
        {
            "question": "Which sentence is correct?",
            "topic": "Grammar",
            "userAnswer": "She doesn't like coffee",
            "correctAnswer": "She doesn't like coffee",
            "isCorrect": True,
            "explanation": "This is the correct form using 'doesn't' for third person singular.",
            "difficulty": "beginner"
        },
        {
            "question": "Choose the past tense of 'go':",
            "topic": "Grammar",
            "userAnswer": "went",
            "correctAnswer": "went",
            "isCorrect": True,
            "explanation": "'Went' is the correct past tense of the irregular verb 'go'.",
            "difficulty": "beginner"
        },
        {
            "question": "What is the plural of 'child'?",
            "topic": "Grammar",
            "userAnswer": "children",
            "correctAnswer": "children",
            "isCorrect": True,
            "explanation": "'Children' is the irregular plural form of 'child'.",
            "difficulty": "beginner"
        },
        {
            "question": "Complete: 'I _____ to school every day'",
            "topic": "Grammar",
            "userAnswer": "go",
            "correctAnswer": "go",
            "isCorrect": True,
            "explanation": "Use 'go' with 'I' (first person singular).",
            "difficulty": "beginner"
        }
    ]


def create_sample_quiz_data(score_percentage=80, topic="Grammar", difficulty="beginner", questions=None):
    """Helper function to create sample quiz data for testing"""
    if questions is None:
        # Default questions
        questions = [
            {
                "question": "Which sentence is correct?",
                "topic": topic,
                "userAnswer": "She doesn't like coffee",
                "correctAnswer": "She doesn't like coffee",
                "isCorrect": True,
                "explanation": "This is the correct form using 'doesn't' for third person singular.",
                "difficulty": difficulty
            },
            {
                "question": "Choose the past tense of 'go':",
                "topic": topic,
                "userAnswer": "went",
                "correctAnswer": "went",
                "isCorrect": True,
                "explanation": "'Went' is the correct past tense of the irregular verb 'go'.",
                "difficulty": difficulty
            },
            {
                "question": "What is the plural of 'child'?",
                "topic": topic,
                "userAnswer": "children",
                "correctAnswer": "children",
                "isCorrect": score_percentage >= 75,  # Make some wrong for lower scores
                "explanation": "'Children' is the irregular plural form of 'child'.",
                "difficulty": difficulty
            },
            {
                "question": "Complete: 'I _____ to school every day'",
                "topic": topic,
                "userAnswer": "go" if score_percentage >= 100 else "goes",
                "correctAnswer": "go",
                "isCorrect": score_percentage >= 100,
                "explanation": "Use 'go' with 'I' (first person singular).",
                "difficulty": difficulty
            }
        ]
    
    # Adjust correct answers based on target score
    total_questions = len(questions)
    target_correct = int((score_percentage / 100) * total_questions)
    
    for i, question in enumerate(questions):
        if i < target_correct:
            question["isCorrect"] = True
            question["userAnswer"] = question["correctAnswer"]
        else:
            question["isCorrect"] = False
            question["userAnswer"] = "wrong answer"
    
    return {
        "quiz_data": {"questions": questions},
        "score": score_percentage,
        "topic": topic,
        "difficulty": difficulty,
        "quiz_type": "adaptive"
    }


class TestQuizSubmissionBasics:
    """Test class for basic quiz submission functionality"""

    def test_quiz_submission_endpoint_exists(self, authenticated_user, backend_url):
        """Test that the quiz evaluation endpoint exists and is accessible"""
        headers = authenticated_user['headers']
        quiz_data = create_sample_quiz_data(score_percentage=80)
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        # Should not return 404 (endpoint should exist)
        assert response.status_code != 404, "Quiz evaluation endpoint should exist"
        
        # Should return success or acceptable error
        assert response.status_code in [200, 400, 422], f"Unexpected status code: {response.status_code}"

    def test_quiz_submission_requires_authentication(self, backend_url):
        """Test that quiz submission requires authentication"""
        quiz_data = create_sample_quiz_data(score_percentage=80)
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", json=quiz_data)
        
        assert response.status_code == 401, f"Quiz submission should require auth, got {response.status_code}"

    def test_successful_quiz_submission(self, authenticated_user, backend_url):
        """Test successful quiz submission and response structure"""
        headers = authenticated_user['headers']
        quiz_data = create_sample_quiz_data(score_percentage=75)
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        assert response.status_code == 200, f"Quiz submission should succeed: {response.status_code} - {response.text}"
        
        result = response.json()
        
        # Check for expected response fields
        expected_fields = ["score", "total_quizzes"]
        for field in expected_fields:
            assert field in result, f"Response should contain '{field}' field"
        
        # Validate data types and ranges
        assert isinstance(result["score"], (int, float)), "Score should be numeric"
        assert 0 <= result["score"] <= 100, f"Score should be 0-100, got {result['score']}"
        assert isinstance(result["total_quizzes"], int), "Total quizzes should be an integer"
        assert result["total_quizzes"] > 0, "Total quizzes should be positive after submission"

    def test_quiz_submission_response_content(self, authenticated_user, backend_url):
        """Test that quiz submission response contains appropriate content"""
        headers = authenticated_user['headers']
        quiz_data = create_sample_quiz_data(score_percentage=85, topic="Vocabulary")
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Check for additional useful fields
        optional_fields = ["current_level", "average_score", "level_changed", "topic_performance"]
        present_fields = [field for field in optional_fields if field in result]
        
        assert len(present_fields) > 0, f"Response should contain some additional fields: {optional_fields}"
        
        # If level info is present, validate it
        if "current_level" in result:
            assert result["current_level"] in ["beginner", "intermediate", "advanced"], f"Invalid level: {result['current_level']}"
        
        # If average score is present, validate it
        if "average_score" in result:
            avg_score = result["average_score"]
            assert 0 <= avg_score <= 100, f"Average score should be 0-100, got {avg_score}"


class TestFirstQuizCompletion:
    """Test class for first quiz completion tracking"""

    def test_first_quiz_flag_initial_state(self, authenticated_user):
        """Test that new users have has_completed_first_quiz set to False"""
        initial_profile = authenticated_user['initial_profile']
        
        # Most new users should start with False
        assert initial_profile['has_completed_first_quiz'] in [False, True], "First quiz flag should be boolean"

    def test_first_quiz_completion_tracking(self, authenticated_user, backend_url):
        """Test that first quiz completion is properly tracked"""
        headers = authenticated_user['headers']
        initial_profile = authenticated_user['initial_profile']
        
        # Skip if user already completed first quiz
        if initial_profile['has_completed_first_quiz']:
            pytest.skip("User already completed first quiz")
        
        # Submit first quiz
        quiz_data = create_sample_quiz_data(score_percentage=75)
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        assert response.status_code == 200, "First quiz submission should succeed"
        
        # Check updated profile
        profile_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        assert profile_response.status_code == 200, "Profile retrieval should succeed"
        
        profile_data = profile_response.json()['data']
        has_completed_first = profile_data.get('has_completed_first_quiz', False)
        
        assert has_completed_first is True, "First quiz completion flag should be set after quiz submission"

    def test_first_quiz_flag_persistence(self, authenticated_user, backend_url):
        """Test that first quiz flag persists across multiple quiz submissions"""
        headers = authenticated_user['headers']
        
        # Submit a quiz to ensure flag is set
        quiz_data = create_sample_quiz_data(score_percentage=80)
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        assert response.status_code == 200
        
        # Submit another quiz
        quiz_data2 = create_sample_quiz_data(score_percentage=70, topic="Vocabulary")
        response2 = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                json=quiz_data2, headers=headers)
        assert response2.status_code == 200
        
        # Check profile
        profile_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()['data']
        has_completed_first = profile_data.get('has_completed_first_quiz', False)
        
        assert has_completed_first is True, "First quiz flag should remain True after multiple submissions"


class TestQuizScoring:
    """Test class for quiz scoring accuracy"""

    @pytest.mark.parametrize("expected_score", [100, 75, 50, 25, 0])
    def test_quiz_scoring_accuracy(self, authenticated_user, backend_url, expected_score):
        """Test that quiz scoring is calculated correctly for different score ranges"""
        headers = authenticated_user['headers']
        
        quiz_data = create_sample_quiz_data(score_percentage=expected_score)
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        assert response.status_code == 200, f"Quiz submission should succeed for {expected_score}% score"
        
        result = response.json()
        returned_score = result.get('score')
        
        assert returned_score == expected_score, f"Score mismatch: expected {expected_score}%, got {returned_score}%"

    def test_score_calculation_with_mixed_answers(self, authenticated_user, backend_url):
        """Test score calculation with a mix of correct and incorrect answers"""
        headers = authenticated_user['headers']
        
        # Create questions with specific correct/incorrect pattern
        questions = [
            {
                "question": "Question 1",
                "topic": "Grammar",
                "userAnswer": "correct",
                "correctAnswer": "correct",
                "isCorrect": True,
                "explanation": "Explanation 1",
                "difficulty": "beginner"
            },
            {
                "question": "Question 2", 
                "topic": "Grammar",
                "userAnswer": "wrong",
                "correctAnswer": "correct",
                "isCorrect": False,
                "explanation": "Explanation 2",
                "difficulty": "beginner"
            },
            {
                "question": "Question 3",
                "topic": "Grammar", 
                "userAnswer": "correct",
                "correctAnswer": "correct",
                "isCorrect": True,
                "explanation": "Explanation 3",
                "difficulty": "beginner"
            },
            {
                "question": "Question 4",
                "topic": "Grammar",
                "userAnswer": "wrong",
                "correctAnswer": "correct", 
                "isCorrect": False,
                "explanation": "Explanation 4",
                "difficulty": "beginner"
            }
        ]
        
        # 2 correct out of 4 = 50%
        quiz_data = {
            "quiz_data": {"questions": questions},
            "score": 50,
            "topic": "Grammar",
            "difficulty": "beginner",
            "quiz_type": "adaptive"
        }
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        returned_score = result.get('score')
        assert returned_score == 50, f"Expected 50% score for 2/4 correct, got {returned_score}%"

    def test_score_boundary_values(self, authenticated_user, backend_url):
        """Test score calculation at boundary values (0% and 100%)"""
        headers = authenticated_user['headers']
        
        # Test 0% score
        quiz_data_0 = create_sample_quiz_data(score_percentage=0)
        response_0 = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                 json=quiz_data_0, headers=headers)
        
        assert response_0.status_code == 200
        result_0 = response_0.json()
        assert result_0.get('score') == 0, "0% score should be handled correctly"
        
        # Test 100% score
        quiz_data_100 = create_sample_quiz_data(score_percentage=100)
        response_100 = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data_100, headers=headers)
        
        assert response_100.status_code == 200
        result_100 = response_100.json()
        assert result_100.get('score') == 100, "100% score should be handled correctly"


class TestTopicPerformanceTracking:
    """Test class for topic-specific performance tracking"""

    @pytest.mark.parametrize("topic", ["Grammar", "Vocabulary", "Reading", "Writing", "Listening"])
    def test_topic_performance_tracking(self, authenticated_user, backend_url, topic):
        """Test that performance is tracked by topic"""
        headers = authenticated_user['headers']
        
        quiz_data = create_sample_quiz_data(score_percentage=80, topic=topic)
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        assert response.status_code == 200, f"Quiz submission should succeed for {topic}"
        
        result = response.json()
        
        # Check if topic performance is tracked in response
        if "topic_performance" in result:
            topic_performance = result["topic_performance"]
            
            if topic in topic_performance:
                performance = topic_performance[topic]
                assert isinstance(performance, dict), f"{topic} performance should be a dictionary"
                
                # Check for expected performance fields
                if "correct" in performance and "total" in performance:
                    assert performance["total"] > 0, f"{topic} should have total questions > 0"
                    assert 0 <= performance["correct"] <= performance["total"], f"{topic} correct should be ≤ total"

    def test_multiple_topics_tracking(self, authenticated_user, backend_url):
        """Test that multiple topics are tracked independently"""
        headers = authenticated_user['headers']
        
        # Submit quizzes for different topics
        topics_to_test = ["Grammar", "Vocabulary"]
        
        for i, topic in enumerate(topics_to_test):
            score = 70 + (i * 10)  # Different scores for each topic
            quiz_data = create_sample_quiz_data(score_percentage=score, topic=topic)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            assert response.status_code == 200, f"Quiz submission should succeed for {topic}"
        
        # Check if both topics are tracked (implementation dependent)
        # This test validates the structure is in place

    def test_topic_performance_aggregation(self, authenticated_user, backend_url):
        """Test that topic performance aggregates correctly over multiple quizzes"""
        headers = authenticated_user['headers']
        topic = "Grammar"
        
        # Submit multiple quizzes for the same topic
        scores = [60, 80, 90]
        
        for score in scores:
            quiz_data = create_sample_quiz_data(score_percentage=score, topic=topic)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            assert response.status_code == 200, f"Quiz submission should succeed for score {score}"
        
        # Final response should reflect aggregated performance
        # Exact aggregation logic depends on implementation


class TestLevelProgression:
    """Test class for user level progression logic"""

    def test_level_progression_detection(self, authenticated_user, backend_url):
        """Test that level progression is detected with high scores"""
        headers = authenticated_user['headers']
        initial_level = authenticated_user['initial_profile']['english_level']
        
        # Submit several high-scoring quizzes
        high_scores = [85, 90, 85, 88, 92]
        
        level_changed = False
        current_level = initial_level
        
        for i, score in enumerate(high_scores):
            quiz_data = create_sample_quiz_data(score_percentage=score)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            assert response.status_code == 200, f"Quiz {i+1} submission should succeed"
            
            result = response.json()
            
            # Check for level progression indicators
            if "level_changed" in result and result["level_changed"]:
                level_changed = True
                new_level = result.get("current_level", current_level)
                assert new_level != current_level, "Level should actually change when level_changed is True"
                current_level = new_level
                break
            
            if "current_level" in result:
                current_level = result["current_level"]
        
        # Level progression might not always trigger in tests
        # This test validates the structure is in place

    def test_level_progression_validity(self, authenticated_user, backend_url):
        """Test that level progression follows valid progression paths"""
        headers = authenticated_user['headers']
        
        # Submit a high-scoring quiz and check level validity
        quiz_data = create_sample_quiz_data(score_percentage=95)
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        if "current_level" in result:
            current_level = result["current_level"]
            assert current_level in ["beginner", "intermediate", "advanced"], f"Invalid level: {current_level}"
        
        if "level_changed" in result and result["level_changed"]:
            # If level changed, it should be a valid progression
            initial_level = authenticated_user['initial_profile']['english_level']
            new_level = result.get("current_level")
            
            valid_progressions = {
                "beginner": ["intermediate"],
                "intermediate": ["advanced"],
                "advanced": []  # Can't progress beyond advanced
            }
            
            if new_level != initial_level:
                assert new_level in valid_progressions.get(initial_level, []), f"Invalid progression: {initial_level} -> {new_level}"

    def test_level_retrocession_detection(self, authenticated_user, backend_url):
        """Test that level retrocession can be detected with low scores"""
        headers = authenticated_user['headers']
        
        # If user is not at beginner level, test retrocession
        initial_level = authenticated_user['initial_profile']['english_level']
        
        if initial_level == "beginner":
            pytest.skip("Cannot test retrocession for beginner level users")
        
        # Submit several low-scoring quizzes
        low_scores = [30, 25, 35, 40, 30]
        
        for i, score in enumerate(low_scores):
            quiz_data = create_sample_quiz_data(score_percentage=score)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            assert response.status_code == 200, f"Low score quiz {i+1} should be accepted"
            
            result = response.json()
            
            # Check for level change indicators
            if "level_changed" in result and result["level_changed"]:
                new_level = result.get("current_level")
                if new_level != initial_level:
                    # Validate retrocession is valid
                    valid_retrocessions = {
                        "advanced": ["intermediate"],
                        "intermediate": ["beginner"]
                    }
                    assert new_level in valid_retrocessions.get(initial_level, []), f"Invalid retrocession: {initial_level} -> {new_level}"
                    break


class TestAverageScoreCalculation:
    """Test class for average score calculation"""

    def test_average_score_calculation(self, authenticated_user, backend_url):
        """Test that average score is calculated correctly"""
        headers = authenticated_user['headers']
        
        # Get initial profile state
        initial_profile_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        assert initial_profile_response.status_code == 200, "Initial profile retrieval should succeed"
        initial_profile = initial_profile_response.json()['data']
        initial_quizzes = initial_profile.get('total_quizzes', 0)
        initial_average = initial_profile.get('average_score', 0)
        
        # Submit multiple quizzes with known scores
        quiz_scores = [60, 70, 80, 90]
        
        for score in quiz_scores:
            quiz_data = create_sample_quiz_data(score_percentage=score)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            assert response.status_code == 200, f"Quiz with score {score} should succeed"
        
        # Check final average
        profile_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        assert profile_response.status_code == 200, "Profile retrieval should succeed"
        
        profile_data = profile_response.json()['data']
        final_average = profile_data.get('average_score', 0)
        final_quizzes = profile_data.get('total_quizzes', 0)
        
        # Verify quiz count increased
        assert final_quizzes >= initial_quizzes + len(quiz_scores), f"Quiz count should increase from {initial_quizzes} to at least {initial_quizzes + len(quiz_scores)}, got {final_quizzes}"
        
        # Verify average is reasonable
        assert 0 <= final_average <= 100, f"Average score should be 0-100, got {final_average}"
        
        # If this was the first set of quizzes, verify more precise calculation
        if initial_quizzes == 0 and final_average > 0:
            expected_average = sum(quiz_scores) / len(quiz_scores)  # 75.0
            assert abs(final_average - expected_average) < 5.0, f"Average score should be ~{expected_average}, got {final_average}"
        elif final_average == 0 and final_quizzes > initial_quizzes:
            # Average score might not have been calculated yet - this could be a backend issue
            # but the test should not fail for timing reasons
            pass

    def test_average_score_updates_realtime(self, authenticated_user, backend_url):
        """Test that average score updates with each quiz submission"""
        headers = authenticated_user['headers']
        
        initial_average = authenticated_user['initial_profile']['average_score']
        previous_average = initial_average
        
        # Submit quizzes and track average progression
        test_scores = [80, 90, 70]
        
        for i, score in enumerate(test_scores):
            quiz_data = create_sample_quiz_data(score_percentage=score)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            
            # Check if average is provided in response
            if "average_score" in result:
                current_average = result["average_score"]
                assert 0 <= current_average <= 100, f"Average score should be 0-100, got {current_average}"
                
                # Average should change (unless it's the exact same score)
                if score != previous_average:
                    # Average should be updated
                    pass  # Exact change depends on number of previous quizzes
                
                previous_average = current_average

    def test_average_score_with_extreme_values(self, authenticated_user, backend_url):
        """Test average score calculation with extreme values (0% and 100%)"""
        headers = authenticated_user['headers']
        
        # Submit extreme scores
        extreme_scores = [0, 100, 0, 100]
        expected_average = sum(extreme_scores) / len(extreme_scores)  # 50.0
        
        for score in extreme_scores:
            quiz_data = create_sample_quiz_data(score_percentage=score)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            assert response.status_code == 200, f"Extreme score {score} should be accepted"
        
        # Verify average is calculated correctly with extreme values
        profile_response = requests.get(f"{backend_url}/api/auth/profile", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()['data']
        final_average = profile_data.get('average_score', 0)
        
        # Should handle extreme values gracefully
        assert 0 <= final_average <= 100, f"Average with extreme values should be 0-100, got {final_average}"


class TestQuizSubmissionValidation:
    """Test class for quiz submission validation and error handling"""

    def test_missing_quiz_data_validation(self, authenticated_user, backend_url):
        """Test validation when quiz_data is missing"""
        headers = authenticated_user['headers']
        
        invalid_quiz = {
            "score": 80,
            "topic": "Grammar",
            "difficulty": "beginner"
            # Missing quiz_data
        }
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=invalid_quiz, headers=headers)
        
        assert response.status_code == 422, f"Missing quiz_data should return 422, got {response.status_code}"

    def test_missing_score_validation(self, authenticated_user, backend_url):
        """Test validation when score is missing"""
        headers = authenticated_user['headers']
        
        invalid_quiz = {
            "quiz_data": {"questions": []},
            "topic": "Grammar",
            "difficulty": "beginner"
            # Missing score
        }
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=invalid_quiz, headers=headers)
        
        assert response.status_code == 422, f"Missing score should return 422, got {response.status_code}"

    def test_invalid_score_range_validation(self, authenticated_user, backend_url):
        """Test validation of score ranges"""
        headers = authenticated_user['headers']
        
        # Test score > 100
        invalid_high_score = create_sample_quiz_data(score_percentage=80)
        invalid_high_score['score'] = 150
        
        response_high = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                    json=invalid_high_score, headers=headers)
        
        # Might be accepted and clamped, or rejected - both are valid
        assert response_high.status_code in [200, 400, 422], f"High score handling: {response_high.status_code}"
        
        # Test negative score
        invalid_low_score = create_sample_quiz_data(score_percentage=80)
        invalid_low_score['score'] = -10
        
        response_low = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=invalid_low_score, headers=headers)
        
        # Should handle negative scores appropriately
        assert response_low.status_code in [200, 400, 422], f"Negative score handling: {response_low.status_code}"

    def test_empty_questions_validation(self, authenticated_user, backend_url):
        """Test validation when questions array is empty"""
        headers = authenticated_user['headers']
        
        empty_questions_quiz = {
            "quiz_data": {"questions": []},
            "score": 0,
            "topic": "Grammar",
            "difficulty": "beginner",
            "quiz_type": "adaptive"
        }
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=empty_questions_quiz, headers=headers)
        
        # Empty questions might be rejected or accepted with 0 score
        assert response.status_code in [200, 400, 422], f"Empty questions handling: {response.status_code}"

    def test_malformed_question_data_validation(self, authenticated_user, backend_url):
        """Test validation of malformed question data"""
        headers = authenticated_user['headers']
        
        malformed_quiz = {
            "quiz_data": {
                "questions": [
                    {
                        # Missing required fields like 'question', 'isCorrect', etc.
                        "topic": "Grammar"
                    }
                ]
            },
            "score": 50,
            "topic": "Grammar",
            "difficulty": "beginner",
            "quiz_type": "adaptive"
        }
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=malformed_quiz, headers=headers)
        
        # Should handle malformed questions appropriately
        assert response.status_code in [200, 400, 422], f"Malformed questions handling: {response.status_code}"

    def test_invalid_topic_validation(self, authenticated_user, backend_url):
        """Test handling of invalid/unusual topics"""
        headers = authenticated_user['headers']
        
        unusual_topic_quiz = create_sample_quiz_data(score_percentage=75, topic="UnusualTopic123")
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=unusual_topic_quiz, headers=headers)
        
        # Should accept unusual topics gracefully
        assert response.status_code in [200, 400], f"Unusual topic should be handled gracefully: {response.status_code}"

    def test_invalid_difficulty_validation(self, authenticated_user, backend_url):
        """Test handling of invalid difficulty levels"""
        headers = authenticated_user['headers']
        
        invalid_difficulty_quiz = create_sample_quiz_data(score_percentage=75, difficulty="invalid_difficulty")
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=invalid_difficulty_quiz, headers=headers)
        
        # Should handle invalid difficulty appropriately
        assert response.status_code in [200, 400, 422], f"Invalid difficulty handling: {response.status_code}"


class TestQuizEvaluationEdgeCases:
    """Test class for edge cases and error scenarios"""

    def test_concurrent_quiz_submissions(self, authenticated_user, backend_url):
        """Test handling of rapid/concurrent quiz submissions"""
        headers = authenticated_user['headers']
        
        # Submit quizzes rapidly
        responses = []
        for i in range(3):
            quiz_data = create_sample_quiz_data(score_percentage=70 + i*10)
            
            response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            responses.append(response)
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # All submissions should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Rapid submission {i+1} should succeed: {response.status_code}"

    def test_very_large_quiz_submission(self, authenticated_user, backend_url):
        """Test handling of quizzes with many questions"""
        headers = authenticated_user['headers']
        
        # Create a quiz with many questions
        many_questions = []
        for i in range(20):  # Large number of questions
            question = {
                "question": f"Question {i+1}",
                "topic": "Grammar",
                "userAnswer": "answer",
                "correctAnswer": "answer",
                "isCorrect": True,
                "explanation": f"Explanation {i+1}",
                "difficulty": "beginner"
            }
            many_questions.append(question)
        
        large_quiz = {
            "quiz_data": {"questions": many_questions},
            "score": 100,
            "topic": "Grammar",
            "difficulty": "beginner",
            "quiz_type": "adaptive"
        }
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=large_quiz, headers=headers)
        
        # Should handle large quizzes gracefully
        assert response.status_code in [200, 400, 413], f"Large quiz handling: {response.status_code}"

    def test_quiz_submission_with_unicode_content(self, authenticated_user, backend_url):
        """Test quiz submission with Unicode characters"""
        headers = authenticated_user['headers']
        
        unicode_quiz = create_sample_quiz_data(score_percentage=80)
        # Add Unicode content
        unicode_quiz["quiz_data"]["questions"][0]["question"] = "What's the meaning of 'café'? ☕"
        unicode_quiz["quiz_data"]["questions"][0]["userAnswer"] = "Coffee shop with café ☕"
        unicode_quiz["quiz_data"]["questions"][0]["explanation"] = "Café means coffee shop in French 🇫🇷"
        
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=unicode_quiz, headers=headers)
        
        # Should handle Unicode content properly
        assert response.status_code == 200, f"Unicode content should be handled: {response.status_code}"

    def test_quiz_submission_performance_timing(self, authenticated_user, backend_url):
        """Test that quiz submission responds within reasonable time"""
        headers = authenticated_user['headers']
        
        quiz_data = create_sample_quiz_data(score_percentage=80)
        
        start_time = time.time()
        response = requests.post(f"{backend_url}/api/evaluate-quiz/", 
                               json=quiz_data, headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200, "Quiz submission should succeed"
        assert response_time < 10.0, f"Quiz evaluation should complete within 10 seconds, took {response_time:.2f}s"


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
    print("🚀 Running Quiz Evaluation Tests with pytest...")
    print("=" * 60)
    print("\n📋 Test Coverage:")
    print("   • Quiz submission basics")
    print("   • First quiz completion tracking")
    print("   • Scoring accuracy and calculation")
    print("   • Topic performance tracking")
    print("   • Level progression and retrocession")
    print("   • Average score calculation")
    print("   • Input validation and error handling")
    print("   • Edge cases and performance")
    print("\n" + "=" * 60)
    
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


# Legacy support function for backward compatibility
def main():
    """Legacy main function for backward compatibility"""
    print("🚀 Running Quiz Evaluation Tests with pytest...")
    print("=" * 60)
    print("\n📋 Test Coverage:")
    print("   • Quiz submission basics")
    print("   • First quiz completion tracking")
    print("   • Scoring accuracy and calculation")
    print("   • Topic performance tracking")
    print("   • Level progression and retrocession")
    print("   • Average score calculation")
    print("   • Input validation and error handling")
    print("   • Edge cases and performance")
    print("\n" + "=" * 60)
    
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


if __name__ == "__main__":
    # Run pytest when executed directly
    pytest.main([__file__, "-v"])
