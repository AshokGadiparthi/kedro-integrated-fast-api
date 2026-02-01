"""Datasources API Routes"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/datasources", tags=["Datasources"])

@router.get("/")
async def list_datasources():
    return []

@router.post("/")
async def create_datasource(data: dict):
    return {"id": "mock-id", "name": data.get("name", "datasource")}
