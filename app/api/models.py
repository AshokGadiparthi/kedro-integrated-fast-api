"""Models API Routes"""
from fastapi import APIRouter
from app.schemas import ModelCreate, ModelResponse

router = APIRouter(prefix="/api/models", tags=["Models"])

@router.get("/", response_model=list)
async def list_models():
    return []

@router.post("/", response_model=ModelResponse)
async def create_model(model: ModelCreate):
    return {
        "id": "mock-id",
        "name": model.name,
        "project_id": model.project_id,
        "description": model.description,
        "model_type": model.model_type,
        "created_at": "2026-02-01"
    }
