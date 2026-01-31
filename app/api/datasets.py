"""
Datasets API - Phase 3
=======================
File upload and dataset management

ENDPOINTS:
POST   /api/datasets/{project_id}/upload      Upload file
GET    /api/datasets/{project_id}             List datasets
GET    /api/datasets/details/{id}             Get details
GET    /api/datasets/{id}/profile             Get quality profile
DELETE /api/datasets/{id}                     Delete dataset
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging
import io
import json
from datetime import datetime

from app.core.database import get_db
from app.models.models import User, Workspace, Project, Dataset
from app.core.auth import verify_token, extract_token_from_header

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# HELPER: Get current user
# ============================================================================

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Extract and verify user from Authorization header"""
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
    """Verify user has access to project"""
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
# UPLOAD FILE
# ============================================================================

@router.post("/{project_id}/upload", status_code=201, summary="Upload dataset")
async def upload_dataset(
    project_id: str,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a dataset file
    
    Supports: CSV, JSON, Parquet, Excel, TSV
    Max size: 1GB
    """
    
    # Verify project access
    project = verify_project_access(project_id, current_user, db)
    
    logger.info(f"📤 Uploading file: {file.filename}")
    
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No file selected")
    
    # Get file extension
    file_ext = file.filename.split('.')[-1].lower()
    supported = ["csv", "json", "parquet", "xlsx", "xls", "tsv"]
    if file_ext not in supported:
        raise HTTPException(400, f"Unsupported format: .{file_ext}. Use: {', '.join(supported)}")
    
    # Read file content
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate size (1GB max)
        max_size = 1024 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(400, f"File too large. Max: 1GB")
        
        logger.info(f"✅ File read: {file_size / 1024:.1f}KB")
        
    except Exception as e:
        logger.error(f"❌ Error reading file: {str(e)}")
        raise HTTPException(400, f"Error reading file: {str(e)}")
    
    # Infer schema from file
    try:
        schema, row_count, quality_score = _infer_schema(file_content, file_ext)
        logger.info(f"✅ Schema inferred: {len(schema)} columns, {row_count} rows")
        
    except Exception as e:
        logger.warning(f"⚠️  Schema inference failed: {str(e)}")
        schema = []
        row_count = 0
        quality_score = 0
    
    # Create dataset record
    dataset = Dataset(
        project_id=project_id,
        name=name,
        description=description,
        source_type="upload",
        file_name=file.filename,
        file_format=file_ext,
        file_size_bytes=file_size,
        file_content=file_content,  # ← Store file as blob
        row_count=row_count,
        column_count=len(schema),
        columns_info=schema,
        schema_inferred=len(schema) > 0,
        schema_confidence=95.0 if schema else 0,
        quality_score=quality_score,
        tags=json.loads(tags) if tags else [],
        status="ready"
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    logger.info(f"✅ Dataset created: {dataset.id}")
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "file_name": dataset.file_name,
        "file_size_mb": file_size / 1024 / 1024,
        "row_count": row_count,
        "column_count": len(schema),
        "quality_score": quality_score,
        "schema": schema,
        "status": "ready",
        "created_at": dataset.created_at.isoformat()
    }


# ============================================================================
# LIST DATASETS
# ============================================================================

@router.get("/{project_id}", summary="List datasets")
def list_datasets(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all datasets for a project"""
    
    # Verify access
    project = verify_project_access(project_id, current_user, db)
    
    logger.info(f"📋 Listing datasets for project: {project_id}")
    
    datasets = db.query(Dataset).filter(
        Dataset.project_id == project_id,
        Dataset.status != "archived"
    ).all()
    
    return [
        {
            "id": ds.id,
            "name": ds.name,
            "file_name": ds.file_name,
            "file_format": ds.file_format,
            "row_count": ds.row_count,
            "column_count": ds.column_count,
            "quality_score": ds.quality_score,
            "version": ds.version,
            "status": ds.status,
            "created_at": ds.created_at.isoformat()
        }
        for ds in datasets
    ]


# ============================================================================
# GET DATASET DETAILS
# ============================================================================

@router.get("/details/{dataset_id}", summary="Get dataset details")
def get_dataset_details(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dataset details (schema, quality, etc)"""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    # Verify access
    project = verify_project_access(dataset.project_id, current_user, db)
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "file_name": dataset.file_name,
        "file_format": dataset.file_format,
        "file_size_mb": dataset.file_size_bytes / 1024 / 1024 if dataset.file_size_bytes else 0,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "schema": dataset.columns_info,
        "quality_score": dataset.quality_score,
        "missing_values_count": dataset.missing_values_count,
        "missing_values_pct": dataset.missing_values_pct,
        "duplicates_count": dataset.duplicate_rows_count,
        "tags": dataset.tags,
        "status": dataset.status,
        "version": dataset.version,
        "created_at": dataset.created_at.isoformat()
    }


# ============================================================================
# GET DATA PROFILE / QUALITY REPORT
# ============================================================================

@router.get("/{dataset_id}/profile", summary="Get data quality profile")
def get_dataset_profile(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data quality report"""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    # Verify access
    project = verify_project_access(dataset.project_id, current_user, db)
    
    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "quality_metrics": {
            "overall_score": dataset.quality_score,
            "completeness": 100 - (dataset.missing_values_pct or 0),
            "missing_values_count": dataset.missing_values_count,
            "missing_values_pct": dataset.missing_values_pct,
            "duplicates_count": dataset.duplicate_rows_count
        },
        "schema": dataset.columns_info,
        "last_updated": dataset.updated_at.isoformat()
    }


# ============================================================================
# DELETE DATASET
# ============================================================================

@router.delete("/{dataset_id}", status_code=204, summary="Delete dataset")
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete dataset (soft delete)"""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    # Verify access
    project = verify_project_access(dataset.project_id, current_user, db)
    
    logger.info(f"🗑️  Deleting: {dataset_id}")
    
    dataset.status = "archived"
    dataset.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"✅ Archived: {dataset_id}")


# ============================================================================
# SCHEMA INFERENCE
# ============================================================================

def _infer_schema(file_content: bytes, file_format: str) -> tuple:
    """
    Infer schema from file
    
    Returns: (schema, row_count, quality_score)
    """
    
    try:
        import pandas as pd
        
        # Read file based on format
        if file_format == "csv":
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_format == "tsv":
            df = pd.read_csv(io.BytesIO(file_content), sep="\t")
        elif file_format == "json":
            df = pd.read_json(io.BytesIO(file_content))
        elif file_format in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(file_content))
        elif file_format == "parquet":
            df = pd.read_parquet(io.BytesIO(file_content))
        else:
            raise ValueError(f"Unsupported format: {file_format}")
        
        # Build schema
        schema = []
        for col in df.columns:
            col_type = str(df[col].dtype)
            
            # Convert numpy types to simple types
            if "int" in col_type:
                simple_type = "integer"
            elif "float" in col_type:
                simple_type = "float"
            elif "object" in col_type:
                simple_type = "string"
            elif "datetime" in col_type or "date" in col_type:
                simple_type = "datetime"
            elif "bool" in col_type:
                simple_type = "boolean"
            else:
                simple_type = "string"
            
            schema.append({
                "name": col,
                "type": simple_type,
                "nullable": bool(df[col].isnull().any()),
                "description": ""
            })
        
        # Calculate quality
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        quality_score = 100 * (1 - missing_cells / max(total_cells, 1))
        
        return schema, df.shape[0], quality_score
        
    except Exception as e:
        logger.error(f"Schema inference error: {str(e)}")
        raise

