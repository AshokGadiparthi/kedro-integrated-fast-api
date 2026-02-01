"""
Authentication API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import UserRegister, UserLogin, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    """Register a new user"""
    return {
        "access_token": "mock-token",
        "token_type": "bearer",
        "user": {
            "id": "mock-id",
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": "2026-02-01"
        }
    }

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    """Login user"""
    return {
        "access_token": "mock-token",
        "token_type": "bearer",
        "user": {
            "id": "mock-id",
            "username": user.username,
            "email": None,
            "full_name": None,
            "created_at": "2026-02-01"
        }
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh():
    """Refresh token"""
    return {
        "access_token": "mock-token",
        "token_type": "bearer",
        "user": {
            "id": "mock-id",
            "username": "mock-user",
            "email": None,
            "full_name": None,
            "created_at": "2026-02-01"
        }
    }
