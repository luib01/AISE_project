# backend/app/models/recommendation_engine.py
from app.db import get_db

db = get_db()

def recommend_resources_for_user(user_id: str) -> list:
    """
    Naive logic:
    1. Find user doc in Users collection.
    2. Identify topics with progress < 60 => 'weak topics'.
    3. Query 'Resources' for those topics.
    4. Return matched resources or fallback.
    """
    user_doc = db.Users.find_one({"user_id": user_id})
    if not user_doc:
        # Return a structured fallback resource
        return [{
            "title": "Getting Started with English Learning",
            "topic": "General",
            "url": "https://example.com/english-basics",
            "difficulty": "beginner",
            "description": "Basic English learning resources for new users",
            "reason": "New user - no progress data found"
        }]

    progress = user_doc.get("progress", {})
    # e.g. progress = { "Grammar": 40, "Vocabulary": 75 }

    weak_topics = [topic for topic, score in progress.items() if score < 60]
    if not weak_topics:
        # If no weak topics, return general advanced resources
        all_resources = list(db.Resources.find({}, {"_id": 0}))
        if all_resources:
            return all_resources
        else:
            # Return structured fallback
            return [{
                "title": "Advanced English Practice",
                "topic": "General",
                "url": "https://example.com/advanced-english",
                "difficulty": "advanced",
                "description": "Advanced practice materials for proficient learners",
                "reason": "No weak topics identified - general practice recommended"
            }]

    # Query resources for weak topics
    query = {"topic": {"$in": weak_topics}}
    matched_resources = list(db.Resources.find(query, {"_id": 0}))

    if matched_resources:
        return matched_resources
    else:
        # Return structured fallback for weak topics
        fallback_resources = []
        for topic in weak_topics[:3]:  # Limit to first 3 weak topics
            fallback_resources.append({
                "title": f"{topic} Practice Materials",
                "topic": topic,
                "url": f"https://example.com/{topic.lower()}-practice",
                "difficulty": "beginner",
                "description": f"Recommended practice materials for improving {topic} skills",
                "reason": f"Identified as weak topic (below 60% proficiency)"
            })
        
        return fallback_resources if fallback_resources else [{
            "title": "General English Practice",
            "topic": "General",
            "url": "https://example.com/general-practice",
            "difficulty": "intermediate",
            "description": "General English practice materials",
            "reason": "No specific resources found for weak topics"
        }]
