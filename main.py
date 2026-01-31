"""
ML Platform - FastAPI Entry Point
===================================
PHASE 0-3: Complete ML Platform with Models & Activities

Includes automatic database bootstrap on startup.

Start with:
$ python main.py

Then visit: http://192.168.1.147:8000/docs
"""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

logger.info("🚀 Starting ML Platform API...")
logger.info("🔄 Initializing database...")

try:
    from app.core.database import engine, Base
    # Import all models to register them with SQLAlchemy
    from app.models.models import User, Workspace, Project, Datasource, Dataset, Model, Activity
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("✅ Database initialized successfully!")
    logger.info("📊 Tables created: users, workspaces, projects, datasources, datasets, models, activities")
    
except Exception as e:
    logger.error(f"❌ FATAL: Database initialization failed: {e}")
    logger.error("Cannot start server without database!")
    raise

# Create FastAPI app
app = FastAPI(
    title="ML Platform API - Phase 0-3",
    description="Complete ML Platform with Models & Activities - Automatic Bootstrap",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS - Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "app": "ML Platform API",
        "phase": "0 - Authentication & Workspace Management",
        "version": "0.1.0",
        "status": "running",
        "docs_url": "http://127.0.0.1:8000/docs",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# IMPORT ROUTES
# ============================================================================

# Import route modules
from app.api import auth, workspaces, projects, datasources, datasets, models, activities

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(workspaces.router, prefix="/api/workspaces", tags=["Workspaces"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(datasources.router, prefix="/api/datasources", tags=["Datasources"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(models.router, prefix="/api/models", tags=["Models - Phase 3"])
app.include_router(activities.router, prefix="/api/activities", tags=["Activities - Phase 3"])

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    logger.error(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    logger.info("🚀 ML Platform API starting...")
    logger.info("📚 API Docs: http://127.0.0.1:8000/docs")
    logger.info("✅ Server ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown"""
    logger.info("🛑 ML Platform API shutting down...")

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
