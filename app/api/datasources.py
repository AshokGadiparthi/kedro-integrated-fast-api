"""
Datasources API - Phase 3
Manage data sources (MySQL, PostgreSQL, APIs, etc)
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.models import User, Workspace, Project, Datasource
from app.core.auth import verify_token, extract_token_from_header

logger = logging.getLogger(__name__)
router = APIRouter()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization")
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def verify_project_access(project_id: str, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == user.id
    ).first()
    if not workspace:
        raise HTTPException(status_code=403, detail="No access to project")
    return project

# ============================================================================
# CREATE DATASOURCE - FIXED PARAMETER HANDLING
# ============================================================================

@router.post("/{project_id}", status_code=201, summary="Create datasource")
def create_datasource(
    project_id: str,
    name: str = Body(...),
    type: str = Body(...),
    host: str = Body(...),
    port: int = Body(...),
    database_name: str = Body(...),
    username: str = Body(...),
    password: str = Body(...),
    description: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new datasource"""
    
    project = verify_project_access(project_id, current_user, db)
    
    # Validate type
    valid_types = ["mysql", "postgresql", "sqlite", "s3", "api", "mongodb"]
    if type.lower() not in valid_types:
        raise HTTPException(400, f"Invalid type. Use: {', '.join(valid_types)}")
    
    logger.info(f"📝 Creating datasource: {name} ({type})")
    
    # Create connection config
    connection_config = {
        "host": host,
        "port": port,
        "database": database_name,
        "username": username,
        "password": password
    }
    
    # Create datasource
    datasource = Datasource(
        project_id=project_id,
        name=name,
        type=type.lower(),
        host=host,
        port=port,
        database_name=database_name,
        username=username,
        password=password,
        description=description,
        status="untested",
        connection_config=connection_config
    )
    
    db.add(datasource)
    db.commit()
    db.refresh(datasource)
    
    logger.info(f"✅ Datasource created: {datasource.id}")
    return {
        "id": datasource.id,
        "name": datasource.name,
        "type": datasource.type,
        "host": datasource.host,
        "port": datasource.port,
        "database": datasource.database_name,
        "status": datasource.status,
        "created_at": datasource.created_at.isoformat()
    }

# ============================================================================
# LIST DATASOURCES
# ============================================================================

@router.get("/{project_id}", summary="List datasources")
def list_datasources(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all datasources for a project"""
    
    project = verify_project_access(project_id, current_user, db)
    logger.info(f"📋 Listing datasources for project: {project_id}")
    
    datasources = db.query(Datasource).filter(
        Datasource.project_id == project_id,
        Datasource.status != "deleted"
    ).all()
    
    return [
        {
            "id": ds.id,
            "name": ds.name,
            "type": ds.type,
            "host": ds.host,
            "port": ds.port,
            "database": ds.database_name,
            "status": ds.status,
            "created_at": ds.created_at.isoformat()
        }
        for ds in datasources
    ]

# ============================================================================
# GET DATASOURCE DETAILS
# ============================================================================

@router.get("/details/{datasource_id}", summary="Get datasource details")
def get_datasource_details(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get datasource details"""
    
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(404, "Datasource not found")
    
    project = verify_project_access(datasource.project_id, current_user, db)
    
    return {
        "id": datasource.id,
        "name": datasource.name,
        "type": datasource.type,
        "host": datasource.host,
        "port": datasource.port,
        "database": datasource.database_name,
        "username": datasource.username,
        "status": datasource.status,
        "created_at": datasource.created_at.isoformat(),
        "updated_at": datasource.updated_at.isoformat()
    }

# ============================================================================
# UPDATE DATASOURCE
# ============================================================================

@router.put("/{datasource_id}", summary="Update datasource")
def update_datasource(
    datasource_id: str,
    name: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    host: Optional[str] = Body(None),
    port: Optional[int] = Body(None),
    database_name: Optional[str] = Body(None),
    username: Optional[str] = Body(None),
    password: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update datasource"""
    
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(404, "Datasource not found")
    
    project = verify_project_access(datasource.project_id, current_user, db)
    
    if name:
        datasource.name = name
    if description is not None:
        datasource.description = description
    if host:
        datasource.host = host
    if port:
        datasource.port = port
    if database_name:
        datasource.database_name = database_name
    if username:
        datasource.username = username
    if password:
        datasource.password = password
    
    datasource.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(datasource)
    
    logger.info(f"✅ Updated datasource: {datasource_id}")
    return {
        "id": datasource.id,
        "name": datasource.name,
        "type": datasource.type,
        "status": datasource.status,
        "updated_at": datasource.updated_at.isoformat()
    }

# ============================================================================
# TEST CONNECTION
# ============================================================================

@router.post("/{datasource_id}/test", summary="Test datasource connection")
def test_datasource(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test datasource connection"""
    
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(404, "Datasource not found")
    
    project = verify_project_access(datasource.project_id, current_user, db)
    
    logger.info(f"🧪 Testing connection for: {datasource.name}")
    
    try:
        if datasource.type == "mysql":
            import mysql.connector
            conn = mysql.connector.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=datasource.password,
                database=datasource.database_name
            )
            conn.close()
            result = "Connection successful"
        elif datasource.type == "postgresql":
            import psycopg2
            conn = psycopg2.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=datasource.password,
                database=datasource.database_name
            )
            conn.close()
            result = "Connection successful"
        else:
            result = f"Testing not implemented for {datasource.type}"
        
        datasource.status = "tested"
        datasource.test_result = {"status": "success", "message": result}
        datasource.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Test passed: {datasource.name}")
        return {"status": "success", "message": result}
        
    except Exception as e:
        datasource.status = "tested"
        datasource.test_result = {"status": "failed", "message": str(e)}
        datasource.updated_at = datetime.utcnow()
        db.commit()
        
        logger.error(f"❌ Test failed: {str(e)}")
        return {"status": "failed", "message": str(e)}

# ============================================================================
# DELETE DATASOURCE
# ============================================================================

@router.delete("/{datasource_id}", status_code=204, summary="Delete datasource")
def delete_datasource(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete datasource (soft delete)"""
    
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(404, "Datasource not found")
    
    project = verify_project_access(datasource.project_id, current_user, db)
    
    logger.info(f"🗑️  Deleting: {datasource_id}")
    datasource.status = "deleted"
    datasource.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"✅ Archived: {datasource_id}")

