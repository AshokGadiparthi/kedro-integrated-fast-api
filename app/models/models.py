"""
Database Models - PHASE 0 + PHASE 1 + PHASE 2
==============================================
SQLAlchemy ORM models for all phases

PHASES:
- Phase 0: User, Workspace
- Phase 1: Project
- Phase 2: Datasource, Dataset
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    """User model - represents a user account"""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    workspaces = relationship(
        "Workspace",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<User {self.email}>"


# ============================================================================
# WORKSPACE MODEL
# ============================================================================

class Workspace(Base):
    """Workspace model - represents a project workspace for a user"""
    
    __tablename__ = "workspaces"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    owner = relationship("User", back_populates="workspaces", lazy="select")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Workspace {self.name}>"


# ============================================================================
# PROJECT MODEL - PHASE 1
# ============================================================================

class Project(Base):
    """Project model - represents a machine learning project"""
    
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    problem_type = Column(String(50), nullable=False, default="Classification")
    status = Column(String(50), default="Active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    workspace = relationship("Workspace", back_populates="projects", lazy="select")
    datasources = relationship("Datasource", back_populates="project", cascade="all, delete-orphan", lazy="select")
    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Project {self.name}>"


# ============================================================================
# DATASOURCE MODEL - PHASE 2
# ============================================================================

class Datasource(Base):
    """
    Datasource model - represents a data source (file upload or database connection)
    
    Supported types:
    - csv, excel, json, parquet (file uploads)
    - bigquery, snowflake, postgresql, mysql, oracle, db2, hadoop (database connections)
    """
    
    __tablename__ = "datasources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # csv, excel, bigquery, snowflake, etc
    description = Column(Text, nullable=True)
    
    # Connection config (encrypted in production)
    connection_config = Column(JSON, nullable=True)  # Store credentials securely
    
    # File upload info
    file_path = Column(String(500), nullable=True)  # Path to uploaded file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)  # Connection test passed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="datasources", lazy="select")
    datasets = relationship("Dataset", back_populates="datasource", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Datasource {self.name} ({self.type})>"


# ============================================================================
# DATASET MODEL - PHASE 2
# ============================================================================

class Dataset(Base):
    """
    Dataset model - represents processed data ready for ML
    
    A dataset is created from a datasource after:
    - File upload / database connection
    - Data preview validation
    - Optional data cleaning
    - Column selection
    """
    
    __tablename__ = "datasets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    datasource_id = Column(String(36), ForeignKey("datasources.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Data info
    row_count = Column(Integer, nullable=True)  # Number of rows
    column_count = Column(Integer, nullable=True)  # Number of columns
    columns_info = Column(JSON, nullable=True)  # Column names, types, null counts
    
    # Data quality
    missing_values_count = Column(Integer, nullable=True)
    duplicate_rows_count = Column(Integer, nullable=True)
    
    # Status
    is_processed = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="datasets", lazy="select")
    datasource = relationship("Datasource", back_populates="datasets", lazy="select")
    
    def __repr__(self):
        return f"<Dataset {self.name}>"


# ============================================================================
# FUTURE MODELS (Placeholders)
# ============================================================================

# Phase 3: EDA & Features
# class EDAReport(Base):
#     __tablename__ = "eda_reports"
# 
# class Feature(Base):
#     __tablename__ = "features"

# Phase 4: Algorithms
# class Algorithm(Base):
#     __tablename__ = "algorithms"

# And many more in future phases...
