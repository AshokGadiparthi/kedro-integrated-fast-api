"""
SQLAlchemy Models - Phase 3
All models properly structured to ensure registration with Base
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, JSON, ForeignKey, LargeBinary, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# ============================================================================
# ASSOCIATION TABLE - Define FIRST
# ============================================================================

model_datasets = Table(
    'model_datasets',
    Base.metadata,
    Column('model_id', String(36), ForeignKey('models.id'), primary_key=True),
    Column('dataset_id', String(36), ForeignKey('datasets.id'), primary_key=True)
)

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(500), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    workspaces = relationship("Workspace", back_populates="owner", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"

# ============================================================================
# WORKSPACE MODEL
# ============================================================================

class Workspace(Base):
    __tablename__ = 'workspaces'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    owner = relationship("User", back_populates="workspaces", lazy="select")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan", lazy="select")
    activities = relationship("Activity", back_populates="workspace", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Workspace {self.name}>"

# ============================================================================
# PROJECT MODEL
# ============================================================================

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    workspace = relationship("Workspace", back_populates="projects", lazy="select")
    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan", lazy="select")
    datasources = relationship("Datasource", back_populates="project", cascade="all, delete-orphan", lazy="select")
    models = relationship("Model", back_populates="project", cascade="all, delete-orphan", lazy="select")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Project {self.name}>"

# ============================================================================
# DATASOURCE MODEL
# ============================================================================

class Datasource(Base):
    __tablename__ = 'datasources'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(String(500), nullable=True)
    connection_config = Column(JSON, nullable=True)
    status = Column(String(50), default='untested')
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)
    last_tested_at = Column(DateTime, nullable=True)
    test_result = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    owner = Column(String(255), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="datasources", lazy="select")
    datasets = relationship("Dataset", back_populates="datasource", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Datasource {self.name}>"

# ============================================================================
# DATASET MODEL
# ============================================================================

class Dataset(Base):
    __tablename__ = 'datasets'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    datasource_id = Column(String(36), ForeignKey('datasources.id', ondelete='SET NULL'), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_format = Column(String(50), nullable=True)
    file_content = Column(LargeBinary, nullable=True)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    columns_info = Column(JSON, nullable=True)
    quality_score = Column(Float, nullable=True)
    missing_values_count = Column(Integer, nullable=True)
    missing_values_pct = Column(Float, nullable=True)
    duplicate_rows_count = Column(Integer, nullable=True)
    duplicate_rows_pct = Column(Float, nullable=True)
    schema_inferred = Column(Boolean, default=False)
    schema_confidence = Column(Float, nullable=True)
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    parent_version_id = Column(String(36), nullable=True)
    status = Column(String(50), default='ready')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="datasets", lazy="select")
    datasource = relationship("Datasource", back_populates="datasets", lazy="select")
    models = relationship("Model", secondary=model_datasets, back_populates="datasets", lazy="select")
    
    def __repr__(self):
        return f"<Dataset {self.name}>"

# ============================================================================
# MODEL MODEL
# ============================================================================

class Model(Base):
    __tablename__ = 'models'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_type = Column(String(100), nullable=False)
    algorithm = Column(String(100), nullable=True)
    parameters = Column(JSON, nullable=True)
    model_path = Column(String(500), nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    status = Column(String(50), default='untrained')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="models", lazy="select")
    datasets = relationship("Dataset", secondary=model_datasets, back_populates="models", lazy="select")
    
    def __repr__(self):
        return f"<Model {self.name}>"

# ============================================================================
# ACTIVITY MODEL
# ============================================================================

class Activity(Base):
    __tablename__ = 'activities'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    workspace_id = Column(String(36), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True)
    project_id = Column(String(36), ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="activities", lazy="select")
    workspace = relationship("Workspace", back_populates="activities", lazy="select")
    project = relationship("Project", back_populates="activities", lazy="select")
    
    def __repr__(self):
        return f"<Activity {self.action}>"

