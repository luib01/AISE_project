#!/usr/bin/env python3
"""
Test script to verify that Reading comprehension questions include passages.
"""

import requests
import json
import random
import time

# Test configuration
BACKEND_URL = "http://localhost:8000"

def get_test_user():
    """Generate a test user with random username"""
    return {
        "username": f"read_{random.randint(100, 999)}",
        "password": "password123"
    }

def test_reading_comprehension():
    """Test that Reading topic generates questions with passages"""
    print("🧪 Testing Reading comprehension feature...\n")
    
    test_user = get_test_user()
    
    try:
        # Register and login
        requests.post(f"{BACKEND_URL}/api/auth/signup", json=test_user)
        login_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json=test_user)
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["session_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test Reading quiz generation
            quiz_request = {
                "topic": "Reading",
                "num_questions": 4,
                "previous_questions": []
            }
            
            print("📚 Generating Reading comprehension quiz...")
            quiz_response = requests.post(
                f"{BACKEND_URL}/api/generate-adaptive-quiz/", 
                json=quiz_request, 
                headers=headers
            )
            
            if quiz_response.status_code == 200:
                quiz_data = quiz_response.json()
                questions = quiz_data.get("questions", [])
                
                print(f"✅ Generated {len(questions)} questions\n")
                
                # Check if questions have passages
                has_passages = False
                for i, question in enumerate(questions):
                    print(f"📖 Question {i+1}:")
                    print(f"   Topic: {question.get('topic', 'N/A')}")
                    
                    if 'passage' in question and question['passage']:
                        has_passages = True
                        print(f"   ✅ Has passage ({len(question['passage'])} characters)")
                        print(f"   Passage preview: {question['passage'][:100]}...")
                    else:
                        print(f"   ❌ No passage found")
                    
                    print(f"   Question: {question.get('question', 'N/A')[:80]}...")
                    print()
                
                if has_passages:
                    print("🎉 SUCCESS: Reading questions include comprehension passages!")
                    return True
                else:
                    print("❌ FAIL: No reading passages found in questions")
                    return False
            else:
                print(f"❌ Failed to generate quiz: {quiz_response.status_code}")
                print(f"Response: {quiz_response.text}")
                return False
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_other_topics():
    """Test that non-Reading topics don't include passages"""
    print("🧪 Testing that other topics don't include passages...\n")
    
    test_user = get_test_user()
    
    try:
        # Register and login
        requests.post(f"{BACKEND_URL}/api/auth/signup", json=test_user)
        login_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json=test_user)
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["session_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test Grammar quiz generation
            quiz_request = {
                "topic": "Grammar",
                "num_questions": 2,
                "previous_questions": []
            }
            
            print("📝 Generating Grammar quiz...")
            quiz_response = requests.post(
                f"{BACKEND_URL}/api/generate-adaptive-quiz/", 
                json=quiz_request, 
                headers=headers
            )
            
            if quiz_response.status_code == 200:
                quiz_data = quiz_response.json()
                questions = quiz_data.get("questions", [])
                
                print(f"✅ Generated {len(questions)} Grammar questions")
                
                # Check that Grammar questions don't have passages
                has_passages = False
                for i, question in enumerate(questions):
                    if 'passage' in question and question['passage']:
                        has_passages = True
                        print(f"   ❌ Grammar question {i+1} unexpectedly has passage")
                    else:
                        print(f"   ✅ Grammar question {i+1} correctly has no passage")
                
                if not has_passages:
                    print("🎉 SUCCESS: Grammar questions correctly don't include passages!")
                    return True
                else:
                    print("❌ FAIL: Grammar questions incorrectly include passages")
                    return False
            else:
                print(f"❌ Failed to generate Grammar quiz: {quiz_response.status_code}")
                return False
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main function for test runner compatibility"""
    print("🚀 Testing Reading comprehension passage feature...\n")
    
    # Test Reading comprehension
    reading_success = test_reading_comprehension()
    print()
    
    # Test other topics
    other_success = test_other_topics()
    print()
    
    overall_success = reading_success and other_success
    print(f"{'🎉 ALL TESTS PASSED!' if overall_success else '❌ SOME TESTS FAILED!'}")
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
