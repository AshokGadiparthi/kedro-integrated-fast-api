"""
Placeholder Routes - Phase 3 Features
======================================

These endpoints are called by the frontend but will be fully implemented in Phase 3.
For now, they return mock data to prevent 404 errors.

Endpoints:
- GET /models/recent         Get recent models
- GET /activities/recent     Get recent activities
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.models.models import User
from app.core.auth import verify_token, extract_token_from_header

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# ============================================================================
# HELPER FUNCTION - Get current user from token
# ============================================================================

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Extract and verify user from Authorization header"""
    token = extract_token_from_header(authorization)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ============================================================================
# GET RECENT MODELS (Placeholder - Phase 3)
# ============================================================================

@router.get(
    "/models/recent",
    summary="Get recent models",
    description="Get recently created or trained models (Phase 3)"
)
def get_recent_models(
    project_id: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent models (Phase 3 - Placeholder)
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Query Parameters:**
    - project_id: (Optional) Filter by project
    - limit: Number of models to return (default: 5)
    
    **Response (200 OK):**
    ```json
    {
      "models": [],
      "total": 0,
      "message": "Models feature coming in Phase 3"
    }
    ```
    """
    
    logger.info(f"📊 Getting recent models for user: {current_user.email}")
    
    # Placeholder response
    return {
        "models": [],
        "total": 0,
        "message": "Models feature coming in Phase 3: Model Training & Evaluation"
    }


# ============================================================================
# GET RECENT ACTIVITIES (Placeholder - Phase 3)
# ============================================================================

@router.get(
    "/activities/recent",
    summary="Get recent activities",
    description="Get recent activities in user's workspace (Phase 3)"
)
def get_recent_activities(
    project_id: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent activities (Phase 3 - Placeholder)
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Query Parameters:**
    - project_id: (Optional) Filter by project
    - limit: Number of activities to return (default: 5)
    
    **Response (200 OK):**
    ```json
    {
      "activities": [],
      "total": 0,
      "message": "Activities feature coming in Phase 3"
    }
    ```
    """
    
    logger.info(f"📋 Getting recent activities for user: {current_user.email}")
    
    # Placeholder response
    return {
        "activities": [],
        "total": 0,
        "message": "Activities feature coming in Phase 3: Monitoring & Optimization"
    }
