"""
Datasets API - Phase 3 FIXED
Proper metrics calculation with 0-1 scale and unique values
"""

from fastapi import APIRouter, Depends, HTTPException, Header, File, UploadFile, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging
import io
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.models import User, Project, Dataset, Activity
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
    if project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="No access to project")
    return project

@router.post("/{project_id}", status_code=201, summary="Upload dataset")
async def upload_dataset(
    project_id: str,
    file: UploadFile = File(...),
    name: str = Query(...),
    description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    
    # Initialize metrics
    schema = []
    row_count = 0
    column_count = 0
    quality_score = 0.0
    missing_values_pct = 0.0
    duplicate_rows_pct = 0.0
    
    try:
        import pandas as pd
        
        logger.info(f"📊 Parsing {file_ext} file...")
        
        if file_ext == "csv":
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_ext == "tsv":
            df = pd.read_csv(io.BytesIO(file_content), sep="\t")
        elif file_ext == "json":
            df = pd.read_json(io.BytesIO(file_content))
        elif file_ext in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(file_content))
        elif file_ext == "parquet":
            df = pd.read_parquet(io.BytesIO(file_content))
        else:
            raise ValueError(f"Unsupported format: {file_ext}")
        
        row_count = len(df)
        column_count = len(df.columns)
        logger.info(f"📈 Rows: {row_count}, Columns: {column_count}")
        
        # Calculate missing values percentage
        total_cells = row_count * column_count
        missing_cells = df.isnull().sum().sum()
        missing_values_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0.0
        
        # Calculate duplicate rows percentage
        duplicate_rows = df.duplicated().sum()
        duplicate_rows_pct = (duplicate_rows / row_count * 100) if row_count > 0 else 0.0
        
        # Calculate quality score (0.0 to 1.0 SCALE)
        completeness = (1 - missing_values_pct / 100)
        uniqueness = (1 - duplicate_rows_pct / 100)
        quality_score = (completeness + uniqueness) / 2
        
        logger.info(f"📊 Missing: {missing_values_pct:.1f}%, Duplicates: {duplicate_rows_pct:.1f}%, Quality: {quality_score:.2f}")
        
        # Build schema with unique values
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
            
            col_missing_pct = (df[col].isnull().sum() / row_count * 100) if row_count > 0 else 0.0
            unique_values = df[col].nunique()
            
            schema.append({
                "name": col,
                "type": simple_type,
                "nullable": bool(df[col].isnull().any()),
                "unique_values": int(unique_values),
                "missing_pct": round(col_missing_pct, 2)
            })
        
        logger.info(f"✅ Schema built: {len(schema)} columns")
        
    except Exception as e:
        logger.error(f"❌ Error processing file: {str(e)}")
        schema = []
        row_count = 0
        column_count = 0
        quality_score = 0.0
        missing_values_pct = 0.0
        duplicate_rows_pct = 0.0
    
    # Create dataset
    dataset = Dataset(
        project_id=project_id,
        name=name,
        description=description,
        file_name=file.filename,
        file_format=file_ext,
        file_content=file_content,
        row_count=row_count,
        column_count=column_count,
        columns_info=schema,
        schema_inferred=len(schema) > 0,
        schema_confidence=95.0 if schema else 0,
        quality_score=quality_score,
        missing_values_pct=missing_values_pct,
        duplicate_rows_pct=duplicate_rows_pct,
        status="ready"
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # 📊 LOG ACTIVITY
    activity = Activity(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        project_id=project_id,
        action="created",
        entity_type="dataset",
        entity_id=dataset.id,
        details={"file_name": file.filename, "row_count": row_count}
    )
    db.add(activity)
    db.commit()
    
    logger.info(f"✅ Dataset created: {dataset.id}")
    return {
        "id": dataset.id,
        "name": name,
        "file_name": file.filename,
        "file_size": file_size,
        "row_count": row_count,
        "column_count": column_count,
        "quality_score": quality_score,
        "missing_values_pct": missing_values_pct,
        "duplicate_rows_pct": duplicate_rows_pct,
        "schema": schema,
        "status": "ready",
        "created_at": dataset.created_at.isoformat()
    }

@router.get("/details/{dataset_id}", summary="Get dataset details")
def get_dataset_details(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

@router.get("/{dataset_id}/preview", summary="Get dataset preview")
def get_dataset_preview(
    dataset_id: str,
    rows: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

@router.get("/{dataset_id}/quality", summary="Get dataset quality metrics")
def get_dataset_quality(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

@router.get("/{project_id}", summary="List datasets")
def list_datasets(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
            "missing_values_pct": ds.missing_values_pct or 0,
            "duplicate_rows_pct": ds.duplicate_rows_pct or 0,
            "status": ds.status,
            "created_at": ds.created_at.isoformat()
        }
        for ds in datasets
    ]

@router.delete("/{dataset_id}", status_code=204, summary="Delete dataset")
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    project = verify_project_access(dataset.project_id, current_user, db)
    logger.info(f"🗑️  Deleting: {dataset_id}")
    dataset.status = "archived"
    dataset.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"✅ Archived: {dataset_id}")

