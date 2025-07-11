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
    user_profile = get_user_profile(user_id)
    db = get_db()
    quizzes = db.Quizzes.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", 1)

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

    return {
        "performance": performance_data,
        "total_quizzes": user_profile.get("total_quizzes", 0),
        "average_score": user_profile.get("average_score", 0.0),
        "english_level": user_profile.get("english_level", "beginner")
    }

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
        
        recent_quizzes_desc = list(db.Quizzes.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(20))  # Get latest 20 quizzes
        
        # Reverse list to get chronological order for line plot
        recent_quizzes = list(reversed(recent_quizzes_desc))
        
        # Calculate topic-wise performance
        topic_performance = {}
        topic_scores = {}  # Track scores by topic for average calculation
        
        for quiz in recent_quizzes:
            topic = quiz.get("topic", "Unknown")
            score = quiz.get("score", 0)
            
            # Track scores for average calculation
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(score)
            
            # Track correct/total questions
            topic_perf = quiz.get("topic_performance", {})
            for topic_name, perf in topic_perf.items():
                if topic_name not in topic_performance:
                    topic_performance[topic_name] = {"correct": 0, "total": 0}
                topic_performance[topic_name]["correct"] += perf["correct"]
                topic_performance[topic_name]["total"] += perf["total"]
        
        # Convert to percentages and include average scores
        topic_percentages = {}
        for topic, perf in topic_performance.items():
            if perf["total"] > 0:
                percentage = round((perf["correct"] / perf["total"]) * 100, 1)
                average_score = round(sum(topic_scores.get(topic, [0])) / len(topic_scores.get(topic, [1])), 1)
                
                topic_percentages[topic] = {
                    "percentage": percentage,
                    "correct": perf["correct"],
                    "total": perf["total"],
                    "average_score": average_score
                }
        
        total_quizzes = user_profile.get("total_quizzes", 0)
        first_quiz_num = (total_quizzes - len(recent_quizzes) + 1) if total_quizzes > 0 else 1
        
        # Debug logging
        print(f"DEBUG Performance: user_id={user_id}, total_quizzes={total_quizzes}, recent_count={len(recent_quizzes)}, first_quiz_num={first_quiz_num}")
        
        # Build recent quizzes response
        recent_quizzes_response = [
            {
                "quiz_number": first_quiz_num + i,
                "score": quiz.get("score", 0),
                "topic": quiz.get("topic", "Unknown"),
                "difficulty": quiz.get("difficulty", "beginner"),
                "timestamp": quiz.get("timestamp")
            }
            for i, quiz in enumerate(recent_quizzes)
        ]
        
        # Debug quiz numbers
        print(f"DEBUG Quiz numbers: {[q['quiz_number'] for q in recent_quizzes_response]}")

        return {
            "user_id": user_id,
            "english_level": user_profile.get("english_level", "beginner"),
            "total_quizzes": total_quizzes,
            "average_score": user_profile.get("average_score", 0.0),
            "topic_performance": topic_percentages,
            "recent_quizzes": recent_quizzes_response,
            "level_progression": {
                "current_level": user_profile.get("english_level", "beginner"),
                "level_changed": user_profile.get("level_changed", False),
                "previous_level": user_profile.get("previous_level"),
                "level_change_date": user_profile.get("level_change_date")
            }
        }
        
    except Exception as e:
        return {"error": f"Error fetching detailed performance: {str(e)}"}
