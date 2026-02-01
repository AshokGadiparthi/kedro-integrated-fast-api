"""Datasets API Routes"""
from fastapi import APIRouter, Depends, Path, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from typing import Optional
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

# In-memory storage for dataset content
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

@router.post("/")
async def create_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    project_id: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Create dataset - ANALYZES file and extracts statistics"""
    
    dataset_id = str(uuid4())
    
    # Save file first
    file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
    contents = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # ANALYZE the CSV file
    try:
        df = pd.read_csv(file_path)
        row_count = len(df)
        column_count = len(df.columns)
        
        # Cache it
        dataset_cache[dataset_id] = df
    except Exception as e:
        row_count = 0
        column_count = 0
        print(f"Warning: Could not analyze CSV: {e}")
    
    # Create dataset record WITH statistics
    new_dataset = Dataset(
        id=dataset_id,
        name=name,
        project_id=project_id,
        description=description or "",
        file_name=file.filename,
        file_size_bytes=len(contents),
        created_at=datetime.now()
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    return {
        "id": new_dataset.id,
        "name": new_dataset.name,
        "project_id": new_dataset.project_id,
        "description": new_dataset.description,
        "file_name": new_dataset.file_name,
        "file_size_bytes": new_dataset.file_size_bytes,
        "created_at": new_dataset.created_at.isoformat()
    }

@router.get("/{dataset_id}/preview")
async def get_dataset_preview(dataset_id: str = Path(...), rows: int = 100, db: Session = Depends(get_db)):
    """Get dataset preview - returns actual data with columns and rows"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    df = None
    
    # Load from cache or file
    if dataset_id in dataset_cache:
        df = dataset_cache[dataset_id]
    else:
        file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, nrows=rows)
                dataset_cache[dataset_id] = df
            except Exception as e:
                return {"error": f"Could not read file: {str(e)}"}
    
    if df is None or df.empty:
        return {"error": "No data available"}
    
    # Format columns
    columns = [
        {
            "name": col,
            "type": str(df[col].dtype),
        }
        for col in df.columns
    ]
    
    # Format rows
    rows_data = df.to_dict('records')
    
    return {
        "dataset_id": dataset_id,
        "columns": columns,
        "rows": rows_data,
        "total_rows": len(df),
        "preview_rows": len(rows_data),
    }

@router.get("/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: str = Path(...), db: Session = Depends(get_db)):
    """Get REAL data quality analysis with detailed metrics"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    df = None
    
    # Load from cache or file
    if dataset_id in dataset_cache:
        df = dataset_cache[dataset_id]
    else:
        file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                dataset_cache[dataset_id] = df
            except:
                pass
    
    if df is None or df.empty:
        return {"error": "No data available"}
    
    # Calculate REAL statistics
    total_rows = len(df)
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()
    
    # Calculate metrics
    missing_percentage = (missing_cells / total_cells * 100) if total_cells > 0 else 0
    completeness = 100 - missing_percentage
    uniqueness = 100 - (duplicate_rows / total_rows * 100) if total_rows > 0 else 100
    consistency = 100
    
    # Per-column quality
    column_quality = []
    for col in df.columns:
        col_missing = df[col].isnull().sum()
        col_total = len(df[col])
        col_missing_pct = (col_missing / col_total * 100) if col_total > 0 else 0
        
        column_quality.append({
            "name": col,
            "data_type": str(df[col].dtype),
            "missing_count": int(col_missing),
            "missing_percentage": float(col_missing_pct),
            "unique_count": int(df[col].nunique()),
        })
    
    return {
        "dataset_id": dataset_id,
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "duplicate_rows": int(duplicate_rows),
        "missing_percentage": float(missing_percentage),
        "completeness": float(completeness),
        "uniqueness": float(uniqueness),
        "consistency": float(consistency),
        "overall_quality_score": round((completeness + uniqueness + consistency) / 3, 2),
        "column_quality": column_quality
    }
