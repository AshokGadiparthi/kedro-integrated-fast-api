"""
Activities API - PHASE 3
=========================

Track all actions and events in the system.

Endpoints:
- POST   /api/activities/{project_id}             Log activity
- GET    /api/activities/{project_id}             List project activities
- GET    /api/activities/recent/{project_id}      Get recent activities
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.models import User, Workspace, Project, Activity
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
# LOG ACTIVITY
# ============================================================================

@router.post(
    "/{project_id}",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log activity",
    description="Log an activity/action in a project"
)
def log_activity(
    project_id: str,
    activity_data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log an activity
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Request Body:**
    ```json
    {
      "action": "model_trained",
      "target_type": "model",
      "target_id": "model-uuid",
      "description": "Model trained successfully with 92% accuracy"
    }
    ```
    
    **Response (201 Created):**
    ```json
    {
      "id": "activity-uuid",
      "project_id": "project-uuid",
      "action": "model_trained",
      "target_type": "model",
      "target_id": "model-uuid",
      "description": "Model trained successfully with 92% accuracy",
      "created_at": "2024-01-31T17:00:00"
    }
    ```
    """
    
    logger.info(f"📝 Logging activity in project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user has access
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Create activity
    db_activity = Activity(
        project_id=project_id,
        action=activity_data.action,
        target_type=activity_data.target_type,
        target_id=activity_data.target_id,
        description=activity_data.description
    )
    
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    logger.info(f"✅ Activity logged: {activity_data.action}")
    
    return db_activity


# ============================================================================
# LIST ALL ACTIVITIES
# ============================================================================

@router.get(
    "/{project_id}",
    response_model=List[ActivityResponse],
    summary="List activities",
    description="Get all activities in a project"
)
def list_activities(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all activities in project
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Response (200 OK):**
    ```json
    [
      {
        "id": "activity-uuid-1",
        "project_id": "project-uuid",
        "action": "model_trained",
        "target_type": "model",
        "target_id": "model-uuid",
        "description": "Model trained successfully",
        "created_at": "2024-01-31T17:00:00"
      }
    ]
    ```
    """
    
    logger.info(f"📋 Listing activities for project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get activities
    activities = db.query(Activity).filter(
        Activity.project_id == project_id
    ).order_by(Activity.created_at.desc()).all()
    
    logger.info(f"✅ Found {len(activities)} activities")
    
    return activities


# ============================================================================
# GET RECENT ACTIVITIES
# ============================================================================

@router.get(
    "/recent/{project_id}",
    response_model=List[ActivityResponse],
    summary="Get recent activities",
    description="Get latest activities in a project"
)
def get_recent_activities(
    project_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent activities (latest first)
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Query Parameters:**
    - limit: Number of activities to return (default: 10)
    
    **Response (200 OK):**
    ```json
    [
      {
        "id": "activity-uuid-1",
        "project_id": "project-uuid",
        "action": "model_trained",
        "target_type": "model",
        "target_id": "model-uuid",
        "description": "Model trained successfully",
        "created_at": "2024-01-31T17:00:00"
      }
    ]
    ```
    """
    
    logger.info(f"⏱️  Getting recent activities for project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get recent activities
    activities = db.query(Activity).filter(
        Activity.project_id == project_id
    ).order_by(Activity.created_at.desc()).limit(limit).all()
    
    logger.info(f"✅ Found {len(activities)} recent activities")
    
    return activities
