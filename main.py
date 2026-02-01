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
    
    # Step 2: Import all models (Simplified - No Workspaces)
    print("  → Importing models...")
    from app.models.models import User, Project, Datasource, Dataset, Model, Activity
    print("  ✅ All models imported and registered")
    
    # 🔒 SAFEGUARD: Verify Base.metadata is not empty
    print("  → Verifying Base registration...")
    if len(Base.metadata.tables) == 0:
        raise RuntimeError(
            "❌ CRITICAL ERROR: Base.metadata.tables is EMPTY!\n"
            "This means models.py is using a different Base instance.\n"
            "Fix: models.py must import Base from app.core.database\n"
            "     Do NOT do: Base = declarative_base()\n"
            "Check: app/models/models.py line ~13"
        )
    print(f"  ✅ Base registration verified ({len(Base.metadata.tables)} tables)")
    
    # Step 3: Create all tables
    print("  → Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✅ All tables created")
    
    print("\n✅ Database initialization SUCCESSFUL!")
    print("📊 Tables created:")
    print("   - users")
    print("   - projects (owned by users, NO workspace)")
    print("   - datasources, datasets, models")
    print("   - activities (audit log)")
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
# MIDDLEWARE - CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # React dev server
        "http://localhost:3000",      # Alternative React dev
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://192.168.1.147:5173",  # Your machine React
        "http://192.168.1.147:3000",
        "*",                          # Allow all (for development)
    ],
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

    # Projects (Direct - No Workspace)
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

    # Datasources & Datasets (Phase 3)
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
