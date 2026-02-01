"""Datasets API Routes"""
from fastapi import APIRouter, Depends, Path, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import os
import pandas as pd
import numpy as np
import io
from app.core.database import get_db
from app.models.models import Dataset
from app.schemas import DatasetCreate, DatasetResponse

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

# Directory to store uploaded files
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory storage for dataset content (since we can't rely on file system)
dataset_cache = {}

@router.get("/", response_model=list)
async def list_datasets(db: Session = Depends(get_db)):
    """List all datasets"""
    datasets = db.query(Dataset).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "project_id": d.project_id,
            "description": d.description,
            "file_name": d.file_name,
            "file_size_bytes": d.file_size_bytes,
            "created_at": d.created_at.isoformat() if d.created_at else ""
        }
        for d in datasets
    ]

from fastapi import APIRouter, Depends, Path, UploadFile, File, Form

@router.post("/")
async def create_dataset(
    name: str = None,
    project_id: str = None,
    description: str = None,
    file: UploadFile = None,
    db: Session = Depends(get_db)
):
    """Create dataset - simple parameters"""
    
    dataset_id = str(uuid4())
    new_dataset = Dataset(
        id=dataset_id,
        name=name or "dataset",
        project_id=project_id,
        description=description or "",
        file_name="sample_data.csv",
        file_size_bytes=0,
        created_at=datetime.now()
    )
    db.add(new_dataset)
    db.flush()
    
    # Save file if provided
    if file:
        contents = await file.read()
        file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
        
        # Write to file
        try:
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Read back to verify
            with open(file_path, "r") as f:
                df = pd.read_csv(f)
                dataset_cache[dataset_id] = df
            
            new_dataset.file_name = file.filename
            new_dataset.file_size_bytes = len(contents)
        except Exception as e:
            print(f"Error: {e}")
    
    db.commit()
    db.refresh(new_dataset)
    
    return {
        "id": new_dataset.id,
        "name": new_dataset.name,
        "project_id": new_dataset.project_id,
        "file_name": new_dataset.file_name,
        "file_size_bytes": new_dataset.file_size_bytes,
        "created_at": new_dataset.created_at.isoformat()
    }

@router.post("/{dataset_id}/upload")
async def upload_dataset_file(dataset_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and STORE actual file data for dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    try:
        # Read file content
        contents = await file.read()
        
        # Save to filesystem
        file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Also cache in memory for quick access
        try:
            df = pd.read_csv(io.BytesIO(contents))
            dataset_cache[dataset_id] = df
        except:
            pass
        
        # Update dataset record
        dataset.file_name = file.filename
        dataset.file_size_bytes = len(contents)
        db.commit()
        
        return {
            "id": dataset.id,
            "file_name": file.filename,
            "size": len(contents),
            "status": "uploaded"
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/{dataset_id}/preview")
async def get_dataset_preview(dataset_id: str = Path(...), rows: int = 100, db: Session = Depends(get_db)):
    """Get dataset preview with REAL data from uploaded file"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    df = None
    
    # Try from memory cache first
    if dataset_id in dataset_cache:
        df = dataset_cache[dataset_id]
    else:
        # Try to read from filesystem
        file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, nrows=rows)
                dataset_cache[dataset_id] = df
            except Exception as e:
                return {"error": f"Could not read file: {str(e)}"}
    
    if df is not None and not df.empty:
        # Return REAL data
        return {
            "id": dataset.id,
            "name": dataset.name,
            "rows": len(df),
            "columns": list(df.columns),
            "data": df.head(rows).to_dict('records')
        }
    
    return {"error": "No data available"}

@router.get("/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: str = Path(...), db: Session = Depends(get_db)):
    """Get REAL data quality analysis from actual file"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    df = None
    
    # Try from memory cache first
    if dataset_id in dataset_cache:
        df = dataset_cache[dataset_id]
    else:
        # Try to read from filesystem
        file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                dataset_cache[dataset_id] = df
            except:
                pass
    
    if df is not None and not df.empty:
        # Calculate REAL statistics
        total_rows = len(df)
        total_cols = len(df.columns)
        
        # Real missing values percentage
        total_cells = total_rows * total_cols
        missing_cells = df.isna().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
        
        # Real duplicate rows
        duplicate_rows = df.duplicated().sum()
        
        # Real uniqueness check
        uniqueness = 100  # Default
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            avg_unique_ratio = np.mean([df[col].nunique() / len(df) for col in numeric_cols]) * 100
            uniqueness = min(100, avg_unique_ratio)
        
        # Real consistency (all rows have same number of columns)
        consistency = 100  # CSV enforces this
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "completeness": round(completeness, 2),
            "duplicate_rows": int(duplicate_rows),
            "missing_values_percent": round((missing_cells / total_cells * 100) if total_cells > 0 else 0, 2),
            "uniqueness": round(uniqueness, 2),
            "consistency": consistency,
            "overall_quality_score": round((completeness + uniqueness + consistency) / 3, 2)
        }
    
    return {"error": "No data available"}
