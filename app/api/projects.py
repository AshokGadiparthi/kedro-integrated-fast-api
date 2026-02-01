"""Projects API Routes"""
from fastapi import APIRouter, Depends
from app.schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("/", response_model=list)
async def list_projects():
    return []

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    return {
        "id": "mock-id",
        "name": project.name,
        "description": project.description,
        "owner_id": "mock-owner",
        "created_at": "2026-02-01"
    }
