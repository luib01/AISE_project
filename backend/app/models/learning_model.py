# backend/app/models/learning_model.py
from datetime import datetime
from app.db import get_db
from app.config import config
from typing import Dict, List, Optional
from bson import ObjectId

db = get_db()

def get_user_profile(user_id: str) -> Dict:
    """Get user profile including English level and progress."""
    try:
        # Get user from auth users collection
        user_profile = db.users.find_one({"_id": ObjectId(user_id)})
        if user_profile:
            # Convert ObjectId to string for JSON serialization
            user_profile["user_id"] = str(user_profile["_id"])
            user_profile.pop("_id", None)
            user_profile.pop("password", None)  # Don't return password
            
            # Ensure required fields exist
            if "progress" not in user_profile:
                user_profile["progress"] = {}
            if "total_quizzes" not in user_profile:
                user_profile["total_quizzes"] = 0
            if "average_score" not in user_profile:
                user_profile["average_score"] = 0.0
            if "has_completed_first_quiz" not in user_profile:
                user_profile["has_completed_first_quiz"] = False
            if "level_changed" not in user_profile:
                user_profile["level_changed"] = False
            if "level_change_type" not in user_profile:
                user_profile["level_change_type"] = None
            if "level_change_message" not in user_profile:
                user_profile["level_change_message"] = None
            
            # Get recent quiz history for adaptive learning
            recent_quizzes = list(db.Quizzes.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(10))  # Last 10 quizzes
            
            # Format quiz history for adaptive learning
            quiz_history = []
            for quiz in recent_quizzes:
                quiz_info = {
                    "topic": quiz.get("topic", "Unknown"),
                    "difficulty": quiz.get("difficulty", "beginner"),
                    "score": quiz.get("score", 0),
                    "timestamp": quiz.get("timestamp"),
                    "subtopics_covered": quiz.get("subtopics_covered", []),
                    "questions": [q.get("question", "") for q in quiz.get("questions", [])]
                }
                quiz_history.append(quiz_info)
            
            user_profile["quiz_history"] = quiz_history
            return user_profile
        else:
            # User not found, this shouldn't happen with auth
            raise ValueError(f"User {user_id} not found")
    except Exception as e:
        raise ValueError(f"Error getting user profile: {str(e)}")

def update_english_level(user_id: str, new_level: str) -> None:
    """Update user's English level."""
    try:
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "english_level": new_level,
                    "level_changed": True,
                    "level_change_date": datetime.utcnow()
                }
            }
        )
    except Exception as e:
        print(f"Error updating English level: {e}")

def update_user_progress(user_id: str, topic: str, progress: float) -> None:
    """Update user's progress for a specific topic."""
    try:
        # Update in the users collection
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    f"progress.{topic}": progress,
                    "last_updated": datetime.utcnow()
                }
            }
        )
    except Exception as e:
        print(f"Error updating user progress: {e}")

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
    
    # Level progression logic using config thresholds
    if current_level == "beginner":
        if avg_score >= config.LEVEL_UP_THRESHOLD and len(recent_quizzes) >= config.MIN_QUIZZES_FOR_LEVEL_CHANGE:
            return "intermediate"
    elif current_level == "intermediate":
        if avg_score >= config.LEVEL_UP_THRESHOLD + 5 and len(recent_quizzes) >= config.MIN_QUIZZES_FOR_LEVEL_CHANGE:  # Higher threshold for advanced
            return "advanced"
        elif avg_score < config.LEVEL_DOWN_THRESHOLD:
            return "beginner"
    elif current_level == "advanced":
        if avg_score < config.LEVEL_DOWN_THRESHOLD + 10:  # Higher threshold to not demote too easily
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
    
    # Mark first quiz as completed if this is the first quiz
    if total_quizzes == 1:
        update_data["has_completed_first_quiz"] = True
    
    # Add level change notification if level changed
    if new_level != current_level:
        update_data["level_changed"] = True
        update_data["previous_level"] = current_level
        update_data["level_change_date"] = datetime.utcnow()
        
        # Determine if it's progression or retrocession
        level_order = {"beginner": 1, "intermediate": 2, "advanced": 3}
        current_order = level_order.get(current_level, 1)
        new_order = level_order.get(new_level, 1)
        
        if new_order > current_order:
            update_data["level_change_type"] = "progression"
            update_data["level_change_message"] = f"Congratulations! You've progressed from {current_level} to {new_level} level!"
        else:
            update_data["level_change_type"] = "retrocession"
            update_data["level_change_message"] = f"Your level has changed from {current_level} to {new_level}. Keep practicing to improve!"
    
    # Update the users collection (auth users)
    update_result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
