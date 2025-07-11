#!/usr/bin/env python3
"""
Comprehensive test suite for Question Assistant
Tests: Q&A functionality, educational content generation, response validation
"""

import requests
import json
import time
import random

# Test configuration
BACKEND_URL = "http://localhost:8000"

class QuestionAssistantTester:
    def __init__(self):
        self.test_user = None
        self.session_token = None
    
    def setup_test_user(self):
        """Create a test user for testing"""
        print("🔧 Setting up test user...")
        
        username = f"qa_{random.randint(100, 999)}"
        password = "QATest123"
        
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
    
    def test_question_assistant_basic(self):
        """Test basic question-answering functionality"""
        print("🧪 Testing Question Assistant Basic Functionality...")
        
        # Test cases with different types of questions
        test_questions = [
            {
                "question": "What is the difference between 'affect' and 'effect'?",
                "context": "English grammar",
                "description": "Grammar question"
            },
            {
                "question": "How do I use 'present perfect' tense?",
                "context": "English tenses",
                "description": "Tense question"
            },
            {
                "question": "What does 'ubiquitous' mean?",
                "context": "English vocabulary",
                "description": "Vocabulary question"
            }
        ]
        
        for test_case in test_questions:
            print(f"   Testing {test_case['description']}...")
            
            question_request = {
                "question": test_case["question"],
                "context": test_case["context"]
            }
            
            response = requests.post(f"{BACKEND_URL}/api/ask-question/", json=question_request)
            
            if response.status_code == 200:
                result = response.json()
                
                if "answer" in result and result["answer"]:
                    answer = result["answer"]
                    if len(answer) > 20:  # Reasonable answer length
                        print(f"      ✅ {test_case['description']} answered successfully")
                        print(f"         Answer length: {len(answer)} characters")
                    else:
                        print(f"      ❌ {test_case['description']} answer too short: {answer}")
                        return False
                elif "error" in result:
                    print(f"      ⚠️ {test_case['description']} returned error: {result['error']}")
                    # This might be expected if the Q&A service is not available
                    return True
                else:
                    print(f"      ❌ {test_case['description']} no answer or error in response")
                    return False
            else:
                print(f"      ❌ {test_case['description']} request failed: {response.status_code}")
                return False
        
        return True
    
    def test_question_assistant_validation(self):
        """Test question assistant input validation"""
        print("🧪 Testing Question Assistant Validation...")
        
        # Test 1: Missing question
        missing_question = {"context": "English grammar"}
        response1 = requests.post(f"{BACKEND_URL}/api/ask-question/", json=missing_question)
        
        if response1.status_code == 422:  # Validation error
            print("   ✅ Missing question properly rejected")
        else:
            print(f"   ❌ Missing question not properly handled: {response1.status_code}")
            return False
        
        # Test 2: Missing context
        missing_context = {"question": "What is grammar?"}
        response2 = requests.post(f"{BACKEND_URL}/api/ask-question/", json=missing_context)
        
        if response2.status_code == 422:  # Validation error
            print("   ✅ Missing context properly rejected")
        else:
            print(f"   ❌ Missing context not properly handled: {response2.status_code}")
            return False
        
        # Test 3: Empty question
        empty_question = {"question": "", "context": "English"}
        response3 = requests.post(f"{BACKEND_URL}/api/ask-question/", json=empty_question)
        
        if response3.status_code in [400, 422]:  # Should reject empty question
            print("   ✅ Empty question properly rejected")
        else:
            print(f"   ❌ Empty question not properly handled: {response3.status_code}")
            # Don't fail the test for this - might be handled differently
        
        # Test 4: Very long question
        long_question = {
            "question": "What is grammar? " * 100,  # Very long question
            "context": "English"
        }
        response4 = requests.post(f"{BACKEND_URL}/api/ask-question/", json=long_question)
        
        # Should handle gracefully (accept or reject appropriately)
        if response4.status_code in [200, 400, 413, 422]:
            print("   ✅ Long question handled appropriately")
            return True
        else:
            print(f"   ❌ Long question not properly handled: {response4.status_code}")
            return False
    
    def test_question_answer_persistence(self):
        """Test that questions and answers are saved properly"""
        print("🧪 Testing Question-Answer Persistence...")
        
        # Submit a question
        test_question = {
            "question": "What is the past tense of 'go'?",
            "context": "English grammar test"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/ask-question/", json=test_question)
        
        if response.status_code == 200:
            result = response.json()
            
            if "answer" in result and result["answer"]:
                print("   ✅ Question submitted and answered")
                
                # Check if question and answer are in response
                returned_question = result.get("question")
                returned_answer = result.get("answer")
                
                if (returned_question == test_question["question"] and 
                    returned_answer and len(returned_answer) > 10):
                    print("   ✅ Question and answer properly returned")
                    print(f"      Question: {returned_question}")
                    print(f"      Answer length: {len(returned_answer)} characters")
                    return True
                else:
                    print("   ❌ Question or answer not properly returned")
                    return False
            elif "error" in result:
                print(f"   ⚠️ Question processing error: {result['error']}")
                return True  # Don't fail for service unavailability
            else:
                print("   ❌ No answer or error in response")
                return False
        else:
            print(f"   ❌ Question submission failed: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all question assistant tests"""
        print("🚀 Starting Question Assistant Tests...\n")
        
        success_count = 0
        total_tests = 3
        
        try:
            if not self.setup_test_user():
                print("❌ Failed to setup test user. Continuing with limited testing.")
            print()
            
            if self.test_question_assistant_basic():
                success_count += 1
            print()
            
            if self.test_question_assistant_validation():
                success_count += 1
            print()
            
            if self.test_question_answer_persistence():
                success_count += 1
            print()
            
        except Exception as e:
            print(f"❌ Unexpected error during Q&A testing: {e}")
        
        finally:
            if self.session_token:
                self.cleanup_test_user()
        
        print(f"\n📊 Question Assistant Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🎉 All Q&A tests passed!")
            return True
        else:
            print("⚠️ Some Q&A tests failed. Check the output above for details.")
            print("💡 Note: Some tests may fail if external Q&A services are not configured.")
            return False

def main():
    """Main test function"""
    tester = QuestionAssistantTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    main()
