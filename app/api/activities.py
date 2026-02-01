"""Activities API Routes"""
from fastapi import APIRouter
from app.schemas import ActivityCreate, ActivityResponse

router = APIRouter(prefix="/api/activities", tags=["Activities"])

@router.get("/", response_model=list)
async def list_activities():
    return []

@router.post("/", response_model=ActivityResponse)
async def create_activity(activity: ActivityCreate):
    return {
        "id": "mock-id",
        "user_id": "mock-user",
        "action": activity.action,
        "entity_type": activity.entity_type,
        "entity_id": activity.entity_id,
        "details": activity.details,
        "created_at": "2026-02-01"
    }
