#!/usr/bin/env python3
"""
Test script to verify the quiz completion bug fix.
This script checks and updates existing users' has_completed_first_quiz status.
"""

import sys
import os
sys.path.append('/app')

from app.db import get_db
from datetime import datetime

def test_and_fix_quiz_completion_status():
    """Check and fix existing users' quiz completion status"""
    db = get_db()
    
    # Find all users
    users = list(db.users.find({}))
    print(f"Found {len(users)} users in database")
    
    for user in users:
        user_id = str(user["_id"])
        username = user.get("username", "Unknown")
        total_quizzes = user.get("total_quizzes", 0)
        has_completed_first = user.get("has_completed_first_quiz", False)
        
        print(f"\nUser: {username} (ID: {user_id})")
        print(f"  Total quizzes: {total_quizzes}")
        print(f"  Has completed first quiz: {has_completed_first}")
        
        # Check quiz history in Quizzes collection
        quiz_count = db.Quizzes.count_documents({"user_id": user_id})
        print(f"  Quiz history count: {quiz_count}")
        
        # Fix inconsistency: if user has quizzes but flag is False
        if quiz_count > 0 and not has_completed_first:
            print(f"  🔧 FIXING: User has {quiz_count} quizzes but has_completed_first_quiz is False")
            db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "has_completed_first_quiz": True,
                        "total_quizzes": quiz_count if total_quizzes != quiz_count else total_quizzes
                    }
                }
            )
            print(f"  ✅ Fixed: Set has_completed_first_quiz to True")
        elif quiz_count == 0 and has_completed_first:
            print(f"  🔧 FIXING: User has no quizzes but has_completed_first_quiz is True")
            db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "has_completed_first_quiz": False,
                        "total_quizzes": 0
                    }
                }
            )
            print(f"  ✅ Fixed: Set has_completed_first_quiz to False")
        else:
            print(f"  ✅ Status is consistent")

if __name__ == "__main__":
    try:
        test_and_fix_quiz_completion_status()
        print("\n🎉 Quiz completion status check and fix completed!")
    except Exception as e:
        print(f"❌ Error: {e}")
