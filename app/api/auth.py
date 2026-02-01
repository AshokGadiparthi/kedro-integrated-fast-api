"""
Authentication API Routes
FIXED: Now creates real users in database and generates real JWT tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4
import jwt
from app.core.database import get_db
from app.models.models import User
from app.schemas import UserRegister, UserLogin, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# JWT config
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(user_id: str):
    """Create JWT token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register a new user - creates in database"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    new_user = User(
        id=str(uuid4()),
        username=user.username,
        email=user.email,
        password_hash=user.password,  # TODO: Hash this in production
        created_at=datetime.now()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    token = create_access_token(new_user.id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "created_at": new_user.created_at.isoformat()
        }
    }

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user - creates if doesn't exist"""
    
    # Try to find user
    db_user = db.query(User).filter(User.username == user.username).first()
    
    # If user doesn't exist, create them (for demo purposes)
    if not db_user:
        db_user = User(
            id=str(uuid4()),
            username=user.username,
            password_hash=user.password,  # TODO: Hash this in production
            email=user.username if "@" in user.username else f"{user.username}@example.com",
            created_at=datetime.now()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    
    # Generate token
    token = create_access_token(db_user.id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "created_at": db_user.created_at.isoformat()
        }
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh(db: Session = Depends(get_db)):
    """Refresh token"""
    # This should ideally accept the old token and validate it
    # For now, return a new mock token
    
    user_id = str(uuid4())
    token = create_access_token(user_id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "username": "user",
            "email": None,
            "created_at": datetime.now().isoformat()
        }
    }

