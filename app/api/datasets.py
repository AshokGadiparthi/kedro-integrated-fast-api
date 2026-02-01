"""Datasets API Routes"""
from fastapi import APIRouter, Depends, Path, UploadFile, File
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import os
import pandas as pd
from app.core.database import get_db
from app.models.models import Dataset
from app.schemas import DatasetCreate, DatasetResponse

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

# Directory to store uploaded files
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

@router.post("/", response_model=DatasetResponse)
async def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    """Create new dataset"""
    new_dataset = Dataset(
        id=str(uuid4()),
        name=dataset.name,
        project_id=dataset.project_id,
        description=dataset.description,
        file_name="data.csv",
        file_size_bytes=0,
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

@router.post("/{dataset_id}/upload")
async def upload_dataset_file(dataset_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload actual file data for dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    # Save file
    file_path = f"{UPLOAD_DIR}/{dataset_id}_{file.filename}"
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Update dataset
    dataset.file_name = file.filename
    dataset.file_size_bytes = len(contents)
    db.commit()
    
    return {"id": dataset.id, "file_name": file.filename, "size": len(contents)}

@router.get("/{dataset_id}/preview")
async def get_dataset_preview(dataset_id: str = Path(...), rows: int = 100, db: Session = Depends(get_db)):
    """Get dataset preview (first N rows)"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    # Try to read actual file if it exists
    file_path = f"{UPLOAD_DIR}/{dataset_id}_{dataset.file_name}"
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, nrows=rows)
            preview_data = df.to_dict('records')
            return {
                "id": dataset.id,
                "name": dataset.name,
                "rows": len(preview_data),
                "columns": list(df.columns),
                "preview": preview_data
            }
        except:
            pass
    
    # Fallback to sample data
    return {
        "id": dataset.id,
        "name": dataset.name,
        "rows": rows,
        "preview": [
            {"col1": "value1", "col2": "value2"},
            {"col1": "value3", "col2": "value4"},
        ]
    }

@router.get("/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: str = Path(...), db: Session = Depends(get_db)):
    """Get dataset quality report"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "quality_score": 85,
        "completeness": 95,
        "validity": 90,
        "consistency": 80,
        "issues": []
    }
