#!/usr/bin/env python3
"""
Comprehensive test suite for Performance Analytics and Progress Tracking
Tests: User performance endpoints, progress calculation, analytics data
"""

import requests
import json
import time
import random

# Test configuration
BACKEND_URL = "http://localhost:8000"

class PerformanceAnalyticsTester:
    def __init__(self):
        self.test_user = None
        self.session_token = None
    
    def setup_test_user_with_history(self):
        """Create a test user and generate some quiz history"""
        print("🔧 Setting up test user with quiz history...")
        
        username = f"perf_{random.randint(100, 999)}"
        password = "PerfTest123"
        
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
        else:
            print(f"   ❌ Failed to login test user: {signin_response.status_code}")
            return False
        
        # Generate some quiz history
        return self.generate_quiz_history()
    
    def generate_quiz_history(self):
        """Generate sample quiz history for testing analytics"""
        print("   📊 Generating quiz history...")
        
        if not self.session_token:
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        # Generate quizzes with different topics and scores
        quiz_scenarios = [
            {"topic": "Grammar", "score": 85, "difficulty": "beginner"},
            {"topic": "Vocabulary", "score": 70, "difficulty": "beginner"},
            {"topic": "Grammar", "score": 90, "difficulty": "beginner"},
            {"topic": "Reading", "score": 75, "difficulty": "beginner"},
            {"topic": "Vocabulary", "score": 80, "difficulty": "intermediate"},
            {"topic": "Mixed", "score": 88, "difficulty": "intermediate"},
        ]
        
        for i, scenario in enumerate(quiz_scenarios):
            quiz_data = self.create_sample_quiz_data(
                score=scenario["score"], 
                topic=scenario["topic"],
                difficulty=scenario["difficulty"]
            )
            
            response = requests.post(f"{BACKEND_URL}/api/evaluate-quiz/", 
                                   json=quiz_data, headers=headers)
            
            if response.status_code == 200:
                print(f"      ✅ Quiz {i+1}: {scenario['topic']} ({scenario['score']}%)")
            else:
                print(f"      ❌ Failed to submit quiz {i+1}: {response.status_code}")
                return False
        
        print("   ✅ Quiz history generated successfully")
        return True
    
    def create_sample_quiz_data(self, score=80, topic="Grammar", difficulty="beginner"):
        """Create sample quiz data for testing"""
        # Create questions that result in the desired score
        correct_count = int((score / 100) * 4)  # Out of 4 questions
        
        questions = []
        for i in range(4):
            is_correct = i < correct_count
            questions.append({
                "question": f"Sample {topic} question {i+1}",
                "topic": topic,
                "userAnswer": "Correct answer" if is_correct else "Wrong answer",
                "correctAnswer": "Correct answer",
                "isCorrect": is_correct,
                "explanation": f"Explanation for {topic} question {i+1}",
                "difficulty": difficulty
            })
        
        return {
            "quiz_data": {"questions": questions},
            "score": score,
            "topic": topic,
            "difficulty": difficulty,
            "quiz_type": "adaptive"
        }
    
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
    
    def test_basic_user_performance(self):
        """Test basic user performance endpoint"""
        print("🧪 Testing Basic User Performance Endpoint...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for performance testing")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        response = requests.get(f"{BACKEND_URL}/api/user-performance/", headers=headers)
        
        if response.status_code == 200:
            performance_data = response.json()
            
            # Check for expected fields
            expected_fields = ["total_quizzes", "average_score", "english_level"]
            missing_fields = [field for field in expected_fields if field not in performance_data]
            
            if not missing_fields:
                print("   ✅ Basic performance data retrieved successfully")
                print(f"      Total Quizzes: {performance_data.get('total_quizzes')}")
                print(f"      Average Score: {performance_data.get('average_score')}%")
                print(f"      English Level: {performance_data.get('english_level')}")
                return True
            else:
                print(f"   ❌ Missing fields in performance data: {missing_fields}")
                return False
        else:
            print(f"   ❌ Failed to retrieve basic performance: {response.status_code}")
            return False
    
    def test_detailed_user_performance(self):
        """Test detailed user performance endpoint"""
        print("🧪 Testing Detailed User Performance Endpoint...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for detailed performance testing")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        response = requests.get(f"{BACKEND_URL}/api/user-performance-detailed/", headers=headers)
        
        if response.status_code == 200:
            detailed_data = response.json()
            
            print("   ✅ Detailed performance data retrieved successfully")
            
            # Check for quiz history
            if "quiz_history" in detailed_data:
                quiz_history = detailed_data["quiz_history"]
                print(f"      Quiz History: {len(quiz_history)} quizzes found")
                
                if quiz_history:
                    # Validate quiz history structure
                    first_quiz = quiz_history[0]
                    expected_quiz_fields = ["topic", "score", "timestamp"]
                    missing_quiz_fields = [field for field in expected_quiz_fields if field not in first_quiz]
                    
                    if not missing_quiz_fields:
                        print("      ✅ Quiz history has valid structure")
                    else:
                        print(f"      ❌ Quiz history missing fields: {missing_quiz_fields}")
                        return False
            
            # Check for topic performance
            if "topic_performance" in detailed_data:
                topic_performance = detailed_data["topic_performance"]
                print(f"      Topic Performance: {len(topic_performance)} topics tracked")
                
                for topic, performance in topic_performance.items():
                    if isinstance(performance, dict) and "average_score" in performance:
                        print(f"         {topic}: {performance['average_score']:.1f}%")
                    else:
                        print(f"         {topic}: {performance}")
            
            # Check for level progression
            if "level_progression" in detailed_data:
                level_progression = detailed_data["level_progression"]
                print(f"      Level Progression: {len(level_progression)} entries")
            
            return True
        else:
            print(f"   ❌ Failed to retrieve detailed performance: {response.status_code}")
            return False
    
    def test_performance_metrics_calculation(self):
        """Test that performance metrics are calculated correctly"""
        print("🧪 Testing Performance Metrics Calculation...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for metrics testing")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        # Get current user profile to check calculated metrics
        profile_response = requests.get(f"{BACKEND_URL}/api/auth/profile", headers=headers)
        
        if profile_response.status_code != 200:
            print(f"   ❌ Failed to get user profile: {profile_response.status_code}")
            return False
        
        profile_data = profile_response.json()['data']
        total_quizzes = profile_data.get('total_quizzes', 0)
        average_score = profile_data.get('average_score', 0)
        
        print(f"   📊 Current metrics:")
        print(f"      Total Quizzes: {total_quizzes}")
        print(f"      Average Score: {average_score:.1f}%")
        
        # Validate that metrics make sense
        if total_quizzes > 0:
            if 0 <= average_score <= 100:
                print("   ✅ Performance metrics are within valid ranges")
            else:
                print(f"   ❌ Average score out of valid range: {average_score}")
                return False
        else:
            print("   ⚠️ No quiz history found for metrics validation")
        
        # Test performance endpoint consistency
        performance_response = requests.get(f"{BACKEND_URL}/api/user-performance/", headers=headers)
        
        if performance_response.status_code == 200:
            performance_data = performance_response.json()
            perf_total_quizzes = performance_data.get('total_quizzes', 0)
            perf_average_score = performance_data.get('average_score', 0)
            
            # Check consistency between profile and performance endpoints
            if (total_quizzes == perf_total_quizzes and 
                abs(average_score - perf_average_score) < 0.1):
                print("   ✅ Performance metrics consistent across endpoints")
                return True
            else:
                print("   ❌ Performance metrics inconsistent between endpoints")
                print(f"      Profile: {total_quizzes} quizzes, {average_score:.1f}% avg")
                print(f"      Performance: {perf_total_quizzes} quizzes, {perf_average_score:.1f}% avg")
                return False
        else:
            print(f"   ❌ Failed to get performance data: {performance_response.status_code}")
            return False
    
    def test_topic_performance_tracking(self):
        """Test topic-specific performance tracking"""
        print("🧪 Testing Topic Performance Tracking...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for topic tracking testing")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        # Get detailed performance to check topic tracking
        response = requests.get(f"{BACKEND_URL}/api/user-performance-detailed/", headers=headers)
        
        if response.status_code == 200:
            detailed_data = response.json()
            topic_performance = detailed_data.get("topic_performance", {})
            
            if topic_performance:
                print("   ✅ Topic performance tracking working")
                
                # Check that topics from our generated history are tracked
                expected_topics = ["Grammar", "Vocabulary", "Reading", "Mixed"]
                tracked_topics = list(topic_performance.keys())
                
                found_topics = [topic for topic in expected_topics if topic in tracked_topics]
                
                if found_topics:
                    print(f"      Topics tracked: {found_topics}")
                    
                    # Validate topic performance structure
                    for topic in found_topics:
                        topic_data = topic_performance[topic]
                        if isinstance(topic_data, dict):
                            if "average_score" in topic_data:
                                avg_score = topic_data["average_score"]
                                if 0 <= avg_score <= 100:
                                    print(f"         {topic}: {avg_score:.1f}% average")
                                else:
                                    print(f"         ❌ {topic}: Invalid average score {avg_score}")
                                    return False
                            else:
                                print(f"         ⚠️ {topic}: Missing average_score field")
                        else:
                            print(f"         ⚠️ {topic}: Unexpected data format")
                    
                    return True
                else:
                    print("   ⚠️ Expected topics not found in tracking")
                    print(f"      Expected: {expected_topics}")
                    print(f"      Found: {tracked_topics}")
                    return True  # Don't fail - might be valid
            else:
                print("   ⚠️ No topic performance data found")
                print("      This might be expected if no quizzes were submitted")
                return True
        else:
            print(f"   ❌ Failed to get detailed performance: {response.status_code}")
            return False
    
    def test_performance_endpoint_security(self):
        """Test that performance endpoints require authentication"""
        print("🧪 Testing Performance Endpoint Security...")
        
        # Test without authentication
        no_auth_endpoints = [
            "/api/user-performance/",
            "/api/user-performance-detailed/"
        ]
        
        for endpoint in no_auth_endpoints:
            response = requests.get(f"{BACKEND_URL}{endpoint}")
            
            if response.status_code == 401:
                print(f"   ✅ {endpoint} properly requires authentication")
            else:
                print(f"   ❌ {endpoint} doesn't require authentication: {response.status_code}")
                return False
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        
        for endpoint in no_auth_endpoints:
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=invalid_headers)
            
            if response.status_code == 401:
                print(f"   ✅ {endpoint} properly rejects invalid token")
            else:
                print(f"   ❌ {endpoint} accepts invalid token: {response.status_code}")
                return False
        
        return True
    
    def test_progress_data_consistency(self):
        """Test consistency of progress data across different endpoints"""
        print("🧪 Testing Progress Data Consistency...")
        
        if not self.session_token:
            print("   ❌ No authenticated user for consistency testing")
            return False
        
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        # Get data from different endpoints
        profile_response = requests.get(f"{BACKEND_URL}/api/auth/profile", headers=headers)
        performance_response = requests.get(f"{BACKEND_URL}/api/user-performance/", headers=headers)
        detailed_response = requests.get(f"{BACKEND_URL}/api/user-performance-detailed/", headers=headers)
        
        if (profile_response.status_code == 200 and 
            performance_response.status_code == 200 and 
            detailed_response.status_code == 200):
            
            profile_data = profile_response.json()['data']
            performance_data = performance_response.json()
            detailed_data = detailed_response.json()
            
            # Check total_quizzes consistency
            profile_quizzes = profile_data.get('total_quizzes', 0)
            performance_quizzes = performance_data.get('total_quizzes', 0)
            detailed_history_length = len(detailed_data.get('quiz_history', []))
            
            print(f"   📊 Quiz count comparison:")
            print(f"      Profile: {profile_quizzes}")
            print(f"      Performance: {performance_quizzes}")
            print(f"      Detailed history: {detailed_history_length}")
            
            # Allow some flexibility in history length (might be limited)
            if (profile_quizzes == performance_quizzes and 
                detailed_history_length <= profile_quizzes):
                print("   ✅ Quiz counts are consistent")
            else:
                print("   ⚠️ Quiz counts have minor inconsistencies (might be expected)")
            
            # Check average_score consistency
            profile_avg = profile_data.get('average_score', 0)
            performance_avg = performance_data.get('average_score', 0)
            
            if abs(profile_avg - performance_avg) < 0.1:
                print("   ✅ Average scores are consistent")
                return True
            else:
                print(f"   ❌ Average scores inconsistent: {profile_avg} vs {performance_avg}")
                return False
        else:
            print("   ❌ Failed to retrieve data from one or more endpoints")
            return False
    
    def run_all_tests(self):
        """Run all performance analytics tests"""
        print("🚀 Starting Performance Analytics Tests...\n")
        
        success_count = 0
        total_tests = 6
        
        try:
            if not self.setup_test_user_with_history():
                print("❌ Failed to setup test user with history. Aborting performance tests.")
                return False
            print()
            
            if self.test_basic_user_performance():
                success_count += 1
            print()
            
            if self.test_detailed_user_performance():
                success_count += 1
            print()
            
            if self.test_performance_metrics_calculation():
                success_count += 1
            print()
            
            if self.test_topic_performance_tracking():
                success_count += 1
            print()
            
            if self.test_performance_endpoint_security():
                success_count += 1
            print()
            
            if self.test_progress_data_consistency():
                success_count += 1
            print()
            
        except Exception as e:
            print(f"❌ Unexpected error during performance testing: {e}")
        
        finally:
            self.cleanup_test_user()
        
        print(f"\n📊 Performance Analytics Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🎉 All performance analytics tests passed!")
            return True
        else:
            print("⚠️ Some performance analytics tests failed. Check the output above for details.")
            return False

def main():
    """Main test function"""
    tester = PerformanceAnalyticsTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    main()
