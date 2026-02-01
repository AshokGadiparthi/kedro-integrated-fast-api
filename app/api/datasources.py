"""Datasources API Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from app.core.database import get_db

router = APIRouter(prefix="/api/datasources", tags=["Datasources"])

@router.get("/")
async def list_datasources(db: Session = Depends(get_db)):
    """List all datasources"""
    return []

@router.post("/")
async def create_datasource(data: dict, db: Session = Depends(get_db)):
    """Create new datasource"""
    return {"id": str(uuid4()), "name": data.get("name", "datasource")}
