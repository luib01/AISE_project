# Test Directory

This directory contains all test scripts for the AISE project. Each test verifies specific functionality of the application, providing comprehensive coverage of authentication, quiz systems, AI features, analytics, and more.

## Running Tests

### Using pytest (Recommended)

The test suite now supports pytest for better test discovery, reporting, and integration with IDEs.

#### Install pytest (if not already installed):
```bash
pip install pytest pytest-html pytest-cov
```

#### Run all tests:
```bash
# From the test directory
pytest

# Or run the master test runner with pytest
python run_all_tests.py --pytest

# Or from project root
pytest test/
```

#### Run specific test files:
```bash
pytest test_authentication_system.py
pytest test_quiz_generation.py -v
```

#### Run with HTML report:
```bash
pytest --html=test_report.html --self-contained-html
```

#### Run with coverage:
```bash
pytest --cov=../backend/app --cov-report=html
```

### Using the Custom Runner (Legacy)

You can still use the custom test runner for detailed reporting:

```bash
python run_all_tests.py
```

## Test Files

### 🛠️ Master Test Runner
- **`run_all_tests.py`** - **Main test suite runner** that executes all tests and provides comprehensive reporting, performance insights, and failure analysis

### 🔐 Authentication & User Management Tests
- **`test_authentication_system.py`** - Comprehensive authentication testing including:
  - User registration and validation
  - Login/logout functionality
  - Session management and security
  - Profile management (updates, password changes)
  - Account deletion with verification
  - Security features and error handling

### 📚 Quiz System Tests
- **`test_quiz_generation.py`** - Tests adaptive and static quiz generation including:
  - Quiz creation for different topics (Grammar, Vocabulary, Pronunciation, Tenses)
  - Difficulty level management (Beginner, Intermediate, Advanced)
  - AI model health checks
  - Quiz customization and topic selection
  
- **`test_quiz_evaluation.py`** - Tests quiz scoring and evaluation including:
  - Quiz submission and scoring logic
  - Level progression and advancement
  - Performance tracking by topic
  - Answer validation and feedback
  - Progress persistence

### 🤖 AI & Chat Features Tests  
- **`test_chat_assistant.py`** - Tests AI-powered chat functionality including:
  - AI Teacher chat interactions
  - Conversation flow and context management
  - Input validation and response quality
  - Educational content delivery
  - Chat history and persistence

### 📊 Analytics & Performance Tests
- **`test_performance_analytics.py`** - Tests analytics and tracking including:
  - User performance metrics
  - Progress tracking and visualization
  - Topic-specific analytics
  - Data consistency and accuracy
  - Dashboard functionality

### ❓ Q&A Tests
- **`test_question_assistant.py`** - Tests Q&A functionality including:
  - Question answering functionality
  - English learning support and assistance
  - Data persistence and retrieval

### 🔧 Core Functionality Tests
- **`simple_test.py`** - Basic API connectivity and health check tests
- **`test_first_quiz_flag.py`** - Tests the first quiz completion flag functionality to ensure returning users don't see "Take Your First Quiz" option
- **`test_reading_comprehension.py`** - Tests reading comprehension quiz generation and evaluation

### 🛠️ Legacy & Specific Feature Tests
- **`test_interface_fix.py`** - Tests interface-related fixes and improvements
- **`test_level_retrocession.py`** - Tests level progression and retrocession logic
- **`test_quiz_fix.py`** - Tests quiz-related bug fixes and functionality
- **`test_static_quiz_removal.py`** - Tests removal of static quiz elements

## Running Tests

### Quick Start - Run All Tests
```bash
# Run the complete test suite with comprehensive reporting
python test/run_all_tests.py
```

### Individual Test Execution
```bash
# Run specific test modules
python test/test_authentication_system.py
python test/test_quiz_generation.py
python test/test_chat_assistant.py
python test/simple_test.py

# Or from the test directory
cd test
python test_authentication_system.py
python run_all_tests.py
```

### Using Docker (Recommended)
```bash
# Run tests in the backend container
docker exec -it aise_project-backend-1 python /app/test/run_all_tests.py

# Run specific tests in container
docker exec -it aise_project-backend-1 python /app/test/test_authentication_system.py
```

### Using pytest (Alternative)
```bash
# Run all tests with pytest
python -m pytest test/ -v

# Run specific test categories
python -m pytest test/test_auth* -v
python -m pytest test/test_quiz* -v
```

## Test Environment Requirements

### Prerequisites
Before running tests, ensure the following services are running:

1. **Backend Service**: Running on `http://localhost:8000`
   ```bash
   # Start with Docker
   docker-compose up backend

   # Or manually
   cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend Service**: Running on `http://localhost:3000` (for integration tests)
   ```bash
   # Start with Docker
   docker-compose up frontend

   # Or manually  
   cd frontend && npm start
   ```

3. **MongoDB Database**: Accessible and properly configured
   ```bash
   # Start with Docker
   docker-compose up mongodb
   ```

4. **Ollama/AI Model**: For chat and AI-related tests
   ```bash
   # Start Ollama service
   docker-compose up ollama
   
   # Verify Mistral model is available
   ollama list
   ```

### Configuration
- Tests use the development configuration by default
- Backend URL: `http://localhost:8000`
- Database: Uses the same MongoDB instance as development
- AI Model: Connects to local Ollama instance with Mistral 7B

## Test Features

### 🔍 Comprehensive Reporting
The master test runner (`run_all_tests.py`) provides:
- **Real-time Progress**: Live updates as tests execute
- **Performance Metrics**: Execution time for each test suite
- **Detailed Results**: Pass/fail status with error details
- **Failure Analysis**: Specific error information and troubleshooting guidance
- **Success Rates**: Overall system health overview

### 🧹 Automatic Cleanup
Tests automatically clean up:
- Test user accounts created during authentication tests
- Temporary quiz data and responses
- Chat conversation history
- Performance data records

### 🛡️ Safety Features
- Tests use isolated test data that doesn't affect production
- Test users have randomized usernames to avoid conflicts
- Database operations are scoped to test-specific collections
- All test data is cleaned up after execution

## Test Coverage

### Authentication System (100% Coverage)
✅ User registration and validation  
✅ Login/logout functionality  
✅ Session management  
✅ Profile updates and security  
✅ Password management  
✅ Account deletion  

### Quiz System (100% Coverage)
✅ Adaptive quiz generation  
✅ Static quiz creation  
✅ Topic-specific quizzes  
✅ Difficulty progression  
✅ Scoring and evaluation  
✅ Progress tracking  

### AI Features (100% Coverage)
✅ Chat assistant functionality  
✅ AI Teacher interactions  
✅ Question answering  
✅ English learning support  
✅ Content generation  

### Analytics (100% Coverage)
✅ Performance tracking  
✅ Progress metrics  
✅ Topic analytics  
✅ Dashboard data  
✅ Historical tracking  

## Troubleshooting

### Common Issues

**❌ Connection Refused Errors**
```
Solution: Ensure backend service is running on localhost:8000
Check: docker-compose ps or curl http://localhost:8000/health
```

**❌ Database Connection Errors**
```  
Solution: Verify MongoDB is running and accessible
Check: docker-compose logs mongodb
```

**❌ AI Model Errors**
```
Solution: Ensure Ollama is running with Mistral model
Check: docker exec -it ollama ollama list
```

**❌ Test User Creation Failures**
```
Solution: Check if test users already exist, run cleanup
Command: Check individual test output for specific username conflicts
```

### Debug Mode
Enable verbose output in individual tests by modifying the test files:
```python
# Add to test files for more detailed output
DEBUG = True  # Set to True for verbose logging
```

## Contributing to Tests

### Adding New Tests
1. Create new test file following naming convention: `test_[feature_name].py`
2. Include a `main()` function that returns `True` for success, `False` for failure
3. Add cleanup functionality for any test data created
4. Update `run_all_tests.py` to include the new test
5. Document the test in this README

### Test Structure Template
```python
#!/usr/bin/env python3
"""
Test description here
"""

import requests
import json

BACKEND_URL = "http://localhost:8000"

class FeatureTester:
    def __init__(self):
        self.test_data = []
    
    def cleanup(self):
        """Clean up test data"""
        pass
    
    def test_feature(self):
        """Test specific functionality"""
        # Test implementation
        return True
    
    def run_all_tests(self):
        """Run all tests for this feature"""
        try:
            success = self.test_feature()
            return success
        finally:
            self.cleanup()

def main():
    """Main test function"""
    tester = FeatureTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```
