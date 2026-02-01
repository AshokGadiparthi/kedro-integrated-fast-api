"""
Database Configuration - PHASE 0
==================================
SQLAlchemy setup with SQLite (easy for local development)
Later: Migrate to PostgreSQL

WHY SQLITE?
- No setup needed
- Perfect for local development
- Easy to test
- File-based database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE URL
# ============================================================================

# Get database URL from environment or use SQLite default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ml_platform.db")

# Echo SQL queries (helpful for learning)
ECHO_SQL = os.getenv("ECHO_SQL", "true").lower() == "true"

# ============================================================================
# CREATE ENGINE
# ============================================================================

if "sqlite" in DATABASE_URL:
    # SQLite specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=ECHO_SQL
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        DATABASE_URL,
        echo=ECHO_SQL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

# ============================================================================
# SESSION FACTORY
# ============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# ============================================================================
# BASE CLASS FOR MODELS
# ============================================================================

# ⚠️ CRITICAL: This Base instance MUST be used by ALL models
# Do NOT create another declarative_base() anywhere else!
# 
# If models.py creates its own Base instance:
#   - Base.metadata will be empty
#   - Tables won't be created
#   - Database will be created but no tables in it
#
# All ORM models inherit from this
Base = declarative_base()

# 🔒 SAFEGUARD: Verify this Base is registered with models
# This is checked in main.py and verify_all.py
# If you see "Base.metadata has 0 tables" - models.py is using wrong Base!

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db():
    """
    Dependency for FastAPI routes to get database session
    
    Usage in routes:
    @app.get("/items")
    def get_items(db: Session = Depends(get_db)):
        items = db.query(Item).all()
        return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """
    Create all database tables
    
    Run this once:
    $ python -c "from app.core.database import init_db; init_db()"
    """
    # IMPORTANT: Import models so they register with Base
    from app.models.models import User, Workspace, Project, Datasource, Dataset, Model, Activity
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully!")

def drop_db():
    """
    Drop all tables (for testing/cleanup)
    
    DANGEROUS - Only use in development!
    """
    # IMPORTANT: Import models so they register with Base
    from app.models.models import User, Workspace, Project, Datasource, Dataset, Model, Activity
    
    logger.warning("⚠️  Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ Database dropped!")

def reset_db():
    """
    Reset database (drop and recreate)
    
    DANGEROUS - Only use in development!
    """
    drop_db()
    init_db()
