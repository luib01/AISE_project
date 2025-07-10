# backend/app/routes/performance.py
from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.db import get_db
from app.routes.auth import get_current_user
from app.models.learning_model import get_user_profile

router = APIRouter()

@router.get("/user-performance/")
async def get_user_performance(current_user: Dict = Depends(get_current_user)):
    """
    Return an array of all questions from all quizzes the user has taken,
    along with whether they were correct or not, for the bar chart.
    """
    user_id = current_user["user_id"]
    db = get_db()
    quizzes = db.Quizzes.find({"user_id": user_id}, {"_id": 0})

    performance_data = []
    index_counter = 1

    for quiz in quizzes:
        q_data = quiz.get("quiz_data", {}).get("questions", [])
        for q in q_data:
            is_correct = q.get("isCorrect", False)
            question_text = q.get("question", "")
            performance_data.append({
                "index": index_counter,
                "question": question_text,
                "isCorrect": is_correct
            })
            index_counter += 1

    return {"performance": performance_data}

@router.get("/user-performance-detailed/")
async def get_detailed_user_performance(current_user: Dict = Depends(get_current_user)):
    """
    Get detailed user performance including level progression and topic breakdown.
    """
    try:
        user_id = current_user["user_id"]
        user_profile = get_user_profile(user_id)
        
        # Get recent quiz history
        db = get_db()
        
        recent_quizzes = list(db.Quizzes.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(20))  # Increased to 20 for better analysis
        
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
