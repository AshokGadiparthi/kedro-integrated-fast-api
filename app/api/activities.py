"""Activities API Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from app.core.database import get_db
from app.models.models import Activity
from app.schemas import ActivityCreate, ActivityResponse

router = APIRouter(prefix="/api/activities", tags=["Activities"])

@router.get("/", response_model=list)
async def list_activities(db: Session = Depends(get_db)):
    """List all activities"""
    activities = db.query(Activity).all()
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "details": a.details,
            "created_at": a.created_at.isoformat() if a.created_at else ""
        }
        for a in activities
    ]

@router.post("/", response_model=ActivityResponse)
async def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    """Create new activity"""
    new_activity = Activity(
        id=str(uuid4()),
        user_id="user-001",
        action=activity.action,
        entity_type=activity.entity_type,
        entity_id=activity.entity_id,
        details=activity.details,
        created_at=datetime.now()
    )
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    
    return {
        "id": new_activity.id,
        "user_id": new_activity.user_id,
        "action": new_activity.action,
        "entity_type": new_activity.entity_type,
        "entity_id": new_activity.entity_id,
        "details": new_activity.details,
        "created_at": new_activity.created_at.isoformat()
    }
