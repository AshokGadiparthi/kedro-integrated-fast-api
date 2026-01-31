"""
Projects Routes - PHASE 1
===========================
Project CRUD operations

ENDPOINTS:
- GET    /api/workspaces/{workspace_id}/projects          List projects
- POST   /api/workspaces/{workspace_id}/projects          Create project
- GET    /api/projects/{project_id}                       Get project details
- PUT    /api/projects/{project_id}                       Update project
- DELETE /api/projects/{project_id}                       Delete project

Also provides:
- GET    /projects                                        List all user's projects
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.models import User, Workspace, Project
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectListResponse
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
# LIST ALL USER'S PROJECTS (across all workspaces)
# ============================================================================

@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="List all user's projects",
    description="Get all projects across all workspaces for current user"
)
def list_all_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects belonging to the current user (across all workspaces)
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response (200 OK):**
    ```json
    [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Customer Churn Prediction",
        "description": "Predict which customers will churn",
        "problem_type": "Classification",
        "status": "Active",
        "created_at": "2024-01-31T11:00:00",
        "updated_at": "2024-01-31T11:00:00"
      }
    ]
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    """
    
    logger.info(f"📋 Listing all projects for user: {current_user.email}")
    
    # Get all workspaces for this user
    workspaces = db.query(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Workspace.is_active == True
    ).all()
    
    # Get all projects from these workspaces
    workspace_ids = [ws.id for ws in workspaces]
    projects = db.query(Project).filter(
        Project.workspace_id.in_(workspace_ids)
    ).all()
    
    logger.info(f"✅ Found {len(projects)} projects")
    
    return projects


# ============================================================================
# LIST WORKSPACE'S PROJECTS
# ============================================================================

@router.get(
    "/workspaces/{workspace_id}",
    response_model=List[ProjectResponse],
    summary="List workspace's projects",
    description="Get all projects in a specific workspace"
)
def list_workspace_projects(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects in a specific workspace
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - workspace_id: The UUID of the workspace
    
    **Response (200 OK):**
    ```json
    [
      {
        "id": "project-uuid",
        "workspace_id": "workspace-uuid",
        "name": "Project Name",
        ...
      }
    ]
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Workspace not found or doesn't belong to user
    """
    
    logger.info(f"📋 Listing projects for workspace: {workspace_id}")
    
    # Verify workspace exists and belongs to user
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
    
    # Get projects in this workspace
    projects = db.query(Project).filter(
        Project.workspace_id == workspace_id
    ).all()
    
    logger.info(f"✅ Found {len(projects)} projects in workspace")
    
    return projects


# ============================================================================
# CREATE PROJECT
# ============================================================================

@router.post(
    "/workspaces/{workspace_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new project",
    description="Create a new project in a workspace"
)
def create_project(
    workspace_id: str,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project in a workspace
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - workspace_id: The UUID of the workspace
    
    **Request Body:**
    ```json
    {
      "name": "Customer Churn Prediction",
      "description": "Predict which customers will churn",
      "problem_type": "Classification"
    }
    ```
    
    **Response (201 Created):**
    ```json
    {
      "id": "project-uuid",
      "workspace_id": "workspace-uuid",
      "name": "Customer Churn Prediction",
      "description": "Predict which customers will churn",
      "problem_type": "Classification",
      "status": "Active",
      "created_at": "2024-01-31T11:10:00",
      "updated_at": "2024-01-31T11:10:00"
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Workspace not found
    - 422: Validation error
    """
    
    logger.info(f"🆕 Creating project in workspace: {workspace_id}")
    
    # Verify workspace exists and belongs to user
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
    
    # Create project
    db_project = Project(
        workspace_id=workspace_id,
        name=project_data.name,
        description=project_data.description,
        problem_type=project_data.problem_type,
        status="Active"
    )
    
    # Save to database
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    logger.info(f"✅ Project created: {project_data.name} (ID: {db_project.id})")
    
    return db_project


# ============================================================================
# GET PROJECT DETAILS
# ============================================================================

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    description="Get detailed information about a specific project"
)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project details
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Response (200 OK):**
    ```json
    {
      "id": "project-uuid",
      "workspace_id": "workspace-uuid",
      "name": "Customer Churn Prediction",
      ...
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Project not found or doesn't belong to user
    """
    
    logger.info(f"🔍 Getting project: {project_id}")
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        logger.warning(f"❌ Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user has access (check workspace owner)
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        logger.warning(f"❌ User doesn't have access to project: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    logger.info(f"✅ Found project: {project.name}")
    
    return project


# ============================================================================
# UPDATE PROJECT
# ============================================================================

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project details"
)
def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update project
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Request Body:**
    ```json
    {
      "name": "Updated Project Name",
      "description": "Updated description",
      "status": "Active"
    }
    ```
    
    **Response (200 OK):**
    ```json
    {
      "id": "project-uuid",
      "workspace_id": "workspace-uuid",
      "name": "Updated Project Name",
      ...
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Project not found
    """
    
    logger.info(f"✏️  Updating project: {project_id}")
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        logger.warning(f"❌ Project not found: {project_id}")
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
        logger.warning(f"❌ User doesn't have access to project: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update fields
    if project_data.name:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.status:
        project.status = project_data.status
    
    # Save changes
    db.commit()
    db.refresh(project)
    
    logger.info(f"✅ Project updated: {project.name}")
    
    return project


# ============================================================================
# DELETE PROJECT
# ============================================================================

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project"
)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete project
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Response:**
    - 204 No Content (successful deletion)
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Project not found
    """
    
    logger.info(f"🗑️  Deleting project: {project_id}")
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        logger.warning(f"❌ Project not found: {project_id}")
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
        logger.warning(f"❌ User doesn't have access to project: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete project
    db.delete(project)
    db.commit()
    
    logger.info(f"✅ Project deleted: {project.name}")


# ============================================================================
# GET PROJECT STATISTICS (PLACEHOLDER - PHASE 3)
# ============================================================================

@router.get(
    "/{project_id}/stats",
    summary="Get project statistics",
    description="Get statistics for a project"
)
def get_project_stats(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project statistics (Phase 3)
    
    Coming soon!
    """
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify access
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Return mock statistics (Phase 3 will implement properly)
    return {
        "project_id": project_id,
        "models_trained": 0,
        "total_accuracy": 0.0,
        "message": "Statistics coming in Phase 3"
    }
