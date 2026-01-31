"""
Workspace Routes - PHASE 0
============================
Workspace CRUD operations

ENDPOINTS:
- GET    /api/workspaces           - List user's workspaces
- POST   /api/workspaces           - Create new workspace
- GET    /api/workspaces/{id}      - Get workspace details
- PUT    /api/workspaces/{id}      - Update workspace
- DELETE /api/workspaces/{id}      - Delete workspace
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.models import User, Workspace
from app.schemas import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
    WorkspaceListResponse
)
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
    """
    Extract and verify user from Authorization header
    
    Used as dependency in all protected routes
    """
    # Extract token
    token = extract_token_from_header(authorization)
    
    if not token:
        logger.warning("❌ Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    # Verify token
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ============================================================================
# LIST WORKSPACES
# ============================================================================

@router.get(
    "",
    response_model=List[WorkspaceResponse],
    summary="List user's workspaces",
    description="Get all workspaces owned by current user"
)
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all workspaces for the current user
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response (200 OK):**
    ```json
    [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "My ML Workspace",
        "slug": "my-ml-workspace",
        "description": "For development",
        "owner_id": "550e8400-e29b-41d4-a716-446655440001",
        "is_active": true,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
      }
    ]
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    """
    
    logger.info(f"📋 Listing workspaces for user: {current_user.email}")
    
    # Get all workspaces owned by current user
    workspaces = db.query(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Workspace.is_active == True
    ).all()
    
    logger.info(f"✅ Found {len(workspaces)} workspaces")
    
    return workspaces


# ============================================================================
# CREATE WORKSPACE
# ============================================================================

@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new workspace",
    description="Create a new workspace for the current user"
)
def create_workspace(
    workspace_data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new workspace
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Request Body:**
    ```json
    {
      "name": "My ML Workspace",
      "slug": "my-ml-workspace",
      "description": "For development and testing"
    }
    ```
    
    **Response (201 Created):**
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My ML Workspace",
      "slug": "my-ml-workspace",
      "description": "For development and testing",
      "owner_id": "550e8400-e29b-41d4-a716-446655440001",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 400: Slug already exists for this user
    - 422: Validation error
    """
    
    logger.info(f"🆕 Creating workspace: {workspace_data.name}")
    
    # Check if slug already exists for this user
    existing = db.query(Workspace).filter(
        Workspace.slug == workspace_data.slug,
        Workspace.owner_id == current_user.id
    ).first()
    
    if existing:
        logger.warning(f"❌ Slug already exists: {workspace_data.slug}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace with this slug already exists"
        )
    
    # Create workspace
    db_workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        slug=workspace_data.slug,
        owner_id=current_user.id
    )
    
    # Save to database
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    
    logger.info(f"✅ Workspace created: {workspace_data.name} (ID: {db_workspace.id})")
    
    return db_workspace


# ============================================================================
# GET WORKSPACE
# ============================================================================

@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace details",
    description="Get detailed information about a specific workspace"
)
def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workspace details
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - workspace_id: UUID of the workspace
    
    **Response (200 OK):**
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My ML Workspace",
      "slug": "my-ml-workspace",
      "description": "For development",
      "owner_id": "550e8400-e29b-41d4-a716-446655440001",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Workspace not found or doesn't belong to user
    """
    
    logger.info(f"🔍 Getting workspace: {workspace_id}")
    
    # Get workspace, ensure it belongs to current user
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        logger.warning(f"❌ Workspace not found: {workspace_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    logger.info(f"✅ Found workspace: {workspace.name}")
    
    return workspace


# ============================================================================
# UPDATE WORKSPACE
# ============================================================================

@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update workspace",
    description="Update workspace details"
)
def update_workspace(
    workspace_id: str,
    workspace_data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update workspace
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - workspace_id: UUID of the workspace
    
    **Request Body:**
    ```json
    {
      "name": "Updated Name",
      "description": "Updated description"
    }
    ```
    
    **Response (200 OK):**
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Updated Name",
      "slug": "my-ml-workspace",
      "description": "Updated description",
      "owner_id": "550e8400-e29b-41d4-a716-446655440001",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:35:00"
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Workspace not found
    - 422: Validation error
    """
    
    logger.info(f"✏️  Updating workspace: {workspace_id}")
    
    # Get workspace
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        logger.warning(f"❌ Workspace not found: {workspace_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Update fields
    if workspace_data.name:
        workspace.name = workspace_data.name
    if workspace_data.description is not None:
        workspace.description = workspace_data.description
    
    # Save changes
    db.commit()
    db.refresh(workspace)
    
    logger.info(f"✅ Workspace updated: {workspace.name}")
    
    return workspace


# ============================================================================
# DELETE WORKSPACE
# ============================================================================

@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workspace",
    description="Delete a workspace (soft delete - marked inactive)"
)
def delete_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete workspace
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - workspace_id: UUID of the workspace
    
    **Response:**
    - 204 No Content (successful deletion)
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Workspace not found
    """
    
    logger.info(f"🗑️  Deleting workspace: {workspace_id}")
    
    # Get workspace
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        logger.warning(f"❌ Workspace not found: {workspace_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Soft delete (mark as inactive)
    workspace.is_active = False
    db.commit()
    
    logger.info(f"✅ Workspace deleted: {workspace.name}")
