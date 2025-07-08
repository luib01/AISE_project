# backend/app/models/learning_model.py
from datetime import datetime
from app.db import get_db
from typing import Dict, List, Optional

db = get_db()

def get_user_profile(user_id: str) -> Dict:
    """Get user profile including English level and progress."""
    user_profile = db.Users.find_one({"user_id": user_id})
    if not user_profile:
        # Create default profile for new user
        default_profile = {
            "user_id": user_id,
            "english_level": "beginner",  # beginner, intermediate, advanced
            "progress": {},
            "created_at": datetime.utcnow(),
            "total_quizzes": 0,
            "average_score": 0.0,
            "last_quiz_date": None
        }
        db.Users.insert_one(default_profile)
        return default_profile
    return user_profile

def update_english_level(user_id: str, new_level: str) -> None:
    """Update user's English level."""
    db.Users.update_one(
        {"user_id": user_id},
        {"$set": {"english_level": new_level, "level_updated_at": datetime.utcnow()}},
        upsert=True
    )

# backend/app/models/learning_model.py
from datetime import datetime
from app.db import get_db
from app.config import config
from typing import Dict, List, Optional

db = get_db()

def calculate_adaptive_level(user_id: str, quiz_score: int, topic_performance: Dict) -> str:
    """
    Calculate the appropriate English level based on performance using config thresholds.
    Returns: 'beginner', 'intermediate', or 'advanced'
    """
    user_profile = get_user_profile(user_id)
    current_level = user_profile.get("english_level", "beginner")
    
    # Get recent performance data
    recent_quizzes = list(db.Quizzes.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(config.MIN_QUIZZES_FOR_LEVEL_CHANGE))
    
    if not recent_quizzes:
        return current_level
    
    # Calculate average score from recent quizzes
    avg_score = sum(quiz.get("score", 0) for quiz in recent_quizzes) / len(recent_quizzes)
    
    # Level progression logic usando le soglie dalla configurazione
    if current_level == "beginner":
        if avg_score >= config.LEVEL_UP_THRESHOLD and len(recent_quizzes) >= config.MIN_QUIZZES_FOR_LEVEL_CHANGE:
            return "intermediate"
    elif current_level == "intermediate":
        if avg_score >= config.LEVEL_UP_THRESHOLD + 5 and len(recent_quizzes) >= config.MIN_QUIZZES_FOR_LEVEL_CHANGE:  # Threshold più alto per advanced
            return "advanced"
        elif avg_score < config.LEVEL_DOWN_THRESHOLD:
            return "beginner"
    elif current_level == "advanced":
        if avg_score < config.LEVEL_DOWN_THRESHOLD + 10:  # Threshold più alto per non retrocedere troppo facilmente
            return "intermediate"
    
    return current_level

def save_recommendations(user_id: str, recommendations: list) -> None:
    """Save recommendations to 'Recommendations' collection."""
    db.Recommendations.insert_one({
        "user_id": user_id,
        "recommendations": recommendations,
        "timestamp": datetime.utcnow()
    })

def save_quiz_results(user_id: str, quiz_data: dict, score: int, topic: str, difficulty: str) -> None:
    """Save the user's quiz results with enhanced tracking."""
    
    # Calculate topic-specific performance
    questions = quiz_data.get("questions", [])
    topic_performance = {}
    
    for question in questions:
        q_topic = question.get("topic", "Unknown")
        if q_topic not in topic_performance:
            topic_performance[q_topic] = {"correct": 0, "total": 0}
        
        topic_performance[q_topic]["total"] += 1
        if question.get("isCorrect", False):
            topic_performance[q_topic]["correct"] += 1
    
    # Save detailed quiz results
    quiz_result = {
        "user_id": user_id,
        "quiz_data": quiz_data,
        "score": score,
        "topic": topic,
        "difficulty": difficulty,
        "topic_performance": topic_performance,
        "timestamp": datetime.utcnow()
    }
    db.Quizzes.insert_one(quiz_result)
    
    # Update user's overall stats
    user_profile = get_user_profile(user_id)
    total_quizzes = user_profile.get("total_quizzes", 0) + 1
    current_avg = user_profile.get("average_score", 0)
    new_avg = ((current_avg * (total_quizzes - 1)) + score) / total_quizzes
    
    # Calculate and update English level
    new_level = calculate_adaptive_level(user_id, score, topic_performance)
    current_level = user_profile.get("english_level", "beginner")
    
    update_data = {
        "total_quizzes": total_quizzes,
        "average_score": new_avg,
        "last_quiz_date": datetime.utcnow(),
        "english_level": new_level
    }
    
    # Add level change notification if level changed
    if new_level != current_level:
        update_data["level_changed"] = True
        update_data["previous_level"] = current_level
        update_data["level_change_date"] = datetime.utcnow()
    
    db.Users.update_one(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True
    )

def update_user_progress(user_id: str, topic: str, progress: int) -> None:
    """
    Update the user's progress in 'Users' collection.
    For a given topic, we store an integer score (0-100).
    """
    db.Users.update_one(
        {"user_id": user_id},
        {"$set": {f"progress.{topic}": progress}},
        upsert=True
    )
