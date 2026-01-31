"""
Database Models - PHASE 0 + PHASE 1 + PHASE 2 + PHASE 3
========================================================
SQLAlchemy ORM models for all phases

PHASES:
- Phase 0: User, Workspace
- Phase 1: Project
- Phase 2: Datasource, Dataset, Model, Activity
- Phase 3: Enhanced Datasource, Dataset with blob storage & quality metrics
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Float, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

# ============================================================================
# USER MODEL - PHASE 0
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
# WORKSPACE MODEL - PHASE 0
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
    models = relationship("Model", back_populates="project", cascade="all, delete-orphan", lazy="select")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Project {self.name}>"


# ============================================================================
# DATASOURCE MODEL - PHASE 2 + PHASE 3 ENHANCED
# ============================================================================

class Datasource(Base):
    """
    Datasource model - represents a data source (file upload or database connection)
    
    Supported types:
    - File: csv, excel, json, parquet
    - Database: postgresql, mysql, sqlite, oracle, mssql
    - Cloud: s3, bigquery, snowflake
    - API: rest, graphql
    
    Phase 3 Enhancements:
    - Connection testing with status tracking
    - Comprehensive metadata (tags, documentation)
    - Test result history
    """
    
    __tablename__ = "datasources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # csv, postgresql, mysql, s3, api, etc
    description = Column(Text, nullable=True)
    
    # Connection config (encrypted in production)
    connection_config = Column(JSON, nullable=True)  # Store credentials securely
    
    # File upload info
    file_path = Column(String(500), nullable=True)  # Path to uploaded file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Status & Testing (Phase 3)
    status = Column(String(50), default="disconnected")  # connected, disconnected, error, testing
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)  # Connection test passed
    last_tested_at = Column(DateTime, nullable=True)  # When was connection last tested
    test_result = Column(JSON, nullable=True)  # Test result details
    
    # Metadata (Phase 3)
    tags = Column(JSON, nullable=True)  # ["production", "critical"]
    owner = Column(String(255), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="datasources", lazy="select")
    datasets = relationship("Dataset", back_populates="datasource", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Datasource {self.name} ({self.type})>"


# ============================================================================
# DATASET MODEL - PHASE 2 + PHASE 3 ENHANCED
# ============================================================================

class Dataset(Base):
    """
    Dataset model - represents processed data ready for ML
    
    A dataset is created from a datasource after:
    - File upload / database connection
    - Data preview validation
    - Optional data cleaning
    - Column selection
    
    Phase 3 Enhancements:
    - BLOB storage for file content in database
    - Auto schema inference with confidence
    - Data quality metrics (completeness, validity, etc)
    - Versioning support
    - Kedro catalog integration
    """
    
    __tablename__ = "datasets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    datasource_id = Column(String(36), ForeignKey("datasources.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # File information (Phase 3)
    file_name = Column(String(255), nullable=True)
    file_format = Column(String(50), nullable=True)  # csv, json, parquet, excel, etc
    file_content = Column(LargeBinary, nullable=True)  # Actual file stored as BLOB
    
    # Data info
    row_count = Column(Integer, nullable=True)  # Number of rows
    column_count = Column(Integer, nullable=True)  # Number of columns
    columns_info = Column(JSON, nullable=True)  # Column names, types, null counts
    
    # Data quality (Phase 3)
    quality_score = Column(Float, nullable=True)  # 0-100%
    missing_values_count = Column(Integer, nullable=True)
    missing_values_pct = Column(Float, nullable=True)
    duplicate_rows_count = Column(Integer, nullable=True)
    duplicate_rows_pct = Column(Float, nullable=True)
    
    # Schema inference (Phase 3)
    schema_inferred = Column(Boolean, default=False)
    schema_confidence = Column(Float, nullable=True)  # 0-100%
    
    # Versioning (Phase 3)
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    parent_version_id = Column(String(36), nullable=True)
    
    # Status
    is_processed = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="processing")  # processing, ready, error, archived
    
    # Kedro integration (Phase 3)
    is_kedro_registered = Column(Boolean, default=False)
    kedro_catalog_name = Column(String(255), nullable=True)
    
    # Tags and lineage (Phase 3)
    tags = Column(JSON, nullable=True)  # ["transactions", "monthly"]
    lineage_info = Column(JSON, nullable=True)  # Upstream/downstream dependencies
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="datasets", lazy="select")
    datasource = relationship("Datasource", back_populates="datasets", lazy="select")
    
    def __repr__(self):
        return f"<Dataset {self.name}>"


# ============================================================================
# MODEL MODEL - PHASE 2
# ============================================================================

class Model(Base):
    """
    Model model - represents a trained ML model
    
    Fields:
    - id: Unique identifier
    - project_id: Foreign key to Project
    - name: Model name
    - algorithm: Algorithm used
    - accuracy: Model accuracy
    """
    
    __tablename__ = "models"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    algorithm = Column(String(100), nullable=True)
    accuracy = Column(Float, nullable=True)
    status = Column(String(50), default="Training", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="models", lazy="select")
    
    def __repr__(self):
        return f"<Model {self.name}>"


# ============================================================================
# ACTIVITY MODEL - PHASE 2
# ============================================================================

class Activity(Base):
    """
    Activity model - represents project activities/audit logs
    
    Tracks:
    - User actions
    - Model training
    - Dataset uploads
    - Configuration changes
    """
    
    __tablename__ = "activities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    action_type = Column(String(100), nullable=False)  # upload, train, evaluate, etc
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="activities", lazy="select")
    
    def __repr__(self):
        return f"<Activity {self.action_type}>"

