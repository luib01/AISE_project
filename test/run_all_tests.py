#!/usr/bin/env python3
"""
Master test runner for the entire AISE project
Runs all test suites and provides comprehensive reporting
"""

import sys
import time
import importlib.util
from pathlib import Path

# Test configuration
TEST_MODULES = [
    {
        "name": "Authentication System",
        "file": "test_authentication_system.py",
        "description": "User registration, login, profile management"
    },
    {
        "name": "Quiz Generation",
        "file": "test_quiz_generation.py", 
        "description": "Adaptive quiz creation, topics, model health"
    },
    {
        "name": "Quiz Evaluation",
        "file": "test_quiz_evaluation.py",
        "description": "Scoring, progress tracking, level progression"
    },
    {
        "name": "Chat Assistant",
        "file": "test_chat_assistant.py",
        "description": "AI chat functionality, teacher chat"
    },
    {
        "name": "Performance Analytics",
        "file": "test_performance_analytics.py",
        "description": "User analytics, progress metrics"
    },
    {
        "name": "Question Assistant",
        "file": "test_question_assistant.py",
        "description": "Q&A functionality, recommendations"
    },
    {
        "name": "First Quiz Flag",
        "file": "test_first_quiz_flag.py",
        "description": "First quiz completion tracking"
    },
    {
        "name": "Reading Comprehension",
        "file": "test_reading_comprehension.py",
        "description": "Reading quiz functionality"
    }
]

def load_and_run_test(test_file_path):
    """Load and run a test module"""
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Run the main function
        if hasattr(test_module, 'main'):
            return test_module.main()
        else:
            print(f"   ❌ Test module {test_file_path.name} has no main() function")
            return False
            
    except Exception as e:
        print(f"   ❌ Error running test {test_file_path.name}: {e}")
        return False

def run_all_tests():
    """Run all test suites"""
    print("🚀 AISE Project - Comprehensive Test Suite")
    print("=" * 60)
    print("Running all functionality tests...\n")
    
    start_time = time.time()
    test_results = []
    
    # Get the test directory path
    test_dir = Path(__file__).parent
    
    for test_info in TEST_MODULES:
        test_file_path = test_dir / test_info["file"]
        
        print(f"📋 {test_info['name']}")
        print(f"   {test_info['description']}")
        print("-" * 60)
        
        if test_file_path.exists():
            test_start = time.time()
            result = load_and_run_test(test_file_path)
            test_duration = time.time() - test_start
            
            test_results.append({
                "name": test_info["name"],
                "result": result,
                "duration": test_duration,
                "file": test_info["file"]
            })
            
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status} - {test_info['name']} ({test_duration:.1f}s)")
        else:
            print(f"   ⚠️ Test file not found: {test_info['file']}")
            test_results.append({
                "name": test_info["name"],
                "result": False,
                "duration": 0,
                "file": test_info["file"],
                "error": "File not found"
            })
        
        print("\n" + "=" * 60 + "\n")
    
    # Print comprehensive summary
    total_duration = time.time() - start_time
    passed_tests = sum(1 for result in test_results if result["result"])
    total_tests = len(test_results)
    
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Total Duration: {total_duration:.1f} seconds")
    print()
    
    # Detailed results
    print("📋 DETAILED RESULTS:")
    print("-" * 60)
    
    for result in test_results:
        status_icon = "✅" if result["result"] else "❌"
        duration_str = f"({result['duration']:.1f}s)" if result['duration'] > 0 else "(not run)"
        
        print(f"{status_icon} {result['name']} {duration_str}")
        
        if not result["result"] and "error" in result:
            print(f"    Error: {result['error']}")
    
    print()
    
    # Performance insights
    if test_results:
        slowest_test = max(test_results, key=lambda x: x['duration'])
        fastest_test = min([r for r in test_results if r['duration'] > 0], 
                          key=lambda x: x['duration'], default=None)
        
        print("⚡ PERFORMANCE INSIGHTS:")
        print(f"   Slowest: {slowest_test['name']} ({slowest_test['duration']:.1f}s)")
        if fastest_test:
            print(f"   Fastest: {fastest_test['name']} ({fastest_test['duration']:.1f}s)")
        print()
    
    # Failure analysis
    failed_tests = [r for r in test_results if not r["result"]]
    if failed_tests:
        print("🔍 FAILURE ANALYSIS:")
        print("-" * 60)
        for failed in failed_tests:
            print(f"❌ {failed['name']}")
            if "error" in failed:
                print(f"    Issue: {failed['error']}")
            else:
                print(f"    Issue: Test execution failed - check individual test output")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        print("   1. Check that backend and frontend services are running")
        print("   2. Verify MongoDB is accessible")
        print("   3. Ensure Ollama/AI model is running (for chat tests)")
        print("   4. Check network connectivity to localhost:8000")
        print("   5. Review individual test outputs above for specific errors")
        print()
    
    # Success message
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("   The AISE project is functioning correctly across all components.")
    elif passed_tests > total_tests * 0.8:  # 80% pass rate
        print("✅ MOSTLY SUCCESSFUL!")
        print(f"   {passed_tests}/{total_tests} test suites passed.")
        print("   Review failed tests for minor issues.")
    else:
        print("⚠️ SIGNIFICANT ISSUES DETECTED!")
        print(f"   Only {passed_tests}/{total_tests} test suites passed.")
        print("   Review failed tests and system configuration.")
    
    print()
    print("=" * 60)
    print("Test suite completed.")
    
    return passed_tests == total_tests

def main():
    """Main function"""
    success = run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
