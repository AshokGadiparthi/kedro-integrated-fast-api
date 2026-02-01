"""
Models API - PHASE 3
====================

Train, manage, and track ML models in projects.

Endpoints:
- POST   /api/models/{project_id}              Create model
- GET    /api/models/{project_id}              List project models
- GET    /api/models/details/{model_id}        Get model details
- PUT    /api/models/{model_id}                Update model
- DELETE /api/models/{model_id}                Delete model
- POST   /api/models/{model_id}/complete       Mark as trained
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
import uuid

from app.core.database import get_db
from app.models.models import User, Project, Model, Activity
from app.schemas import ModelCreate, ModelResponse
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
# CREATE MODEL
# ============================================================================

@router.post(
    "/{project_id}",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create model",
    description="Create a new ML model for training"
)
def create_model(
    project_id: str,
    model_data: ModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new model
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Request Body:**
    ```json
    {
      "name": "Customer Churn v1",
      "algorithm": "Random Forest"
    }
    ```
    
    **Response (201 Created):**
    ```json
    {
      "id": "model-uuid",
      "project_id": "project-uuid",
      "name": "Customer Churn v1",
      "algorithm": "Random Forest",
      "accuracy": null,
      "status": "Training",
      "created_at": "2024-01-31T17:00:00",
      "updated_at": "2024-01-31T17:00:00"
    }
    ```
    """
    
    logger.info(f"🆕 Creating model in project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user owns project
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    # Create model
    db_model = Model(
        project_id=project_id,
        name=model_data.name,
        algorithm=model_data.algorithm,
        status="Training"
    )
    
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    # 📊 LOG ACTIVITY
    activity = Activity(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        project_id=project_id,
        action="created",
        entity_type="model",
        entity_id=db_model.id,
        details={"name": model_data.name, "algorithm": model_data.algorithm}
    )
    db.add(activity)
    db.commit()
    
    logger.info(f"✅ Model created: {model_data.name} (ID: {db_model.id})")
    
    return db_model


# ============================================================================
# LIST MODELS BY PROJECT
# ============================================================================

@router.get(
    "/{project_id}",
    response_model=List[ModelResponse],
    summary="List project models",
    description="Get all models in a project"
)
def list_project_models(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all models in project
    
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
        "id": "model-uuid-1",
        "project_id": "project-uuid",
        "name": "Customer Churn v1",
        "algorithm": "Random Forest",
        "accuracy": 0.92,
        "status": "Trained",
        "created_at": "2024-01-31T17:00:00"
      }
    ]
    ```
    """
    
    logger.info(f"📋 Listing models for project: {project_id}")
    
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
    
    # Get models
    models = db.query(Model).filter(Model.project_id == project_id).all()
    logger.info(f"✅ Found {len(models)} models")
    
    return models


# ============================================================================
# GET MODEL DETAILS
# ============================================================================

@router.get(
    "/details/{model_id}",
    response_model=ModelResponse,
    summary="Get model details",
    description="Get detailed information about a model"
)
def get_model_details(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get model details
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - model_id: The UUID of the model
    """
    
    logger.info(f"📊 Getting model details: {model_id}")
    
    # Get model
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == model.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    logger.info(f"✅ Model retrieved: {model.name}")
    return model


# ============================================================================
# UPDATE MODEL (Mark as trained with metrics)
# ============================================================================

@router.put(
    "/{model_id}",
    response_model=ModelResponse,
    summary="Update model",
    description="Update model with training results"
)
def update_model(
    model_id: str,
    updates: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update model with training results
    
    **Example - Mark as trained:**
    ```json
    {
      "status": "Trained",
      "accuracy": 0.92,
      "precision": 0.90,
      "recall": 0.94,
      "f1_score": 0.92,
      "training_duration_seconds": 3600
    }
    ```
    """
    
    logger.info(f"🔄 Updating model: {model_id}")
    
    # Get model
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == model.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Update model
    for key, value in updates.items():
        if hasattr(model, key):
            setattr(model, key, value)
    
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    
    logger.info(f"✅ Model updated: {model.name}")
    return model


# ============================================================================
# DELETE MODEL
# ============================================================================

@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete model",
    description="Delete a model"
)
def delete_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete model
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response (204 No Content):**
    ```
    (empty)
    ```
    """
    
    logger.info(f"🗑️  Deleting model: {model_id}")
    
    # Get model
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == model.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Delete model
    db.delete(model)
    db.commit()
    
    # Delete model
    db.delete(model)
    db.commit()
    



# ============================================================================
# FRONTEND COMPATIBILITY ALIASES
# ============================================================================

@router.get(
    "/recent",
    response_model=List[ModelResponse],
    summary="Get recent models (alias)",
    description="Get recently trained models - alias for /api/models/{project_id}"
)
def get_recent_models_alias(
    project_id: str = None,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Frontend compatibility route
    Supports: GET /api/models/recent?projectId=...
    
    Also supports: GET /api/models/{project_id}
    """
    
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="projectId is required"
        )
    
    logger.info(f"📋 Listing recent models for project: {project_id}")
    
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
    
    # Get recent models
    models = db.query(Model).filter(
        Model.project_id == project_id
    ).order_by(Model.created_at.desc()).limit(limit).all()
    
    logger.info(f"✅ Found {len(models)} recent models")
    
    return models
