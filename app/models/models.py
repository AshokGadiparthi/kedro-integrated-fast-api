"""Database Models"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Dataset(Base):
    """Dataset model"""
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    project_id = Column(String, index=True)
    file_name = Column(String)
    file_size_bytes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Activity(Base):
    """Activity model"""
    __tablename__ = "activities"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    project_id = Column(String, nullable=True)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
