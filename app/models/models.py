"""Database Models"""
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func
from uuid import uuid4
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
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, index=True)
    project_id = Column(String, nullable=True)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EdaResult(Base):
    """EDA Analysis Results - stores all analysis data"""
    __tablename__ = "eda_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, index=True, unique=True)
    user_id = Column(String, index=True)
    
    # Summary data (JSON stored as text)
    summary = Column(Text)  # {shape, columns, dtypes, memory_usage}
    
    # Statistics data (JSON stored as text)
    statistics = Column(Text)  # {basic_stats, missing_values, duplicates}
    
    # Quality metrics (JSON stored as text)
    quality = Column(Text)  # {completeness, uniqueness, validity, consistency, etc}
    
    # Correlations (JSON stored as text)
    correlations = Column(Text)  # {correlations dict, threshold}
    
    # Metadata
    analysis_status = Column(String, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ============================================================================
# EDA RESULT MODELS - Store analysis results in database
# ============================================================================

class EDASummary(Base):
    """EDA Summary - Basic profile information"""
    __tablename__ = "eda_summary"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    shape_rows = Column(Integer)
    shape_cols = Column(Integer)
    columns = Column(Text)  # JSON string of column names
    dtypes = Column(Text)  # JSON string of column dtypes
    memory_usage = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EDAStatistics(Base):
    """EDA Statistics - Descriptive statistics"""
    __tablename__ = "eda_statistics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    basic_stats = Column(Text)  # JSON string of describe() results
    missing_values = Column(Text)  # JSON string of missing values by column
    duplicates = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EDAQuality(Base):
    """EDA Quality Report - Data quality metrics"""
    __tablename__ = "eda_quality"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    completeness = Column(String)  # Percentage as string
    uniqueness = Column(String)
    validity = Column(String)
    consistency = Column(String)
    duplicate_rows = Column(Integer)
    missing_values_count = Column(Integer)
    total_cells = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EDACorrelations(Base):
    """EDA Correlations - Correlation matrix"""
    __tablename__ = "eda_correlations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    dataset_id = Column(String, unique=True, index=True)
    correlations = Column(Text)  # JSON string of correlations
    threshold = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Datasource(Base):
    """Datasource model"""
    __tablename__ = "datasources"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    type = Column(String)
    description = Column(Text, nullable=True)
    project_id = Column(String, index=True)
    host = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
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
