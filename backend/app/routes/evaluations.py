# backend/app/routes/evaluations.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models.learning_model import save_quiz_results, update_user_progress, get_user_profile
from app.routes.auth import get_current_user

router = APIRouter()

class QuestionData(BaseModel):
    question: str
    topic: str
    userAnswer: str
    correctAnswer: str
    isCorrect: bool
    explanation: str = ""
    difficulty: str = "beginner"

class QuizSubmission(BaseModel):
    quiz_data: Dict[str, Any]
    score: int
    topic: str
    difficulty: str = "beginner"
    quiz_type: str = "adaptive"  # "adaptive" or "manual"

@router.post("/evaluate-quiz/")
async def evaluate_quiz(
    submission: QuizSubmission,
    current_user: Dict = Depends(get_current_user)
):
    """
    Save quiz results + update user progress and English level adaptively.
    """
    try:
        # Use authenticated user's ID
        user_id = current_user["user_id"]
        
        # Get user profile for context
        user_profile = get_user_profile(user_id)
        current_level = user_profile.get("english_level", "beginner")
        
        # 1) Save entire quiz results with enhanced information
        save_quiz_results(
            user_id=user_id,
            quiz_data=submission.quiz_data,
            score=submission.score,
            topic=submission.topic,
            difficulty=submission.difficulty
        )

        # 2) Update progress per topic based on performance
        questions = submission.quiz_data.get("questions", [])
        topic_scores = {}
        
        for q in questions:
            topic = q.get("topic", "Unknown")
            is_correct = q.get("isCorrect", False)
            
            if topic not in topic_scores:
                topic_scores[topic] = {"correct": 0, "total": 0}
            
            topic_scores[topic]["total"] += 1
            if is_correct:
                topic_scores[topic]["correct"] += 1
        
        # Update progress for each topic
        for topic, scores in topic_scores.items():
            progress_val = int((scores["correct"] / scores["total"]) * 100)
            update_user_progress(
                user_id=user_id,
                topic=topic,
                progress=progress_val
            )

        # 3) Get updated user profile to check for level changes
        updated_profile = get_user_profile(user_id)
        new_level = updated_profile.get("english_level", current_level)
        level_changed = new_level != current_level
        
        # 4) Prepare response with detailed feedback
        response_data = {
            "message": "Quiz evaluated and progress updated successfully",
            "score": submission.score,
            "current_level": new_level,
            "level_changed": level_changed,
            "topic_performance": topic_scores,
            "total_quizzes": updated_profile.get("total_quizzes", 0),
            "average_score": updated_profile.get("average_score", 0.0)
        }
        
        if level_changed:
            response_data["level_change_message"] = f"Congratulations! You've progressed from {current_level} to {new_level} level!"
            response_data["previous_level"] = current_level
        
        return response_data
        
    except Exception as e:
        return {"error": f"Error evaluating quiz: {str(e)}"}
