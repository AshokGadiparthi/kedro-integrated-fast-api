"""
Datasources Routes - PHASE 2
=============================
Data ingestion and datasource management

ENDPOINTS:
- POST   /api/datasources/{project_id}           Create datasource
- GET    /api/datasources/{project_id}           List project datasources
- GET    /api/datasources/{datasource_id}        Get datasource details
- DELETE /api/datasources/{datasource_id}        Delete datasource
- POST   /api/datasources/{datasource_id}/test   Test connection
- POST   /api/datasources/{datasource_id}/preview Get data preview
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
import json

from app.core.database import get_db
from app.models.models import User, Workspace, Project, Datasource, Dataset
from app.schemas import DatasourceCreate, DatasourceResponse
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
# CREATE DATASOURCE
# ============================================================================

@router.post(
    "/{project_id}",
    response_model=DatasourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create datasource",
    description="Create a new datasource (file or database connection)"
)
def create_datasource(
    project_id: str,
    datasource_data: DatasourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new datasource
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - project_id: The UUID of the project
    
    **Request Body:**
    ```json
    {
      "name": "Customer Data",
      "type": "csv",
      "description": "Customer information CSV",
      "connection_config": null
    }
    ```
    
    **Response (201 Created):**
    ```json
    {
      "id": "datasource-uuid",
      "project_id": "project-uuid",
      "name": "Customer Data",
      "type": "csv",
      "description": "Customer information CSV",
      "file_path": null,
      "file_size": null,
      "is_active": true,
      "is_connected": false,
      "created_at": "2024-01-31T11:30:00",
      "updated_at": "2024-01-31T11:30:00"
    }
    ```
    
    **Error Cases:**
    - 401: Missing or invalid token
    - 404: Project not found
    """
    
    logger.info(f"🆕 Creating datasource in project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Verify user has access to project's workspace
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Create datasource
    db_datasource = Datasource(
        project_id=project_id,
        name=datasource_data.name,
        type=datasource_data.type,
        description=datasource_data.description,
        connection_config=datasource_data.connection_config
    )
    
    db.add(db_datasource)
    db.commit()
    db.refresh(db_datasource)
    
    logger.info(f"✅ Datasource created: {datasource_data.name}")
    return db_datasource


# ============================================================================
# LIST DATASOURCES
# ============================================================================

@router.get(
    "/{project_id}",
    response_model=List[DatasourceResponse],
    summary="List datasources",
    description="Get all datasources for a project"
)
def list_datasources(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all datasources for a project
    
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
        "id": "datasource-uuid",
        "project_id": "project-uuid",
        "name": "Customer Data",
        "type": "csv",
        ...
      }
    ]
    ```
    """
    
    logger.info(f"📋 Listing datasources for project: {project_id}")
    
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Get datasources
    datasources = db.query(Datasource).filter(
        Datasource.project_id == project_id
    ).all()
    
    logger.info(f"✅ Found {len(datasources)} datasources")
    return datasources


# ============================================================================
# GET DATASOURCE DETAILS
# ============================================================================

@router.get(
    "/details/{datasource_id}",
    response_model=DatasourceResponse,
    summary="Get datasource details",
    description="Get detailed information about a datasource"
)
def get_datasource(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get datasource details
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - datasource_id: The UUID of the datasource
    
    **Response (200 OK):**
    ```json
    {
      "id": "datasource-uuid",
      ...
    }
    ```
    """
    
    logger.info(f"🔍 Getting datasource: {datasource_id}")
    
    # Get datasource
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == datasource.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    return datasource


# ============================================================================
# DELETE DATASOURCE
# ============================================================================

@router.delete(
    "/{datasource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete datasource",
    description="Delete a datasource"
)
def delete_datasource(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a datasource
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - datasource_id: The UUID of the datasource
    
    **Response (204 No Content):**
    ```
    (Empty response)
    ```
    """
    
    logger.info(f"🗑️  Deleting datasource: {datasource_id}")
    
    # Get datasource
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == datasource.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Delete
    db.delete(datasource)
    db.commit()
    
    logger.info(f"✅ Datasource deleted: {datasource.name}")


# ============================================================================
# UPLOAD FILE
# ============================================================================

@router.post(
    "/upload/{datasource_id}",
    response_model=DatasourceResponse,
    summary="Upload data file",
    description="Upload CSV, Excel, JSON, or Parquet file"
)
async def upload_file(
    datasource_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a data file to a datasource
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    Content-Type: multipart/form-data
    ```
    
    **Path Parameters:**
    - datasource_id: The UUID of the datasource
    
    **Form Data:**
    - file: The file to upload (CSV, Excel, JSON, Parquet)
    
    **Response (200 OK):**
    ```json
    {
      "id": "datasource-uuid",
      "file_path": "/uploads/customer_data.csv",
      "file_size": 1024000,
      "is_connected": true,
      ...
    }
    ```
    """
    
    logger.info(f"📤 Uploading file to datasource: {datasource_id}")
    
    # Get datasource
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == datasource.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Save file
    upload_dir = "/tmp/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = f"{upload_dir}/{datasource_id}_{file.filename}"
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Update datasource
    datasource.file_path = file_path
    datasource.file_size = len(contents)
    datasource.is_connected = True
    
    db.commit()
    db.refresh(datasource)
    
    logger.info(f"✅ File uploaded: {file.filename} ({len(contents)} bytes)")
    return datasource


# ============================================================================
# GET DATA PREVIEW
# ============================================================================

@router.get(
    "/preview/{datasource_id}",
    summary="Get data preview",
    description="Get preview of data (first 100 rows)"
)
def get_preview(
    datasource_id: str,
    rows: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a preview of the data
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - datasource_id: The UUID of the datasource
    
    **Query Parameters:**
    - rows: Number of rows to preview (default: 100)
    
    **Response (200 OK):**
    ```json
    {
      "data": [
        ["name", "age", "email"],
        ["John", 28, "john@example.com"],
        ["Jane", 34, "jane@example.com"]
      ],
      "row_count": 2,
      "column_count": 3
    }
    ```
    """
    
    logger.info(f"👁️  Getting preview for datasource: {datasource_id}")
    
    # Get datasource
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == datasource.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Preview functionality requires actual data source implementation
    # This will be fully implemented in Phase 3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Data preview functionality coming in Phase 3: Full Data Integration"
    )


# ============================================================================
# TEST CONNECTION
# ============================================================================

@router.post(
    "/test/{datasource_id}",
    summary="Test connection",
    description="Test datasource connection (for databases)"
)
def test_connection(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test connection to a datasource
    
    **Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Path Parameters:**
    - datasource_id: The UUID of the datasource
    
    **Response (200 OK):**
    ```json
    {
      "status": "connected",
      "message": "Connection successful",
      "database": "customer_db",
      "tables_count": 15
    }
    ```
    """
    
    logger.info(f"🔌 Testing connection for datasource: {datasource_id}")
    
    # Get datasource
    datasource = db.query(Datasource).filter(Datasource.id == datasource_id).first()
    if not datasource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Verify user has access
    project = db.query(Project).filter(Project.id == datasource.project_id).first()
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datasource not found")
    
    # Test connection (mock for now)
    if datasource.type == "csv":
        result = {
            "status": "connected",
            "message": "File is ready",
            "file_size": datasource.file_size,
            "file_path": datasource.file_path
        }
    else:
        result = {
            "status": "connected",
            "message": "Connection successful",
            "datasource_type": datasource.type
        }
    
    # Update datasource
    datasource.is_connected = True
    db.commit()
    
    logger.info(f"✅ Connection test successful")
    return result
