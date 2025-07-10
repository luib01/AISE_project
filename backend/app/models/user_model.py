# backend/app/models/user_model.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
import re
from app.db import get_db
from bson import ObjectId

class UserModel:
    def __init__(self):
        self.db = get_db()
        self.users_collection = self.db["users"]
        self.sessions_collection = self.db["user_sessions"]
        
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, stored_password: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, password_hash = stored_password.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format (alphanumeric, 3-20 chars, no spaces)"""
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return re.match("^[a-zA-Z0-9_]+$", username) is not None
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength (min 8 chars, at least 1 letter and 1 number)"""
        if len(password) < 8:
            return False
        has_letter = re.search("[a-zA-Z]", password)
        has_number = re.search("[0-9]", password)
        return has_letter is not None and has_number is not None
    
    def create_user(self, username: str, password: str) -> Dict[str, Any]:
        """Create a new user account"""
        # Validate input
        if not self._validate_username(username):
            return {"success": False, "error": "Username must be 3-20 characters, alphanumeric and underscore only"}
        
        if not self._validate_password(password):
            return {"success": False, "error": "Password must be at least 8 characters with letters and numbers"}
        
        # Check if username already exists
        if self.users_collection.find_one({"username": username}):
            return {"success": False, "error": "Username already exists"}
        
        # Create user
        user_data = {
            "username": username,
            "password": self._hash_password(password),
            "created_at": datetime.utcnow(),
            "english_level": "beginner",
            "total_quizzes": 0,
            "quiz_history": [],
            "last_login": None,
            "has_completed_first_quiz": False  # Track if user has completed initial static quiz
        }
        
        result = self.users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "english_level": "beginner"
        }
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials"""
        user = self.users_collection.find_one({"username": username})
        
        if not user:
            return {"success": False, "error": "Invalid username or password"}
        
        if not self._verify_password(password, user["password"]):
            return {"success": False, "error": "Invalid username or password"}
        
        # Update last login
        self.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create session token
        session_token = secrets.token_urlsafe(32)
        session_data = {
            "user_id": str(user["_id"]),
            "username": username,
            "token": session_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)  # 7 days expiry
        }
        
        self.sessions_collection.insert_one(session_data)
        
        return {
            "success": True,
            "user_id": str(user["_id"]),
            "username": username,
            "english_level": user.get("english_level", "beginner"),
            "session_token": session_token
        }
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user info"""
        session = self.sessions_collection.find_one({
            "token": session_token,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not session:
            return None
        
        user = self.users_collection.find_one({"_id": ObjectId(session["user_id"])})
        if not user:
            return None
        
        return {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "english_level": user.get("english_level", "beginner"),
            "has_completed_first_quiz": user.get("has_completed_first_quiz", False),
            "level_changed": user.get("level_changed", False),
            "level_change_type": user.get("level_change_type", None),
            "level_change_message": user.get("level_change_message", None),
            "previous_level": user.get("previous_level", None)
        }
    
    def logout_user(self, session_token: str) -> bool:
        """Logout user by invalidating session"""
        result = self.sessions_collection.delete_one({"token": session_token})
        return result.deleted_count > 0
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return None
            
            return {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "english_level": user.get("english_level", "beginner"),
                "total_quizzes": user.get("total_quizzes", 0),
                "has_completed_first_quiz": user.get("has_completed_first_quiz", False),
                "level_changed": user.get("level_changed", False),
                "level_change_type": user.get("level_change_type", None),
                "level_change_message": user.get("level_change_message", None),
                "previous_level": user.get("previous_level", None),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
        except Exception:
            return None
    
    def update_username(self, user_id: str, new_username: str) -> Dict[str, Any]:
        """Update user's username"""
        if not self._validate_username(new_username):
            return {"success": False, "error": "Username must be 3-20 characters, alphanumeric and underscore only"}
        
        # Check if new username already exists
        existing_user = self.users_collection.find_one({"username": new_username})
        if existing_user and str(existing_user["_id"]) != user_id:
            return {"success": False, "error": "Username already exists"}
        
        try:
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"username": new_username}}
            )
            
            if result.modified_count > 0:
                return {"success": True, "message": "Username updated successfully"}
            else:
                return {"success": False, "error": "User not found"}
        except Exception as e:
            return {"success": False, "error": "Failed to update username"}
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user's password"""
        if not self._validate_password(new_password):
            return {"success": False, "error": "Password must be at least 8 characters with letters and numbers"}
        
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Verify current password
            if not self._verify_password(current_password, user["password"]):
                return {"success": False, "error": "Current password is incorrect"}
            
            # Update password
            new_password_hash = self._hash_password(new_password)
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": new_password_hash}}
            )
            
            if result.modified_count > 0:
                # Invalidate all sessions for this user (force re-login)
                self.sessions_collection.delete_many({"user_id": user_id})
                return {"success": True, "message": "Password changed successfully"}
            else:
                return {"success": False, "error": "Failed to change password"}
        except Exception as e:
            return {"success": False, "error": "Failed to change password"}
    
    def delete_account(self, user_id: str, password: str) -> Dict[str, Any]:
        """Delete user account"""
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Verify password before deletion
            if not self._verify_password(password, user["password"]):
                return {"success": False, "error": "Password is incorrect"}
            
            # Delete user and all sessions
            self.users_collection.delete_one({"_id": ObjectId(user_id)})
            self.sessions_collection.delete_many({"user_id": user_id})
            
            return {"success": True, "message": "Account deleted successfully"}
        except Exception as e:
            return {"success": False, "error": "Failed to delete account"}
