#!/usr/bin/env python3
"""
Master test runner for the entire AISE project using pytest
Runs all test suites and provides comprehensive reporting
"""

import pytest
import sys
import time
from pathlib import Path

#!/usr/bin/env python3
"""
Master test runner for the entire AISE project using pytest
Runs all test suites and provides comprehensive reporting
"""

import pytest
import sys
import subprocess
import time
from pathlib import Path

# Test configuration - Maps test names to their file patterns
TEST_MODULES = [
    {
        "name": "Authentication System",
        "pattern": "test_authentication_system.py",
        "description": "User registration, login, profile management"
    },
    {
        "name": "Quiz Generation",
        "pattern": "test_quiz_generation.py", 
        "description": "Adaptive quiz creation, topics, model health"
    },
    {
        "name": "Quiz Evaluation",
        "pattern": "test_quiz_evaluation.py",
        "description": "Scoring, progress tracking, level progression"
    },
    {
        "name": "Chat Assistant",
        "pattern": "test_chat_assistant.py",
        "description": "AI chat functionality, teacher chat"
    },
    {
        "name": "Performance Analytics",
        "pattern": "test_performance_analytics.py",
        "description": "User analytics, progress metrics"
    },
    {
        "name": "Question Assistant",
        "pattern": "test_question_assistant.py",
        "description": "Q&A functionality and English learning support"
    },
    {
        "name": "First Quiz Flag",
        "pattern": "test_first_quiz_flag.py",
        "description": "First quiz completion tracking"
    },
    {
        "name": "Reading Comprehension",
        "pattern": "test_reading_comprehension.py",
        "description": "Reading quiz functionality"
    }
]


class TestSuiteRunner:
    """Pytest-based test suite runner for AISE project"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = []
        
    def run_individual_test(self, test_pattern, test_name, description):
        """Run a single test file using pytest"""
        test_file = self.test_dir / test_pattern
        
        print(f"📋 {test_name}")
        print(f"   {description}")
        print("-" * 60)
        
        if not test_file.exists():
            print(f"   ⚠️ Test file not found: {test_pattern}")
            return False, 0, "File not found"
        
        try:
            start_time = time.time()
            
            # Run pytest for this specific file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_file),
                "-v",
                "--tb=short",
                "--no-header"
            ], capture_output=True, text=True, cwd=self.test_dir)
            
            duration = time.time() - start_time
            
            # Check if tests passed
            success = result.returncode == 0
            
            # Print pytest output
            if result.stdout:
                print(result.stdout)
            if result.stderr and not success:
                print("STDERR:", result.stderr)
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status} - {test_name} ({duration:.1f}s)")
            
            return success, duration, None
            
        except Exception as e:
            print(f"   ❌ Error running test {test_pattern}: {e}")
            return False, 0, str(e)
    
    def run_all_tests(self):
        """Run all test suites using pytest"""
        print("🚀 AISE Project - Comprehensive Test Suite (pytest)")
        print("=" * 60)
        print("Running all functionality tests...\n")
        
        start_time = time.time()
        
        for test_info in TEST_MODULES:
            success, duration, error = self.run_individual_test(
                test_info["pattern"],
                test_info["name"],
                test_info["description"]
            )
            
            self.results.append({
                "name": test_info["name"],
                "result": success,
                "duration": duration,
                "pattern": test_info["pattern"],
                "error": error
            })
            
            print("\n" + "=" * 60 + "\n")
        
        self.print_summary(time.time() - start_time)
        return all(result["result"] for result in self.results)
    
    def print_summary(self, total_duration):
        """Print comprehensive test summary"""
        passed_tests = sum(1 for result in self.results if result["result"])
        total_tests = len(self.results)
        
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
        
        for result in self.results:
            status_icon = "✅" if result["result"] else "❌"
            duration_str = f"({result['duration']:.1f}s)" if result['duration'] > 0 else "(not run)"
            
            print(f"{status_icon} {result['name']} {duration_str}")
            
            if not result["result"] and result["error"]:
                print(f"    Error: {result['error']}")
        
        print()
        
        # Performance insights
        if self.results:
            slowest_test = max(self.results, key=lambda x: x['duration'])
            fastest_test = min([r for r in self.results if r['duration'] > 0], 
                              key=lambda x: x['duration'], default=None)
            
            print("⚡ PERFORMANCE INSIGHTS:")
            print(f"   Slowest: {slowest_test['name']} ({slowest_test['duration']:.1f}s)")
            if fastest_test:
                print(f"   Fastest: {fastest_test['name']} ({fastest_test['duration']:.1f}s)")
            print()
        
        # Failure analysis
        failed_tests = [r for r in self.results if not r["result"]]
        if failed_tests:
            print("🔍 FAILURE ANALYSIS:")
            print("-" * 60)
            for failed in failed_tests:
                print(f"❌ {failed['name']}")
                if failed["error"]:
                    print(f"    Issue: {failed['error']}")
                else:
                    print(f"    Issue: Test execution failed - check individual test output")
            print()
            
            # Setup and Troubleshooting
            print("💡 SETUP AND TROUBLESHOOTING:")
            print("   1. Check that backend and frontend services are running")
            print("   2. Verify MongoDB is accessible")
            print("   3. Ensure Ollama/AI model is running (for chat tests)")
            print("   4. Check network connectivity to localhost:8000")
            print("   5. Review individual test outputs above for specific errors")
            print("   6. Install pytest: pip install pytest")
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


# Pytest test functions for integration with pytest discovery
class TestAISEProject:
    """Pytest test class for AISE project components"""
    
    @pytest.fixture(scope="class")
    def test_runner(self):
        """Fixture to provide test runner instance"""
        return TestSuiteRunner()
    
    def test_authentication_system(self, test_runner):
        """Test authentication system functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_authentication_system.py",
            "Authentication System",
            "User registration, login, profile management"
        )
        assert success, f"Authentication system tests failed: {error}"
    
    def test_quiz_generation(self, test_runner):
        """Test quiz generation functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_quiz_generation.py",
            "Quiz Generation",
            "Adaptive quiz creation, topics, model health"
        )
        assert success, f"Quiz generation tests failed: {error}"
    
    def test_quiz_evaluation(self, test_runner):
        """Test quiz evaluation functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_quiz_evaluation.py",
            "Quiz Evaluation",
            "Scoring, progress tracking, level progression"
        )
        assert success, f"Quiz evaluation tests failed: {error}"
    
    def test_chat_assistant(self, test_runner):
        """Test chat assistant functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_chat_assistant.py",
            "Chat Assistant",
            "AI chat functionality, teacher chat"
        )
        assert success, f"Chat assistant tests failed: {error}"
    
    def test_performance_analytics(self, test_runner):
        """Test performance analytics functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_performance_analytics.py",
            "Performance Analytics",
            "User analytics, progress metrics"
        )
        assert success, f"Performance analytics tests failed: {error}"
    
    def test_question_assistant(self, test_runner):
        """Test question assistant functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_question_assistant.py",
            "Question Assistant",
            "Q&A functionality and English learning support"
        )
        assert success, f"Question assistant tests failed: {error}"
    
    def test_first_quiz_flag(self, test_runner):
        """Test first quiz flag functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_first_quiz_flag.py",
            "First Quiz Flag",
            "First quiz completion tracking"
        )
        assert success, f"First quiz flag tests failed: {error}"
    
    def test_reading_comprehension(self, test_runner):
        """Test reading comprehension functionality"""
        success, _, error = test_runner.run_individual_test(
            "test_reading_comprehension.py",
            "Reading Comprehension",
            "Reading quiz functionality"
        )
        assert success, f"Reading comprehension tests failed: {error}"


def run_all_tests():
    """Legacy function to run all tests - maintained for backward compatibility"""
    runner = TestSuiteRunner()
    return runner.run_all_tests()


def main():
    """Main function - can be called directly or via pytest"""
    if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        # Run via pytest
        pytest.main([__file__, "-v"])
    else:
        # Run via custom runner
        success = run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
