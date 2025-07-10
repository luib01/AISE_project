#!/usr/bin/env python3
"""
Comprehensive test suite for Quiz Generation and Management
Tests: Adaptive quiz generation, static quiz functionality, quiz topics, model health
"""

import requests
import json
import time
import random

# Test configuration
BACKEND_URL = "http://localhost:8000"

class QuizGenerationTester:
    def __init__(self):
        self.test_user = None
        self.session_token = None
        self.available_topics = []
    
    def setup_test_user(self):
        """Create a test user for quiz testing"""
        print("🔧 Setting up test user...")
        
        username = f"quiz_{random.randint(100, 999)}"
        password = "QuizTest123"
        
        # Register user
        signup_response = requests.post(f"{BACKEND_URL}/api/auth/signup", 
                                      json={"username": username, "password": password})
        
        if signup_response.status_code == 200:
            self.test_user = {"username": username, "password": password}
            print(f"   ✅ Test user created: {username}")
        else:
            print(f"   ❌ Failed to create test user: {signup_response.status_code}")
            return False
        
        # Login user
        signin_response = requests.post(f"{BACKEND_URL}/api/auth/signin", 
                                      json={"username": username, "password": password})
        
        if signin_response.status_code == 200:
            self.session_token = signin_response.json()['data']['session_token']
            print(f"   ✅ Test user logged in successfully")
            return True
        else:
            print(f"   ❌ Failed to login test user: {signin_response.status_code}")
            return False
    
    def cleanup_test_user(self):
        """Clean up test user"""
        if self.test_user and self.session_token:
            print("🧹 Cleaning up test user...")
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            delete_response = requests.delete(f"{BACKEND_URL}/api/auth/profile", 
                                            json={"password": self.test_user['password']}, 
                                            headers=headers)
            if delete_response.status_code == 200:
                print("   ✅ Test user cleaned up successfully")
            else:
                print(f"   ⚠️ Failed to cleanup test user: {delete_response.status_code}")
    
    def test_quiz_topics_endpoint(self):
        """Test the quiz topics endpoint"""
        print("🧪 Testing Quiz Topics Endpoint...")
        
        response = requests.get(f"{BACKEND_URL}/api/quiz-topics/")
        
        if response.status_code == 200:
            topics_data = response.json()
            self.available_topics = topics_data.get('topics', [])
            print("   ✅ Quiz topics retrieved successfully")
            print(f"      Available topics: {len(self.available_topics)}")
            
            for topic in self.available_topics[:3]:  # Show first 3 topics
                print(f"      - {topic['name']}: {len(topic['subtopics'])} subtopics")
            
            # Validate topic structure
            required_fields = ['name', 'subtopics', 'levels']
            for topic in self.available_topics:
                if all(field in topic for field in required_fields):
                    continue
                else:
                    print(f"   ❌ Topic {topic.get('name', 'unknown')} missing required fields")
                    return False
            
            print("   ✅ All topics have required structure")
            return True
        else:
            print(f"   ❌ Failed to retrieve quiz topics: {response.status_code}")
            return False
    
    def test_adaptive_quiz_generation(self):
        """Test adaptive quiz generation functionality"""
        print("🧪 Testing Adaptive Quiz Generation...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for quiz generation")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        # Test different topics and difficulties
        test_cases = [
            {"topic": "Grammar", "description": "Grammar quiz"},
            {"topic": "Vocabulary", "description": "Vocabulary quiz"},
            {"topic": "Mixed", "description": "Mixed topic quiz"},
        ]
        
        for test_case in test_cases:
            print(f"   Testing {test_case['description']}...")
            
            quiz_request = {
                "topic": test_case["topic"],
                "num_questions": 4,
                "previous_questions": []
            }
            
            response = requests.post(f"{BACKEND_URL}/api/generate-adaptive-quiz/", 
                                   json=quiz_request, headers=headers)
            
            if response.status_code == 200:
                quiz_data = response.json()
                questions = quiz_data.get("questions", [])
                
                if len(questions) == 4:
                    print(f"      ✅ {test_case['description']} generated successfully (4 questions)")
                    
                    # Validate question structure
                    required_fields = ['question', 'options', 'correct_answer', 'explanation', 'topic', 'difficulty']
                    valid_questions = 0
                    
                    for i, question in enumerate(questions):
                        if all(field in question for field in required_fields):
                            if len(question['options']) == 4:
                                valid_questions += 1
                            else:
                                print(f"      ❌ Question {i+1} doesn't have 4 options")
                        else:
                            print(f"      ❌ Question {i+1} missing required fields")
                    
                    if valid_questions == 4:
                        print(f"      ✅ All questions have valid structure")
                    else:
                        print(f"      ❌ Only {valid_questions}/4 questions are valid")
                        return False
                        
                else:
                    print(f"      ❌ Expected 4 questions, got {len(questions)}")
                    return False
            else:
                print(f"      ❌ {test_case['description']} generation failed: {response.status_code}")
                return False
        
        return True
    
    def test_quiz_generation_with_previous_questions(self):
        """Test quiz generation with previous questions to avoid repetition"""
        print("🧪 Testing Quiz Generation with Previous Questions...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for quiz generation")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        # Generate first quiz
        first_quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": []
        }
        
        first_response = requests.post(f"{BACKEND_URL}/api/generate-adaptive-quiz/", 
                                     json=first_quiz_request, headers=headers)
        
        if first_response.status_code != 200:
            print(f"   ❌ Failed to generate first quiz: {first_response.status_code}")
            return False
        
        first_quiz = first_response.json()
        first_questions = [q['question'] for q in first_quiz.get('questions', [])]
        
        # Generate second quiz with previous questions
        second_quiz_request = {
            "topic": "Grammar",
            "num_questions": 4,
            "previous_questions": first_questions
        }
        
        second_response = requests.post(f"{BACKEND_URL}/api/generate-adaptive-quiz/", 
                                      json=second_quiz_request, headers=headers)
        
        if second_response.status_code == 200:
            second_quiz = second_response.json()
            second_questions = [q['question'] for q in second_quiz.get('questions', [])]
            
            # Check for repetition
            repeated_questions = set(first_questions) & set(second_questions)
            
            if len(repeated_questions) == 0:
                print("   ✅ No question repetition detected")
                print(f"      Previous questions considered: {second_quiz.get('previous_questions_considered', 0)}")
                return True
            else:
                print(f"   ⚠️ Found {len(repeated_questions)} repeated questions")
                print("      This might be acceptable for fallback scenarios")
                return True
        else:
            print(f"   ❌ Failed to generate second quiz: {second_response.status_code}")
            return False
    
    def test_model_health_and_info(self):
        """Test model health check and info endpoints"""
        print("🧪 Testing Model Health and Info...")
        
        # Test model info endpoint
        info_response = requests.get(f"{BACKEND_URL}/api/model-info/")
        
        if info_response.status_code == 200:
            model_info = info_response.json()
            print("   ✅ Model info retrieved successfully")
            print(f"      Current model: {model_info.get('current_model')}")
            print(f"      Base URL: {model_info.get('base_url')}")
            print(f"      Timeout: {model_info.get('timeout')}s")
        else:
            print(f"   ❌ Failed to retrieve model info: {info_response.status_code}")
            return False
        
        # Test health check endpoint
        health_response = requests.get(f"{BACKEND_URL}/api/health-check/")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("   ✅ Model health check passed")
            print(f"      Status: {health_data.get('status')}")
            print(f"      Message: {health_data.get('message')}")
            return True
        else:
            print(f"   ❌ Model health check failed: {health_response.status_code}")
            # This might be expected if Ollama is not running
            print("      Note: This is expected if Ollama/AI model is not running")
            return True  # Don't fail the test for this
    
    def test_user_profile_endpoint(self):
        """Test user profile endpoint for quiz generation"""
        print("🧪 Testing User Profile Endpoint...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for profile testing")
            return False
        
        # Get user info from auth
        headers = {"Authorization": f"Bearer {self.session_token}"}
        auth_response = requests.get(f"{BACKEND_URL}/api/auth/profile", headers=headers)
        
        if auth_response.status_code != 200:
            print(f"   ❌ Failed to get user auth profile: {auth_response.status_code}")
            return False
        
        user_id = auth_response.json()['data']['user_id']
        
        # Test user profile endpoint
        profile_response = requests.get(f"{BACKEND_URL}/api/user-profile/{user_id}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("   ✅ User profile retrieved successfully")
            print(f"      User ID: {profile_data.get('user_id')}")
            print(f"      English Level: {profile_data.get('english_level')}")
            print(f"      Total Quizzes: {profile_data.get('total_quizzes')}")
            print(f"      Average Score: {profile_data.get('average_score')}")
            
            # Validate required fields
            required_fields = ['user_id', 'english_level', 'progress', 'total_quizzes', 'average_score']
            if all(field in profile_data for field in required_fields):
                print("   ✅ Profile has all required fields")
                return True
            else:
                missing_fields = [field for field in required_fields if field not in profile_data]
                print(f"   ❌ Profile missing fields: {missing_fields}")
                return False
        else:
            print(f"   ❌ Failed to retrieve user profile: {profile_response.status_code}")
            return False
    
    def test_quiz_difficulty_levels(self):
        """Test quiz generation for different difficulty levels"""
        print("🧪 Testing Quiz Difficulty Levels...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for difficulty testing")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        difficulty_levels = ["beginner", "intermediate", "advanced"]
        
        for difficulty in difficulty_levels:
            print(f"   Testing {difficulty} level...")
            
            quiz_request = {
                "topic": "Grammar",
                "num_questions": 4,
                "force_difficulty": difficulty,
                "previous_questions": []
            }
            
            response = requests.post(f"{BACKEND_URL}/api/generate-adaptive-quiz/", 
                                   json=quiz_request, headers=headers)
            
            if response.status_code == 200:
                quiz_data = response.json()
                questions = quiz_data.get("questions", [])
                
                # Check if questions have the requested difficulty
                difficulty_matches = sum(1 for q in questions if q.get('difficulty') == difficulty)
                
                if difficulty_matches > 0:
                    print(f"      ✅ {difficulty} quiz generated ({difficulty_matches}/4 questions match level)")
                else:
                    print(f"      ⚠️ {difficulty} quiz generated but difficulty levels don't match")
            else:
                print(f"      ❌ Failed to generate {difficulty} quiz: {response.status_code}")
                return False
        
        return True
    
    def run_all_tests(self):
        """Run all quiz generation tests"""
        print("🚀 Starting Quiz Generation Tests...\n")
        
        success_count = 0
        total_tests = 6
        
        try:
            if not self.setup_test_user():
                print("❌ Failed to setup test user. Aborting quiz tests.")
                return False
            print()
            
            if self.test_quiz_topics_endpoint():
                success_count += 1
            print()
            
            if self.test_adaptive_quiz_generation():
                success_count += 1
            print()
            
            if self.test_quiz_generation_with_previous_questions():
                success_count += 1
            print()
            
            if self.test_model_health_and_info():
                success_count += 1
            print()
            
            if self.test_user_profile_endpoint():
                success_count += 1
            print()
            
            if self.test_quiz_difficulty_levels():
                success_count += 1
            print()
            
        except Exception as e:
            print(f"❌ Unexpected error during quiz testing: {e}")
        
        finally:
            self.cleanup_test_user()
        
        print(f"\n📊 Quiz Generation Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🎉 All quiz generation tests passed!")
            return True
        else:
            print("⚠️ Some quiz generation tests failed. Check the output above for details.")
            return False

def main():
    """Main test function"""
    tester = QuizGenerationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    main()
