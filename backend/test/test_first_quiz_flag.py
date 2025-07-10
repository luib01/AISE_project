#!/usr/bin/env python3
"""
Test script to verify that users who have completed their first quiz 
do not see "Take Your First Quiz" option upon sign in.
"""

import requests
import json
import random

# Test configuration
BACKEND_URL = "http://localhost:8000"

def get_test_user():
    """Generate a test user with random username"""
    return {
        "username": f"first_{random.randint(100, 999)}",
        "password": "password123"
    }

def test_first_quiz_completion_flag():
    """Test that the first quiz completion flag is properly handled"""
    print("🧪 Testing first quiz completion flag...\n")
    
    # Test with a new user
    new_user = get_test_user()
    
    try:
        print("1. Testing NEW USER (should see 'Take Your First Quiz'):")
        
        # Register new user
        register_response = requests.post(f"{BACKEND_URL}/api/auth/signup", json=new_user)
        print(f"   Registration: {register_response.status_code}")
        
        # Sign in new user
        signin_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json=new_user)
        
        if signin_response.status_code == 200:
            signin_data = signin_response.json()
            user_data = signin_data.get("data", {})
            
            has_completed_first_quiz = user_data.get("has_completed_first_quiz", None)
            print(f"   ✅ Sign in successful")
            print(f"   has_completed_first_quiz: {has_completed_first_quiz}")
            
            if has_completed_first_quiz == False:
                print("   ✅ CORRECT: New user should see 'Take Your First Quiz'")
            else:
                print("   ❌ ERROR: New user should not have completed first quiz")
            
            # Get session token for further testing
            token = user_data.get("session_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Simulate completing first quiz
            print("\n2. Simulating first quiz completion...")
            
            # Generate and submit a quiz
            quiz_request = {
                "topic": "Grammar",
                "num_questions": 4,
                "previous_questions": []
            }
            
            quiz_response = requests.post(
                f"{BACKEND_URL}/api/generate-adaptive-quiz/", 
                json=quiz_request, 
                headers=headers
            )
            
            if quiz_response.status_code == 200:
                print("   ✅ Quiz generated successfully")
                
                # Submit quiz results (simulate answering all questions correctly)
                quiz_data = quiz_response.json()
                questions = quiz_data.get("questions", [])
                
                # Create quiz submission with correct answers
                quiz_submission = {
                    "quiz_data": {
                        "questions": []
                    },
                    "score": 100,  # 100% correct
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
                
                # Submit quiz
                submit_response = requests.post(
                    f"{BACKEND_URL}/api/evaluate-quiz/",
                    json=quiz_submission,
                    headers=headers
                )
                
                if submit_response.status_code == 200:
                    print("   ✅ Quiz submitted successfully")
                    
                    # Sign in again to check updated flag
                    print("\n3. Testing RETURNING USER (should see 'Take Adaptive Quiz'):")
                    
                    signin_again_response = requests.post(f"{BACKEND_URL}/api/auth/signin", json=new_user)
                    
                    if signin_again_response.status_code == 200:
                        signin_again_data = signin_again_response.json()
                        user_data_updated = signin_again_data.get("data", {})
                        
                        has_completed_first_quiz_updated = user_data_updated.get("has_completed_first_quiz", None)
                        print(f"   ✅ Sign in successful")
                        print(f"   has_completed_first_quiz: {has_completed_first_quiz_updated}")
                        
                        if has_completed_first_quiz_updated == True:
                            print("   ✅ SUCCESS: Returning user correctly shows completed first quiz!")
                            return True
                        else:
                            print("   ❌ ERROR: User should have completed first quiz flag set to True")
                            return False
                    else:
                        print(f"   ❌ Failed to sign in again: {signin_again_response.status_code}")
                        return False
                else:
                    print(f"   ❌ Failed to submit quiz: {submit_response.status_code}")
                    print(f"   Response: {submit_response.text}")
                    return False
            else:
                print(f"   ❌ Failed to generate quiz: {quiz_response.status_code}")
                return False
        else:
            print(f"   ❌ Sign in failed: {signin_response.status_code}")
            print(f"   Response: {signin_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main function for test runner compatibility"""
    print("🚀 Testing first quiz completion logic...\n")
    success = test_first_quiz_completion_flag()
    print(f"\n{'🎉 TEST PASSED!' if success else '❌ TEST FAILED!'}")
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
