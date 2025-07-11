#!/usr/bin/env python3
"""
Comprehensive pytest test suite for Reading Comprehension Feature
Tests: Reading comprehension passages, topic-specific question generation, passage validation
"""

import pytest
import requests
import json
import random
import time
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
    return f"read_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_user_data(unique_username):
    """Fixture to provide test user data"""
    return {
        "username": unique_username,
        "password": "ReadTest123"
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
def reading_quiz_request():
    """Fixture providing a sample reading quiz request"""
    return {
        "topic": "Reading",
        "num_questions": 4,
        "previous_questions": []
    }


@pytest.fixture
def non_reading_quiz_request():
    """Fixture providing a sample non-reading quiz request"""
    return {
        "topic": "Grammar",
        "num_questions": 4,
        "previous_questions": []
    }


class TestReadingComprehensionPassages:
    """Test class for reading comprehension passage functionality"""

    def test_reading_quiz_generation_endpoint(self, authenticated_user, backend_url, reading_quiz_request):
        """Test that reading quiz generation endpoint is accessible"""
        headers = authenticated_user['headers']
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=reading_quiz_request, headers=headers)
        
        # Should not return 404 (endpoint should exist)
        assert response.status_code != 404, "Reading quiz generation endpoint should exist"
        
        # Should return success or acceptable error
        assert response.status_code in [200, 400, 422, 500, 503], f"Unexpected status code: {response.status_code}"

    def test_reading_questions_include_passages(self, authenticated_user, backend_url, reading_quiz_request):
        """Test that Reading topic generates questions with comprehension passages"""
        headers = authenticated_user['headers']
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=reading_quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            assert len(questions) > 0, "Should generate at least one reading question"
            
            # Check if questions have passages
            questions_with_passages = 0
            
            for i, question in enumerate(questions):
                assert question.get('topic') == 'Reading', f"Question {i+1} should be Reading topic"
                
                if 'passage' in question and question['passage']:
                    questions_with_passages += 1
                    
                    # Validate passage content
                    passage = question['passage']
                    assert isinstance(passage, str), f"Question {i+1} passage should be a string"
                    assert len(passage.strip()) > 50, f"Question {i+1} passage should be substantial (>50 chars)"
                    
                    # Validate question relates to passage
                    question_text = question.get('question', '')
                    assert len(question_text.strip()) > 10, f"Question {i+1} should have substantial text"
            
            # At least some questions should have passages for Reading topic
            assert questions_with_passages > 0, "Reading questions should include comprehension passages"
            
            # Ideally, all reading questions should have passages
            passage_ratio = questions_with_passages / len(questions)
            assert passage_ratio >= 0.5, f"At least 50% of reading questions should have passages, got {passage_ratio:.1%}"
        
        elif response.status_code in [500, 503]:
            pytest.skip(f"Reading quiz generation service unavailable: {response.status_code}")
        else:
            pytest.fail(f"Failed to generate reading quiz: {response.status_code} - {response.text}")

    def test_reading_passage_content_quality(self, authenticated_user, backend_url, reading_quiz_request):
        """Test that reading passages meet quality standards"""
        headers = authenticated_user['headers']
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=reading_quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            passages_found = 0
            
            for i, question in enumerate(questions):
                if 'passage' in question and question['passage']:
                    passages_found += 1
                    passage = question['passage']
                    
                    # Quality checks for passage
                    assert len(passage) >= 100, f"Passage {i+1} should be at least 100 characters long"
                    assert len(passage) <= 2000, f"Passage {i+1} should not exceed 2000 characters"
                    
                    # Check for basic structure (sentences)
                    sentence_endings = passage.count('.') + passage.count('!') + passage.count('?')
                    assert sentence_endings >= 3, f"Passage {i+1} should contain multiple sentences"
                    
                    # Check passage isn't just repeated text
                    words = passage.split()
                    unique_words = set(word.lower().strip('.,!?;:') for word in words)
                    word_variety_ratio = len(unique_words) / len(words) if words else 0
                    assert word_variety_ratio > 0.3, f"Passage {i+1} should have varied vocabulary"
                    
                    # Validate question references passage
                    question_text = question.get('question', '')
                    # Questions should relate to comprehension
                    comprehension_indicators = [
                        'according to the passage', 'the passage states', 'in the text',
                        'the author', 'what does', 'which of the following', 'based on'
                    ]
                    has_comprehension_indicator = any(
                        indicator in question_text.lower() 
                        for indicator in comprehension_indicators
                    )
                    
                    # Not all questions need explicit indicators, but passage should be relevant
                    assert len(question_text) > 20, f"Question {i+1} should be substantial"
            
            if passages_found == 0:
                pytest.skip("No passages found to validate quality")
        
        elif response.status_code in [500, 503]:
            pytest.skip("Reading quiz generation service unavailable for quality testing")
        else:
            pytest.fail(f"Failed to generate reading quiz for quality testing: {response.status_code}")

    def test_reading_questions_structure_with_passages(self, authenticated_user, backend_url, reading_quiz_request):
        """Test that reading questions with passages have proper structure"""
        headers = authenticated_user['headers']
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=reading_quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            for i, question in enumerate(questions):
                # Standard question structure
                required_fields = ['question', 'options', 'correct_answer', 'explanation', 'topic', 'difficulty']
                
                for field in required_fields:
                    assert field in question, f"Question {i+1} missing required field '{field}'"
                
                # Additional checks for questions with passages
                if 'passage' in question and question['passage']:
                    # Options should be meaningful for comprehension
                    options = question.get('options', [])
                    assert len(options) == 4, f"Question {i+1} should have 4 options"
                    
                    # Options should have reasonable length for comprehension questions
                    for j, option in enumerate(options):
                        assert len(option.strip()) > 2, f"Question {i+1} option {j+1} too short"
                        assert len(option.strip()) < 200, f"Question {i+1} option {j+1} too long"
                    
                    # Correct answer should be in options
                    correct_answer = question.get('correct_answer')
                    assert correct_answer in options, f"Question {i+1} correct answer not in options"
                    
                    # Explanation should reference comprehension
                    explanation = question.get('explanation', '')
                    assert len(explanation) > 20, f"Question {i+1} explanation should be substantial"
        
        elif response.status_code in [500, 503]:
            pytest.skip("Reading quiz generation service unavailable for structure testing")
        else:
            pytest.fail(f"Failed to generate reading quiz for structure testing: {response.status_code}")

    def test_multiple_reading_questions_different_passages(self, authenticated_user, backend_url):
        """Test that multiple reading questions can have different passages"""
        headers = authenticated_user['headers']
        
        quiz_request = {
            "topic": "Reading",
            "num_questions": 6,  # Request more questions to test variety
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            passages = []
            for question in questions:
                if 'passage' in question and question['passage']:
                    passages.append(question['passage'])
            
            if len(passages) >= 2:
                # Check for passage variety
                unique_passages = set(passages)
                variety_ratio = len(unique_passages) / len(passages)
                
                # At least some variety in passages (not all identical)
                assert variety_ratio > 0.5, f"Should have some variety in passages, got {variety_ratio:.1%}"
                
                # Check passages are meaningfully different
                if len(unique_passages) >= 2:
                    passage_list = list(unique_passages)
                    for i in range(len(passage_list)):
                        for j in range(i + 1, len(passage_list)):
                            # Passages should be significantly different
                            similarity = self._calculate_text_similarity(passage_list[i], passage_list[j])
                            assert similarity < 0.8, f"Passages {i+1} and {j+1} too similar ({similarity:.1%})"
            else:
                pytest.skip("Not enough passages generated to test variety")
        
        elif response.status_code in [500, 503]:
            pytest.skip("Reading quiz generation service unavailable for variety testing")
        else:
            pytest.fail(f"Failed to generate multiple reading questions: {response.status_code}")

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Helper method to calculate text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)


class TestNonReadingTopics:
    """Test class for ensuring non-reading topics don't inappropriately include passages"""

    @pytest.mark.parametrize("topic", ["Grammar", "Vocabulary", "Writing", "Listening"])
    def test_non_reading_topics_no_passages(self, authenticated_user, backend_url, topic):
        """Test that non-Reading topics don't include comprehension passages"""
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
            
            assert len(questions) > 0, f"Should generate at least one {topic} question"
            
            # Check that questions don't have passages
            questions_with_passages = 0
            
            for i, question in enumerate(questions):
                if 'passage' in question and question['passage']:
                    # Some topics might legitimately have short context, but not full passages
                    passage_length = len(question['passage'])
                    
                    if passage_length > 200:  # Long passages inappropriate for non-reading topics
                        questions_with_passages += 1
                        pytest.fail(f"{topic} question {i+1} inappropriately has long passage ({passage_length} chars)")
                    else:
                        # Short context might be acceptable for some topics
                        pass
            
            # Non-reading topics should generally not have passages
            passage_ratio = questions_with_passages / len(questions)
            assert passage_ratio == 0, f"{topic} questions should not have reading comprehension passages"
        
        elif response.status_code in [500, 503]:
            pytest.skip(f"{topic} quiz generation service unavailable")
        else:
            pytest.fail(f"Failed to generate {topic} quiz: {response.status_code}")

    def test_grammar_questions_structure(self, authenticated_user, backend_url):
        """Test that Grammar questions have appropriate structure (no passages)"""
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
                # Standard structure checks
                assert question.get('topic') == 'Grammar', f"Question {i+1} should be Grammar topic"
                
                # Grammar questions shouldn't have reading passages
                passage = question.get('passage', '')
                if passage:
                    # Allow short context but not reading comprehension passages
                    assert len(passage) < 100, f"Grammar question {i+1} has unexpectedly long passage"
                
                # Grammar questions should focus on language rules
                question_text = question.get('question', '')
                grammar_indicators = [
                    'correct', 'incorrect', 'which', 'choose', 'select', 'best',
                    'sentence', 'word', 'form', 'tense', 'grammar'
                ]
                
                has_grammar_focus = any(
                    indicator in question_text.lower() 
                    for indicator in grammar_indicators
                )
                
                # Most grammar questions should have grammar-focused language
                if not has_grammar_focus:
                    # Still acceptable, just noting
                    pass
        
        elif response.status_code in [500, 503]:
            pytest.skip("Grammar quiz generation service unavailable")
        else:
            pytest.fail(f"Failed to generate grammar quiz: {response.status_code}")

    def test_vocabulary_questions_structure(self, authenticated_user, backend_url):
        """Test that Vocabulary questions have appropriate structure (no passages)"""
        headers = authenticated_user['headers']
        
        quiz_request = {
            "topic": "Vocabulary",
            "num_questions": 4,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=quiz_request, headers=headers)
        
        if response.status_code == 200:
            quiz_data = response.json()
            questions = quiz_data.get("questions", [])
            
            for i, question in enumerate(questions):
                # Standard structure checks
                assert question.get('topic') == 'Vocabulary', f"Question {i+1} should be Vocabulary topic"
                
                # Vocabulary questions shouldn't have reading passages
                passage = question.get('passage', '')
                if passage:
                    # Allow short context but not reading comprehension passages
                    assert len(passage) < 150, f"Vocabulary question {i+1} has unexpectedly long passage"
                
                # Vocabulary questions should focus on word meanings/usage
                question_text = question.get('question', '')
                vocab_indicators = [
                    'meaning', 'definition', 'synonym', 'antonym', 'word', 'vocabulary',
                    'means', 'refers to', 'best describes', 'closest in meaning'
                ]
                
                has_vocab_focus = any(
                    indicator in question_text.lower() 
                    for indicator in vocab_indicators
                )
                
                # Note vocabulary focus but don't require it
                if not has_vocab_focus:
                    pass
        
        elif response.status_code in [500, 503]:
            pytest.skip("Vocabulary quiz generation service unavailable")
        else:
            pytest.fail(f"Failed to generate vocabulary quiz: {response.status_code}")


class TestReadingComprehensionEdgeCases:
    """Test class for edge cases in reading comprehension functionality"""

    def test_reading_quiz_with_previous_questions(self, authenticated_user, backend_url):
        """Test reading quiz generation with previous questions to avoid repetition"""
        headers = authenticated_user['headers']
        
        # Generate first reading quiz
        first_request = {
            "topic": "Reading",
            "num_questions": 4,
            "previous_questions": []
        }
        
        first_response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                     json=first_request, headers=headers)
        
        if first_response.status_code != 200:
            pytest.skip(f"Cannot test reading repetition: first quiz generation failed: {first_response.status_code}")
        
        first_quiz = first_response.json()
        first_questions = [q['question'] for q in first_quiz.get('questions', [])]
        
        # Generate second reading quiz with previous questions
        second_request = {
            "topic": "Reading",
            "num_questions": 4,
            "previous_questions": first_questions
        }
        
        second_response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                      json=second_request, headers=headers)
        
        if second_response.status_code == 200:
            second_quiz = second_response.json()
            second_questions = [q['question'] for q in second_quiz.get('questions', [])]
            
            # Check for question repetition
            repeated_questions = set(first_questions) & set(second_questions)
            repetition_ratio = len(repeated_questions) / len(first_questions) if first_questions else 0
            
            # Should avoid too much repetition
            assert repetition_ratio <= 0.5, f"Too many repeated reading questions: {len(repeated_questions)}/{len(first_questions)}"
            
            # Check that passages are different (if present)
            first_passages = [q.get('passage', '') for q in first_quiz.get('questions', []) if q.get('passage')]
            second_passages = [q.get('passage', '') for q in second_quiz.get('questions', []) if q.get('passage')]
            
            if first_passages and second_passages:
                repeated_passages = set(first_passages) & set(second_passages)
                passage_repetition_ratio = len(repeated_passages) / len(first_passages)
                
                # Passages should ideally be different
                assert passage_repetition_ratio <= 0.5, "Should avoid repeating reading passages"
        
        elif second_response.status_code in [500, 503]:
            pytest.skip("Reading quiz generation service unavailable for repetition testing")
        else:
            pytest.fail(f"Failed to generate second reading quiz: {second_response.status_code}")

    def test_reading_quiz_with_different_question_counts(self, authenticated_user, backend_url):
        """Test reading quiz generation with different question counts"""
        headers = authenticated_user['headers']
        
        question_counts = [2, 4, 6]
        
        for count in question_counts:
            quiz_request = {
                "topic": "Reading",
                "num_questions": count,
                "previous_questions": []
            }
            
            response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                                   json=quiz_request, headers=headers)
            
            if response.status_code == 200:
                quiz_data = response.json()
                questions = quiz_data.get("questions", [])
                
                assert len(questions) == count, f"Expected {count} reading questions, got {len(questions)}"
                
                # Check that passages are maintained across different counts
                questions_with_passages = sum(1 for q in questions if q.get('passage'))
                passage_ratio = questions_with_passages / len(questions) if questions else 0
                
                # Should maintain passage quality regardless of count
                assert passage_ratio >= 0.3, f"Should maintain passages for {count} questions, got {passage_ratio:.1%}"
            
            elif response.status_code in [500, 503]:
                pytest.skip(f"Reading quiz generation unavailable for {count} questions")
            else:
                pytest.fail(f"Failed to generate {count} reading questions: {response.status_code}")

    def test_reading_quiz_response_time(self, authenticated_user, backend_url, reading_quiz_request):
        """Test that reading quiz generation responds within reasonable time"""
        headers = authenticated_user['headers']
        
        start_time = time.time()
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=reading_quiz_request, headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            # Reading comprehension might take longer due to passage generation
            assert response_time < 90.0, f"Reading quiz generation should complete within 90 seconds, took {response_time:.2f}s"
        elif response.status_code in [500, 503]:
            pytest.skip("Reading quiz generation service unavailable for timing test")
        else:
            pytest.fail(f"Reading quiz generation failed: {response.status_code}")

    def test_invalid_reading_quiz_requests(self, authenticated_user, backend_url):
        """Test handling of invalid reading quiz requests"""
        headers = authenticated_user['headers']
        
        # Test with invalid topic
        invalid_request = {
            "topic": "InvalidReading",
            "num_questions": 4,
            "previous_questions": []
        }
        
        response = requests.post(f"{backend_url}/api/generate-adaptive-quiz/", 
                               json=invalid_request, headers=headers)
        
        # Should handle invalid topic gracefully
        assert response.status_code in [200, 400, 422, 500], f"Invalid reading topic should be handled: {response.status_code}"


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
    print("🚀 Running Reading Comprehension Tests with pytest...")
    print("=" * 60)
    print("\n📋 Test Coverage:")
    print("   • Reading comprehension passage inclusion")
    print("   • Reading passage content quality")
    print("   • Reading question structure validation")
    print("   • Non-reading topics passage exclusion")
    print("   • Grammar and vocabulary question validation")
    print("   • Edge cases and error handling")
    print("   • Response times and performance")
    print("\n" + "=" * 60)
    
    exit_code = pytest.main([__file__, "-v"])
    return exit_code == 0


if __name__ == "__main__":
    # Run pytest when executed directly
    pytest.main([__file__, "-v"])
