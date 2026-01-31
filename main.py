"""
ML Platform - FastAPI Entry Point
===================================
PHASE 0-3: Complete ML Platform with Models, Activities & Data Management

Includes automatic database bootstrap on startup.

Run with:
    python main.py

Then visit: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# BOOTSTRAP - Initialize database automatically on startup
# ============================================================================

print("=" * 70)
print("🚀 Starting ML Platform API...")
print("🔄 Initializing database...")
print("=" * 70)

try:
    # Step 1: Import database engine and Base
    print("  → Importing database engine...")
    from app.core.database import engine, Base
    print("  ✅ Database engine imported")
    
    # Step 2: Import Phase 0-1 models
    print("  → Importing Phase 0-1 models...")
    from app.models.models import User, Workspace, Project, Datasource, Dataset, Model, Activity
    print("  ✅ Phase 0-1 models imported")
    
    # Step 3: Import Phase 3 data management models
    print("  → Importing Phase 3 data management models...")
    from app.models.data_management import Datasource as DatasourceV2, Dataset as DatasetV2, DataProfile
    print("  ✅ Data management models imported")
    
    # Step 4: Create all tables
    print("  → Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✅ All tables created")
    
    print("\n✅ Database initialization SUCCESSFUL!")
    print("📊 Tables created:")
    print("   - Phase 0: users, workspaces")
    print("   - Phase 1: projects")
    print("   - Phase 3: datasources, datasets, data_profiles, models, activities")
    print("=" * 70 + "\n")
    
    logger.info("✅ Database initialization complete!")
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    logger.error(f"Import failed: {e}")
    raise
    
except Exception as e:
    print(f"\n❌ DATABASE ERROR: {e}")
    logger.error(f"Database initialization failed: {e}")
    raise

# Create FastAPI app
app = FastAPI(
    title="ML Platform API",
    description="Complete ML Platform with Data Management",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0"
    }

# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

logger.info("🔄 Registering API routes...")

try:
    # Auth
    from app.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    logger.info("✅ Auth routes")

    # Workspaces
    from app.api.workspaces import router as workspaces_router
    app.include_router(workspaces_router, prefix="/api/workspaces", tags=["Workspaces"])
    logger.info("✅ Workspaces routes")

    # Projects
    from app.api.projects import router as projects_router
    app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
    logger.info("✅ Projects routes")

    # Models
    from app.api.models import router as models_router
    app.include_router(models_router, prefix="/api/models", tags=["Models"])
    logger.info("✅ Models routes")

    # Activities
    from app.api.activities import router as activities_router
    app.include_router(activities_router, prefix="/api/activities", tags=["Activities"])
    logger.info("✅ Activities routes")

    # Datasources & Datasets (NEW)
    from app.api.datasources import router as datasources_router
    app.include_router(datasources_router, prefix="/api/datasources", tags=["Datasources"])
    logger.info("✅ Datasources routes")

    from app.api.datasets import router as datasets_router
    app.include_router(datasets_router, prefix="/api/datasets", tags=["Datasets"])
    logger.info("✅ Datasets routes")

    logger.info("✅ All routes registered!")
    print("\n🎉 API Ready!\n")

except Exception as e:
    logger.error(f"Failed to register routes: {e}")
    raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
