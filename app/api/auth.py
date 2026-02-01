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
    
    try:
        # Check if user already exists by username
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == user.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        new_user = User(
            id=str(uuid4()),
            username=user.username,
            email=user.email,
            password_hash=user.password,
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user - finds existing or creates if doesn't exist"""
    
    try:
        # Try to find user by username first
        db_user = db.query(User).filter(User.username == user.username).first()
        
        # If not found by username, try by email (in case they login with email)
        if not db_user and "@" in user.username:
            db_user = db.query(User).filter(User.email == user.username).first()
        
        # If user doesn't exist, create them (for demo purposes)
        if not db_user:
            # Use username as email if it looks like an email, otherwise create one
            email = user.username if "@" in user.username else f"{user.username}@example.com"
            
            # Check if email already exists (even if username doesn't match)
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                # Email already exists, just use that user
                db_user = existing_email
            else:
                # Create new user
                db_user = User(
                    id=str(uuid4()),
                    username=user.username,
                    password_hash=user.password,
                    email=email,
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
    except Exception as e:
        print(f"Login error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {str(e)}"
        )

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

