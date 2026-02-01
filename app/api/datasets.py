"""Datasets API Routes"""
from fastapi import APIRouter
from app.schemas import DatasetCreate, DatasetResponse

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

@router.get("/", response_model=list)
async def list_datasets():
    return []

@router.post("/", response_model=DatasetResponse)
async def create_dataset(dataset: DatasetCreate):
    return {
        "id": "mock-id",
        "name": dataset.name,
        "project_id": dataset.project_id,
        "description": dataset.description,
        "file_name": "data.csv",
        "file_size_bytes": 0,
        "created_at": "2026-02-01"
    }
