"""
Datasets API - Phase 3
File upload and dataset management

ENDPOINTS:
POST   /api/datasets/{project_id}          Upload file
GET    /api/datasets/details/{id}          Get details (MUST BE BEFORE /{id})
GET    /api/datasets/{id}/preview          Get file preview (MUST BE BEFORE /{id})
GET    /api/datasets/{id}/quality          Get quality metrics (MUST BE BEFORE /{id})
GET    /api/datasets/{project_id}          List datasets (GENERIC - LAST)
DELETE /api/datasets/{id}                  Delete dataset
"""

from fastapi import APIRouter, Depends, HTTPException, Header, File, UploadFile, Query
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

@router.post("/{project_id}", status_code=201, summary="Upload dataset")
async def upload_dataset(
    project_id: str,
    file: UploadFile = File(...),
    name: str = Query(...),
    description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload dataset file with query parameters"""
    
    project = verify_project_access(project_id, current_user, db)
    logger.info(f"📤 Uploading: {file.filename}")
    
    if not file.filename:
        raise HTTPException(400, "No file selected")
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ["csv", "json", "parquet", "xlsx", "xls", "tsv"]:
        raise HTTPException(400, f"Unsupported format: .{file_ext}")
    
    try:
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 1024 * 1024 * 1024:
            raise HTTPException(400, "File too large (max 1GB)")
        logger.info(f"✅ File read: {file_size / 1024:.1f}KB")
    except Exception as e:
        raise HTTPException(400, f"Error reading file: {str(e)}")
    
    # Infer schema
    try:
        schema, row_count, quality_score = _infer_schema(file_content, file_ext)
    except:
        schema, row_count, quality_score = [], 0, 0
    
    # Create dataset
    dataset = Dataset(
        project_id=project_id,
        name=name,
        description=description,
        file_name=file.filename,
        file_format=file_ext,
        file_content=file_content,
        row_count=row_count,
        column_count=len(schema),
        columns_info=schema,
        schema_inferred=len(schema) > 0,
        schema_confidence=95.0 if schema else 0,
        quality_score=quality_score,
        status="ready"
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    logger.info(f"✅ Dataset created: {dataset.id}")
    return {
        "id": dataset.id,
        "name": name,
        "file_name": file.filename,
        "row_count": row_count,
        "column_count": len(schema),
        "quality_score": quality_score,
        "schema": schema,
        "status": "ready",
        "created_at": dataset.created_at.isoformat()
    }


# ============================================================================
# SPECIFIC ROUTES - MUST COME BEFORE GENERIC /{project_id}
# ============================================================================

# GET DATASET DETAILS
@router.get("/details/{dataset_id}", summary="Get dataset details")
def get_dataset_details(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dataset details"""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    project = verify_project_access(dataset.project_id, current_user, db)
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "file_name": dataset.file_name,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "quality_score": dataset.quality_score,
        "schema": dataset.columns_info,
        "status": dataset.status,
        "created_at": dataset.created_at.isoformat()
    }


# GET DATASET PREVIEW
@router.get("/{dataset_id}/preview", summary="Get dataset preview")
def get_dataset_preview(
    dataset_id: str,
    rows: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get preview of dataset file (first N rows)"""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    project = verify_project_access(dataset.project_id, current_user, db)
    
    try:
        import pandas as pd
        
        if dataset.file_format == "csv":
            df = pd.read_csv(io.BytesIO(dataset.file_content), nrows=rows)
        elif dataset.file_format == "tsv":
            df = pd.read_csv(io.BytesIO(dataset.file_content), sep="\t", nrows=rows)
        elif dataset.file_format == "json":
            df = pd.read_json(io.BytesIO(dataset.file_content))
            df = df.head(rows)
        elif dataset.file_format in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(dataset.file_content), nrows=rows)
        elif dataset.file_format == "parquet":
            df = pd.read_parquet(io.BytesIO(dataset.file_content))
            df = df.head(rows)
        else:
            raise ValueError(f"Unsupported format: {dataset.file_format}")
        
        data = df.to_dict(orient='records')
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "rows": len(data),
            "columns": list(df.columns),
            "data": data,
            "total_rows": dataset.row_count,
            "total_columns": dataset.column_count
        }
    except Exception as e:
        logger.error(f"Error reading dataset: {str(e)}")
        raise HTTPException(500, f"Error reading file: {str(e)}")


# GET DATASET QUALITY
@router.get("/{dataset_id}/quality", summary="Get dataset quality metrics")
def get_dataset_quality(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data quality report"""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    
    project = verify_project_access(dataset.project_id, current_user, db)
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "file_name": dataset.file_name,
        "file_size": len(dataset.file_content) if dataset.file_content else 0,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "quality_score": dataset.quality_score,
        "missing_values_pct": dataset.missing_values_pct or 0,
        "duplicate_rows_pct": dataset.duplicate_rows_pct or 0,
        "schema": dataset.columns_info,
        "status": dataset.status,
        "updated_at": dataset.updated_at.isoformat()
    }


# ============================================================================
# GENERIC LIST DATASETS - MUST COME LAST (catches all /{project_id})
# ============================================================================

@router.get("/{project_id}", summary="List datasets")
def list_datasets(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all datasets for a project"""
    
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
            "file_size": len(ds.file_content) if ds.file_content else 0,
            "row_count": ds.row_count,
            "column_count": ds.column_count,
            "quality_score": ds.quality_score,
            "status": ds.status,
            "created_at": ds.created_at.isoformat()
        }
        for ds in datasets
    ]


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
    """Infer schema from file. Returns (schema, row_count, quality_score)"""
    
    try:
        import pandas as pd
        
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
        
        schema = []
        for col in df.columns:
            col_type = str(df[col].dtype)
            
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
                "nullable": bool(df[col].isnull().any())
            })
        
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        quality_score = 100 * (1 - missing_cells / max(total_cells, 1))
        
        return schema, df.shape[0], quality_score
        
    except Exception as e:
        logger.error(f"Schema inference error: {str(e)}")
        raise

