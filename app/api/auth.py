"""
Authentication Routes - PHASE 0
=================================
User registration and login endpoints

ENDPOINTS:
- POST /auth/register    - Register new user
- POST /auth/login       - Login and get token
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.core.database import get_db
from app.models.models import User
from app.schemas import (
    UserRegister, 
    UserLogin, 
    UserResponse, 
    TokenResponse
)
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    extract_token_from_header,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# ============================================================================
# REGISTER ENDPOINT
# ============================================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account"
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account
    
    **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "username": "john_doe",
      "password": "securepass123",
      "full_name": "John Doe"
    }
    ```
    
    **Response (201 Created):**
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "john_doe",
      "full_name": "John Doe",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00"
    }
    ```
    
    **Error Cases:**
    - 400: Email or username already exists
    - 422: Validation error (invalid email, weak password, etc)
    """
    
    logger.info(f"📝 Registration attempt: {user_data.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        logger.warning(f"❌ User already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create new user
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    
    # Save to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"✅ User registered: {user_data.email} (ID: {db_user.id})")
    
    return db_user


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and get token",
    description="Authenticate user and return JWT token"
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user and receive JWT access token
    
    **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "securepass123"
    }
    ```
    
    **Response (200 OK):**
    ```json
    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "bearer",
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "username": "john_doe",
        "full_name": "John Doe",
        "is_active": true,
        "created_at": "2024-01-15T10:30:00"
      }
    }
    ```
    
    **How to use the token:**
    Include in Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Error Cases:**
    - 401: Invalid email or password
    - 401: User account is inactive
    - 422: Validation error
    """
    
    logger.info(f"🔑 Login attempt: {user_data.email}")
    
    # Find user by email
    db_user = db.query(User).filter(User.email == user_data.email).first()
    
    if not db_user:
        logger.warning(f"❌ User not found: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, db_user.password_hash):
        logger.warning(f"❌ Wrong password for: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is active
    if not db_user.is_active:
        logger.warning(f"❌ Account inactive: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id},
        expires_delta=access_token_expires
    )
    
    logger.info(f"✅ User logged in: {user_data.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }


# ============================================================================
# GET CURRENT USER ENDPOINT (for debugging/testing)
# ============================================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description="Get information about the currently authenticated user"
)
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response (200 OK):**
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "john_doe",
      "full_name": "John Doe",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00"
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 401: Token expired
    - 404: User not found
    """
    
    # Extract token from header
    token = extract_token_from_header(authorization)
    
    if not token:
        logger.warning("❌ Missing or invalid authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    # Verify token and get user_id
    user_id = verify_token(token)
    
    if not user_id:
        logger.warning("❌ Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        logger.warning(f"❌ User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"✅ Fetched user info: {user.email}")
    
    return user
