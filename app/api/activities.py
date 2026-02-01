"""
Activities API - PHASE 3
=========================

Track all actions and events in the system.

Endpoints:
- POST   /api/activities/{project_id}             Log activity
- GET    /api/activities/{project_id}             List project activities
- GET    /api/activities/recent/{project_id}      Get recent activities
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models.models import User, Project, Activity
from app.schemas import ActivityCreate, ActivityResponse
from app.core.auth import extract_token_from_header, verify_token

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# HELPER FUNCTION - Get current user
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
# LIST ALL ACTIVITIES - WITH QUERY PARAMETER SUPPORT
# ============================================================================

@router.get(
    "",
    summary="List activities (all or by project)",
    description="Get all activities or activities for a specific project using query parameter"
)
def list_all_activities(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    limit: int = Query(100, description="Max number of activities to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List activities - supports both:
    - GET /api/activities                    - All user activities
    - GET /api/activities?project_id=UUID   - Activities for specific project
    """
    
    logger.info(f"📋 Listing activities for user: {current_user.username}")
    
    if project_id:
        # Verify project exists and belongs to user
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify user owns this project
        if project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        # Get project activities
        activities = db.query(Activity).filter(
            Activity.project_id == project_id
        ).order_by(Activity.created_at.desc()).limit(limit).all()
        
        logger.info(f"✅ Found {len(activities)} activities for project: {project_id}")
    else:
        # Get all user activities
        activities = db.query(Activity).filter(
            Activity.user_id == current_user.id
        ).order_by(Activity.created_at.desc()).limit(limit).all()
        
        logger.info(f"✅ Found {len(activities)} activities for user")
    
    # Return as JSON with proper formatting
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "project_id": a.project_id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "details": a.details,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in activities
    ]


# ============================================================================
# LOG ACTIVITY - REMOVED (Activities are now logged automatically in CRUD operations)
# ============================================================================


# ============================================================================
# LIST PROJECT ACTIVITIES - PATH PARAMETER (BACKWARD COMPATIBLE)
# ============================================================================

@router.get(
    "/project/{project_id}",
    summary="List project activities",
    description="Get all activities for a specific project"
)
def list_project_activities(
    project_id: str,
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all activities in a project - using path parameter"""
    
    logger.info(f"📋 Listing activities for project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user owns this project
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    # Get activities
    activities = db.query(Activity).filter(
        Activity.project_id == project_id
    ).order_by(Activity.created_at.desc()).limit(limit).all()
    
    logger.info(f"✅ Found {len(activities)} activities")
    
    # Return as JSON with isoformat dates
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "project_id": a.project_id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "details": a.details,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in activities
    ]


# ============================================================================
# GET RECENT PROJECT ACTIVITIES
# ============================================================================

@router.get(
    "/recent/{project_id}",
    summary="Get recent activities",
    description="Get latest activities in a project"
)
def get_recent_project_activities(
    project_id: str,
    limit: int = Query(10, description="Number of recent activities to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activities (latest first) for a project"""
    
    logger.info(f"⏱️  Getting recent activities for project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user owns this project
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    # Get recent activities
    activities = db.query(Activity).filter(
        Activity.project_id == project_id
    ).order_by(Activity.created_at.desc()).limit(limit).all()
    
    logger.info(f"✅ Found {len(activities)} recent activities")
    
    # Return as JSON with isoformat dates
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "project_id": a.project_id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "details": a.details,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in activities
    ]
