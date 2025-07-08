# backend/app/routes/evaluations.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models.learning_model import save_quiz_results, update_user_progress, get_user_profile

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
    user_id: str
    quiz_data: Dict[str, Any]
    score: int
    topic: str
    difficulty: str = "beginner"
    quiz_type: str = "adaptive"  # "adaptive" or "manual"

@router.post("/evaluate-quiz/")
async def evaluate_quiz(submission: QuizSubmission):
    """
    Save quiz results + update user progress and English level adaptively.
    """
    try:
        # Get user profile for context
        user_profile = get_user_profile(submission.user_id)
        current_level = user_profile.get("english_level", "beginner")
        
        # 1) Save entire quiz results with enhanced information
        save_quiz_results(
            user_id=submission.user_id,
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
                user_id=submission.user_id,
                topic=topic,
                progress=progress_val
            )

        # 3) Get updated user profile to check for level changes
        updated_profile = get_user_profile(submission.user_id)
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

@router.get("/user-performance-detailed/{user_id}")
async def get_detailed_user_performance(user_id: str):
    """
    Get detailed user performance including level progression and topic breakdown.
    """
    try:
        user_profile = get_user_profile(user_id)
        
        # Get recent quiz history
        from app.db import get_db
        db = get_db()
        
        recent_quizzes = list(db.Quizzes.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(10))
        
        # Calculate topic-wise performance
        topic_performance = {}
        for quiz in recent_quizzes:
            topic_perf = quiz.get("topic_performance", {})
            for topic, perf in topic_perf.items():
                if topic not in topic_performance:
                    topic_performance[topic] = {"correct": 0, "total": 0}
                topic_performance[topic]["correct"] += perf["correct"]
                topic_performance[topic]["total"] += perf["total"]
        
        # Convert to percentages
        topic_percentages = {}
        for topic, perf in topic_performance.items():
            if perf["total"] > 0:
                topic_percentages[topic] = {
                    "percentage": round((perf["correct"] / perf["total"]) * 100, 1),
                    "correct": perf["correct"],
                    "total": perf["total"]
                }
        
        return {
            "user_id": user_id,
            "english_level": user_profile.get("english_level", "beginner"),
            "total_quizzes": user_profile.get("total_quizzes", 0),
            "average_score": user_profile.get("average_score", 0.0),
            "topic_performance": topic_percentages,
            "recent_quizzes": [
                {
                    "score": quiz.get("score", 0),
                    "topic": quiz.get("topic", "Unknown"),
                    "difficulty": quiz.get("difficulty", "beginner"),
                    "timestamp": quiz.get("timestamp")
                }
                for quiz in recent_quizzes
            ],
            "level_progression": {
                "current_level": user_profile.get("english_level", "beginner"),
                "level_changed": user_profile.get("level_changed", False),
                "previous_level": user_profile.get("previous_level"),
                "level_change_date": user_profile.get("level_change_date")
            }
        }
        
    except Exception as e:
        return {"error": f"Error fetching detailed performance: {str(e)}"}
