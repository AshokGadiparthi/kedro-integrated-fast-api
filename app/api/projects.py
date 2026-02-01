"""
Projects Routes - Simplified (No Workspaces)
=============================================
Project CRUD operations - Direct under User

ENDPOINTS:
- GET    /api/projects                  List all user projects
- POST   /api/projects                  Create project
- GET    /api/projects/{id}             Get project
- PUT    /api/projects/{id}             Update project
- DELETE /api/projects/{id}             Delete project
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid

from app.core.database import get_db
from app.models.models import User, Project
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate
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
# LIST ALL USER PROJECTS
# ============================================================================

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects for current user"""
    logger.info(f"📋 Listing projects for user: {current_user.username}")
    
    projects = db.query(Project).filter(
        Project.owner_id == current_user.id,
        Project.is_active == True
    ).all()
    
    logger.info(f"✅ Found {len(projects)} projects")
    return projects


# ============================================================================
# CREATE PROJECT
# ============================================================================

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    logger.info(f"➕ Creating project: {project_data.name}")
    
    new_project = Project(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
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
# GET PROJECT
# ============================================================================

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    logger.info(f"🔍 Getting project: {project_id}")
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning(f"❌ Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
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
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning(f"❌ Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
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
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning(f"❌ Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    logger.info(f"✅ Project deleted: {project_id}")
    return None
