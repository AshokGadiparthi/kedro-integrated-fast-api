"""Database Models"""
from sqlalchemy import Column, String, DateTime, Text, Integer
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

class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Dataset(Base):
    """Dataset model"""
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    project_id = Column(String, index=True)
    description = Column(Text, nullable=True)
    file_name = Column(String)
    file_size_bytes = Column(Integer)
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

class Datasource(Base):
    """Datasource model"""
    __tablename__ = "datasources"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    type = Column(String)
    connection_string = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Model(Base):
    """ML Model model"""
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    project_id = Column(String, index=True)
    description = Column(Text, nullable=True)
    model_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
