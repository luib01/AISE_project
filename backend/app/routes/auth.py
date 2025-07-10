# backend/app/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.models.user_model import UserModel

router = APIRouter()
user_model = UserModel()

# Request/Response Models
class SignUpRequest(BaseModel):
    username: str
    password: str

class SignInRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateUsernameRequest(BaseModel):
    new_username: str

class DeleteAccountRequest(BaseModel):
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# Helper function to get current user from session token
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    user = user_model.validate_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return user

@router.post("/signup", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """Register a new user account"""
    result = user_model.create_user(request.username, request.password)
    
    if result["success"]:
        return AuthResponse(
            success=True,
            message="Account created successfully",
            data={
                "user_id": result["user_id"],
                "username": result["username"],
                "english_level": result["english_level"]
            }
        )
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.post("/signin", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """Authenticate user and create session"""
    result = user_model.authenticate_user(request.username, request.password)
    
    if result["success"]:
        return AuthResponse(
            success=True,
            message="Signed in successfully",
            data={
                "user_id": result["user_id"],
                "username": result["username"],
                "english_level": result["english_level"],
                "session_token": result["session_token"]
            }
        )
    else:
        raise HTTPException(status_code=401, detail=result["error"])

@router.post("/logout", response_model=AuthResponse)
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user and invalidate session"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    success = user_model.logout_user(token)
    
    if success:
        return AuthResponse(success=True, message="Logged out successfully")
    else:
        return AuthResponse(success=False, error="Session not found")

@router.get("/profile", response_model=AuthResponse)
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile"""
    profile = user_model.get_user_profile(current_user["user_id"])
    
    if profile:
        return AuthResponse(
            success=True,
            data=profile
        )
    else:
        raise HTTPException(status_code=404, detail="User profile not found")

@router.put("/profile/username", response_model=AuthResponse)
async def update_username(
    request: UpdateUsernameRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user's username"""
    result = user_model.update_username(current_user["user_id"], request.new_username)
    
    if result["success"]:
        return AuthResponse(
            success=True,
            message=result["message"]
        )
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.put("/profile/password", response_model=AuthResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Change user's password"""
    result = user_model.change_password(
        current_user["user_id"],
        request.current_password,
        request.new_password
    )
    
    if result["success"]:
        return AuthResponse(
            success=True,
            message=result["message"]
        )
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.delete("/profile", response_model=AuthResponse)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete user account"""
    result = user_model.delete_account(current_user["user_id"], request.password)
    
    if result["success"]:
        return AuthResponse(
            success=True,
            message=result["message"]
        )
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.get("/validate", response_model=AuthResponse)
async def validate_session(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Validate current session and return user info"""
    return AuthResponse(
        success=True,
        data=current_user
    )
