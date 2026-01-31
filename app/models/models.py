"""
Database Models - PHASE 0
===========================
SQLAlchemy ORM models for User and Workspace

WHAT THESE DO:
- Map Python classes to database tables
- Define relationships
- Handle data validation at DB level
- Enable easy queries
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    """
    User model - represents a user account
    
    Fields:
    - id: Unique identifier (UUID)
    - email: Email address (unique, indexed for fast lookup)
    - username: Username (unique, indexed)
    - hashed_password: BCrypt hashed password
    - full_name: Optional full name
    - is_active: Account status
    - created_at: When user registered
    - workspaces: Relationship to Workspace model
    
    Database table: users
    """
    
    __tablename__ = "users"
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Required Fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Optional Fields
    full_name = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    workspaces = relationship(
        "Workspace",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<User {self.email} ({self.id})>"
    
    def to_dict(self):
        """Convert to dictionary (for debugging)"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# WORKSPACE MODEL
# ============================================================================

class Workspace(Base):
    """
    Workspace model - represents a project workspace for a user
    
    Multi-tenant isolation:
    - Each workspace belongs to one owner (User)
    - Workspace cannot be accessed by other users
    - In future phases: Projects belong to Workspace
    
    Fields:
    - id: Unique identifier
    - name: Workspace name
    - description: Optional description
    - slug: URL-friendly name (like "my-workspace")
    - owner_id: Foreign key to User
    - is_active: Is workspace available
    - created_at: When created
    - updated_at: When last modified
    - owner: Relationship back to User
    
    Database table: workspaces
    """
    
    __tablename__ = "workspaces"
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Required Fields
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, index=True)  # Indexed for lookup
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Optional Fields
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship(
        "User",
        back_populates="workspaces",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<Workspace {self.name} ({self.id})>"
    
    def to_dict(self):
        """Convert to dictionary (for debugging)"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "owner_id": self.owner_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# FUTURE MODELS (Placeholders for upcoming phases)
# ============================================================================

# Phase 1: Projects
# class Project(Base):
#     __tablename__ = "projects"
#     # Will be created in Phase 1

# Phase 2: Data Ingestion
# class Datasource(Base):
#     __tablename__ = "datasources"
# 
# class Dataset(Base):
#     __tablename__ = "datasets"

# And many more in future phases...
