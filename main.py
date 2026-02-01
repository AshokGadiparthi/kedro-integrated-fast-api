"""
ML Platform - Main Application
UPDATED: Integrated with EDA module
All routes included: Auth, Projects, Datasets, Models, Activities, EDA
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.database import engine, Base, init_db
from app.api import auth, projects, datasets, datasources, models, activities, eda
# IMPORTANT: Import ALL models so they register with Base for table creation
from app.models.models import User, Project, Dataset, Activity, Datasource, Model
from app.api.phase3_correlations_endpoints import router as phase3_router  # ✅ ADD THIS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# STARTUP/SHUTDOWN LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    
    # STARTUP
    logger.info("🚀 Starting ML Platform Application...")
    
    # Create database tables
    logger.info("📦 Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")
    
    # Initialize default data
    init_db()
    logger.info("✅ Default data initialized")
    
    logger.info("=" * 70)
    logger.info("✅ ML PLATFORM READY!")
    logger.info("=" * 70)
    logger.info("📍 API Documentation: http://localhost:8000/docs")
    logger.info("📍 EDA Health: GET /api/eda/health")
    logger.info("=" * 70)
    
    yield  # Application is running
    
    # SHUTDOWN
    logger.info("🛑 Shutting down ML Platform...")
    logger.info("✅ Cleanup complete")

# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

app = FastAPI(
    title="ML Platform with EDA",
    description="Complete ML Platform with Exploratory Data Analysis",
    version="1.0.0",
    lifespan=lifespan
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
# ROUTE REGISTRATION
# ============================================================================

# Auth routes
app.include_router(auth.router, tags=["Authentication"])

# Core routes
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(datasources.router)
app.include_router(models.router)
app.include_router(activities.router)

# EDA routes (NEW)
app.include_router(eda.router)

app.include_router(phase3_router)           # ✅ Phase 3 Correlations - ADD THIS LINE

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Application health check"""
    return {
        "status": "healthy",
        "service": "ML Platform with EDA",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "projects": "/api/projects",
            "datasets": "/api/datasets",
            "datasources": "/api/datasources",
            "models": "/api/models",
            "activities": "/api/activities",
            "eda": "/api/eda",
            "docs": "/docs"
        }
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# ============================================================================
# APPLICATION STARTUP MESSAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    logger.info("🎯 ML Platform starting on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
