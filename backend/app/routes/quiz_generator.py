# backend/app/routes/quiz_generator.py
import requests
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.config import config
from app.models.learning_model import get_user_profile, update_english_level

router = APIRouter()

class AdaptiveQuizRequest(BaseModel):
    user_id: str
    topic: str  # e.g., "Grammar", "Vocabulary", "Tenses", "Mixed"
    num_questions: int = 4
    force_difficulty: Optional[str] = None  # Optional override for difficulty

class GeneratedQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    topic: str
    difficulty: str

@router.post("/generate-adaptive-quiz/")
async def generate_adaptive_quiz(request: AdaptiveQuizRequest):
    """
    Generate an adaptive English quiz based on user's current level and performance.
    """
    try:
        # Get user profile to determine current English level
        user_profile = get_user_profile(request.user_id)
        current_level = user_profile.get("english_level", "beginner")
        
        # Use forced difficulty if provided, otherwise use user's level
        difficulty = request.force_difficulty or current_level
        
        # Get user's weak topics for targeted practice
        progress = user_profile.get("progress", {})
        weak_topics = [topic for topic, score in progress.items() if score < 70]
        
        # Craft adaptive prompt based on level and weak areas
        level_descriptions = {
            "beginner": "basic English concepts, simple grammar, common vocabulary",
            "intermediate": "more complex grammar structures, intermediate vocabulary, context-dependent questions",
            "advanced": "advanced grammar, nuanced vocabulary, complex sentence structures, idiomatic expressions"
        }
        
        focus_areas = ""
        if weak_topics:
            focus_areas = f"Focus especially on these areas where the student needs improvement: {', '.join(weak_topics[:3])}. "
        
        prompt = f"""
        You are an expert English teacher creating a personalized quiz for a {difficulty} level student.
        
        {focus_areas}
        
        Create {request.num_questions} multiple choice questions for the topic: {request.topic}
        
        Level: {difficulty} - {level_descriptions.get(difficulty, 'appropriate for their level')}
        
        Requirements:
        - Questions should be {difficulty} level appropriate
        - Include a mix of topics: grammar, vocabulary, reading comprehension, and usage
        - Each question should have exactly 4 options
        - Provide clear explanations for correct answers
        - Make questions engaging and practical
        
        Format your response as valid JSON only, with this exact structure:
        {{
            "questions": [
                {{
                    "question": "Question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Clear explanation of why this is correct",
                    "topic": "Grammar",
                    "difficulty": "{difficulty}"
                }}
            ]
        }}
        
        Topic guidelines:
        - Grammar: verb tenses, articles, prepositions, conditionals, passive voice
        - Vocabulary: synonyms, antonyms, word meanings, collocations
        - Reading: comprehension, inference, main ideas
        - Usage: practical English in context, common expressions
        
        Make sure all questions are at {difficulty} level and appropriate for English learners.
        """
        
        # Usa la configurazione centralizzata per Ollama
        ollama_config = config.get_ollama_config()
        api_url = f"{ollama_config['base_url']}/api/generate"
        
        payload = {
            "model": ollama_config['model'],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": ollama_config['options']['temperature'],
                "max_tokens": ollama_config['options']['max_tokens']
            }
        }
        
        response = requests.post(api_url, json=payload, timeout=ollama_config['timeout'])
        response.raise_for_status()
        data = response.json()
        
        generated_text = data.get("response", "")
        
        # Parse JSON response
        try:
            # Extract JSON from response
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in response")
            
            json_str = generated_text[start_idx:end_idx]
            quiz_data = json.loads(json_str)
            
            # Add metadata
            quiz_data["user_level"] = current_level
            quiz_data["generated_for_level"] = difficulty
            quiz_data["weak_topics"] = weak_topics
            quiz_data["user_id"] = request.user_id
            quiz_data["model_used"] = ollama_config['model']
            
            return quiz_data
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: create a simple quiz if JSON parsing fails
            return create_fallback_quiz(request.topic, difficulty, request.num_questions)
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {str(e)}")

@router.get("/model-info/")
async def get_model_info():
    """Get information about the current Ollama model and configuration."""
    ollama_config = config.get_ollama_config()
    return {
        "current_model": ollama_config['model'],
        "base_url": ollama_config['base_url'],
        "timeout": ollama_config['timeout'],
        "temperature": ollama_config['options']['temperature'],
        "max_tokens": ollama_config['options']['max_tokens'],
        "available_models": config.get_available_models()
    }

def create_fallback_quiz(topic: str, difficulty: str, num_questions: int) -> Dict:
    """Create a fallback quiz when AI generation fails."""
    
    fallback_questions = {
        "beginner": [
            {
                "question": "Which sentence is correct?",
                "options": ["I am student", "I am a student", "I am the student", "I student"],
                "correct_answer": "I am a student",
                "explanation": "We use 'a' before singular countable nouns when introducing them.",
                "topic": "Grammar",
                "difficulty": "beginner"
            },
            {
                "question": "What is the past tense of 'go'?",
                "options": ["goed", "went", "gone", "goes"],
                "correct_answer": "went",
                "explanation": "'Went' is the past tense of the irregular verb 'go'.",
                "topic": "Grammar",
                "difficulty": "beginner"
            }
        ],
        "intermediate": [
            {
                "question": "If I _____ you, I would study harder.",
                "options": ["am", "was", "were", "be"],
                "correct_answer": "were",
                "explanation": "In second conditional sentences, we use 'were' for all persons after 'if'.",
                "topic": "Grammar",
                "difficulty": "intermediate"
            }
        ],
        "advanced": [
            {
                "question": "The new policy has been _____ by the committee.",
                "options": ["ratified", "justified", "clarified", "nullified"],
                "correct_answer": "ratified",
                "explanation": "'Ratified' means officially approved or confirmed, which fits the context.",
                "topic": "Vocabulary",
                "difficulty": "advanced"
            }
        ]
    }
    
    questions = fallback_questions.get(difficulty, fallback_questions["beginner"])
    selected_questions = questions[:num_questions] if len(questions) >= num_questions else questions
    
    return {
        "questions": selected_questions,
        "generated_for_level": difficulty,
        "fallback": True
    }

@router.get("/user-profile/{user_id}")
async def get_user_english_profile(user_id: str):
    """Get user's English learning profile including level and progress."""
    try:
        profile = get_user_profile(user_id)
        return {
            "user_id": user_id,
            "english_level": profile.get("english_level", "beginner"),
            "progress": profile.get("progress", {}),
            "total_quizzes": profile.get("total_quizzes", 0),
            "average_score": profile.get("average_score", 0.0),
            "last_quiz_date": profile.get("last_quiz_date"),
            "level_changed": profile.get("level_changed", False),
            "previous_level": profile.get("previous_level")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user profile: {str(e)}")

@router.post("/update-user-level/")
async def manually_update_user_level(user_id: str, new_level: str):
    """Manually update user's English level (for admin use)."""
    if new_level not in ["beginner", "intermediate", "advanced"]:
        raise HTTPException(status_code=400, detail="Invalid level. Must be 'beginner', 'intermediate', or 'advanced'")
    
    try:
        update_english_level(user_id, new_level)
        return {"message": f"User {user_id} level updated to {new_level}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user level: {str(e)}")

@router.get("/quiz-topics/")
async def get_quiz_topics():
    """Get available English learning topics for quiz generation."""
    topics = [
        {
            "name": "Grammar",
            "subtopics": ["Verb Tenses", "Articles", "Prepositions", "Conditionals", "Passive Voice"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Vocabulary", 
            "subtopics": ["Synonyms", "Antonyms", "Idioms", "Phrasal Verbs", "Word Formation"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Reading",
            "subtopics": ["Main Ideas", "Details", "Inference", "Vocabulary in Context"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Usage",
            "subtopics": ["Common Expressions", "Collocations", "Formal vs Informal"],
            "levels": ["beginner", "intermediate", "advanced"]
        },
        {
            "name": "Mixed",
            "subtopics": ["All topics combined"],
            "levels": ["beginner", "intermediate", "advanced"]
        }
    ]
    
    return {"topics": topics}

@router.post("/change-model/")
async def change_model(new_model: str):
    """Change the Ollama model at runtime (for admin use)."""
    if not config.validate_model(new_model):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid model. Available models: {config.get_available_models()}"
        )
    
    try:
        # Test the new model with a simple prompt
        test_prompt = "Hello, can you respond with 'Model working correctly'?"
        
        api_url = f"{config.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": new_model,
            "prompt": test_prompt,
            "stream": False,
            "options": {"temperature": 0.1, "max_tokens": 20}
        }
        
        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()
        
        # If successful, update the config (this would be temporary until app restart)
        # In a production environment, you'd want to update the .env file
        config.OLLAMA_MODEL = new_model
        
        return {
            "message": f"Model changed to {new_model}",
            "new_model": new_model,
            "note": "This change is temporary until application restart"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to test new model: {str(e)}"
        )

@router.get("/health-check/")
async def health_check():
    """Check if Ollama is running and the current model is available."""
    try:
        ollama_config = config.get_ollama_config()
        api_url = f"{ollama_config['base_url']}/api/generate"
        
        payload = {
            "model": ollama_config['model'],
            "prompt": "Test",
            "stream": False,
            "options": {"temperature": 0.1, "max_tokens": 5}
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "status": "healthy",
            "model": ollama_config['model'],
            "base_url": ollama_config['base_url'],
            "message": "Ollama is running and model is available"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Ollama health check failed: {str(e)}"
        )
