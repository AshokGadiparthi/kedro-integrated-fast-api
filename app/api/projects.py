"""
Projects Routes - With Workspaces
==================================
Project CRUD operations

ENDPOINTS:
- GET    /api/workspaces/{workspace_id}/projects          List projects
- POST   /api/workspaces/{workspace_id}/projects          Create project
- GET    /api/projects/{project_id}                       Get project details
- PUT    /api/projects/{project_id}                       Update project
- DELETE /api/projects/{project_id}                       Delete project
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid

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

router = APIRouter()

# ============================================================================
# HELPER - Get current user
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
# LIST PROJECTS IN WORKSPACE
# ============================================================================

@router.get("/workspaces/{workspace_id}/projects", response_model=List[ProjectResponse])
def list_projects_in_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects in a workspace"""
    logger.info(f"📋 Listing projects in workspace: {workspace_id}")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    projects = db.query(Project).filter(
        Project.workspace_id == workspace_id,
        Project.is_active == True
    ).all()
    
    logger.info(f"✅ Found {len(projects)} projects")
    return projects


# ============================================================================
# CREATE PROJECT IN WORKSPACE
# ============================================================================

@router.post("/workspaces/{workspace_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_in_workspace(
    workspace_id: str,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project in a workspace"""
    logger.info(f"➕ Creating project in workspace: {workspace_id}")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    new_project = Project(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        name=project_data.name,
        description=project_data.description or None,
        is_active=True
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    logger.info(f"✅ Project created: {new_project.id}")
    return new_project


# ============================================================================
# GET PROJECT DETAILS
# ============================================================================

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    logger.info(f"🔍 Getting project: {project_id}")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify user owns workspace
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    logger.info(f"✅ Project found: {project.name}")
    return project


# ============================================================================
# UPDATE PROJECT
# ============================================================================

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    logger.info(f"✏️ Updating project: {project_id}")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify authorization
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if project_data.name:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    
    db.commit()
    db.refresh(project)
    
    logger.info(f"✅ Project updated: {project.name}")
    return project


# ============================================================================
# DELETE PROJECT
# ============================================================================

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project"""
    logger.info(f"🗑️ Deleting project: {project_id}")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify authorization
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    db.delete(project)
    db.commit()
    
    logger.info(f"✅ Project deleted: {project_id}")
    return None
