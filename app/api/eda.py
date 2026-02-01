"""EDA API Endpoints - Exploratory Data Analysis (Universal Version)"""
import json
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.cache import cache_manager
from app.core.serializer_utils import safe_json_dumps
from app.core.universal_eda_analyzer import UniversalEDAAnalyzer
from app.models.models import EdaResult
from app.schemas.eda_schemas import (
    AnalysisRequest, AnalysisResponse, JobStatusResponse, HealthResponse,
    SummaryResponse, StatisticsSimpleResponse, QualityResponse, CorrelationsResponse
)

router = APIRouter(prefix="/api/eda", tags=["EDA"])
logger = logging.getLogger(__name__)

# ============================================================================
# AUTH HELPERS
# ============================================================================

def get_current_user(request: Request):
    """Get current user from token"""
    try:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header:
            return None
        token = auth_header.replace("Bearer ", "")
        return {"id": "mock-user-id", "token": token}
    except:
        return None

def get_user_id_from_token(request: Request) -> str:
    """Extract user_id from JWT token without database lookup"""
    try:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header:
            return "mock-user-id"
        # In production, decode JWT here
        # For now, return mock user
        return "mock-user-id"
    except:
        return "mock-user-id"

# ============================================================================
# BACKGROUND TASK: ACTUAL EDA ANALYSIS
# ============================================================================

async def run_eda_analysis(job_id: str, dataset_id: str, db: Session):
    """Background task to run EDA analysis and store in database"""
    try:
        from app.api.datasets import dataset_cache, UPLOAD_DIR
        import os
        
        file_path = f"{UPLOAD_DIR}/{dataset_id}.csv"
        
        # Get original job data
        original_job_data = await cache_manager.get(f"eda:job:{job_id}")
        if not original_job_data:
            logger.error(f"❌ Original job not found: {job_id}")
            return
        
        original_job = original_job_data if isinstance(original_job_data, dict) else json.loads(original_job_data)
        
        # Load dataset
        if dataset_id in dataset_cache:
            df = dataset_cache[dataset_id]
        elif os.path.exists(file_path):
            df = pd.read_csv(file_path)
            dataset_cache[dataset_id] = df
        else:
            failed_job = {**original_job, "status": "failed", "error": "Dataset file not found", "progress": 0}
            await cache_manager.set(f"eda:job:{job_id}", failed_job, ttl=86400)
            logger.error(f"❌ Dataset file not found: {file_path}")
            return
        
        # Update job status
        processing_job = {
            **original_job,
            "status": "processing",
            "current_phase": "Data Loading",
            "progress": 25,
            "updated_at": datetime.utcnow().isoformat()
        }
        await cache_manager.set(f"eda:job:{job_id}", processing_job, ttl=86400)
        
        # ✅ UNIVERSAL ANALYSIS (Works with ANY dataset!)
        analyzer = UniversalEDAAnalyzer(df)
        
        summary_data = analyzer.get_summary()
        summary_data["dataset_id"] = dataset_id  # Set dataset_id
        
        statistics_data = analyzer.get_statistics()
        statistics_data["dataset_id"] = dataset_id  # Set dataset_id
        
        quality_data = analyzer.get_quality_report()
        quality_data["dataset_id"] = dataset_id  # Set dataset_id
        
        correlations_data = analyzer.get_correlations()
        correlations_data["dataset_id"] = dataset_id  # Set dataset_id
        
        # Update cache with job results (for polling)
        analysis_result = {
            **original_job,
            "status": "completed",
            "progress": 100,
            "current_phase": "Complete",
            "updated_at": datetime.utcnow().isoformat(),
            "results": {
                "summary": summary_data,
                "statistics": statistics_data,
                "quality": quality_data,
                "correlations": correlations_data
            }
        }
        
        await cache_manager.set(f"eda:job:{job_id}", analysis_result, ttl=86400)
        
        # ✅ STORE IN DATABASE (with safe JSON serialization)
        try:
            existing = db.query(EdaResult).filter(EdaResult.dataset_id == dataset_id).first()
            
            if existing:
                existing.summary = safe_json_dumps(summary_data)
                existing.statistics = safe_json_dumps(statistics_data)
                existing.quality = safe_json_dumps(quality_data)
                existing.correlations = safe_json_dumps(correlations_data)
                existing.analysis_status = "completed"
                db.commit()
                logger.info(f"✅ Updated EDA results in database for: {dataset_id}")
            else:
                user_id = original_job.get("user_id", "mock-user-id")
                eda_result = EdaResult(
                    dataset_id=dataset_id,
                    user_id=user_id,
                    summary=safe_json_dumps(summary_data),
                    statistics=safe_json_dumps(statistics_data),
                    quality=safe_json_dumps(quality_data),
                    correlations=safe_json_dumps(correlations_data),
                    analysis_status="completed"
                )
                db.add(eda_result)
                db.commit()
                logger.info(f"✅ Stored EDA results in database for: {dataset_id}")
        except Exception as db_error:
            logger.error(f"❌ Database error: {str(db_error)}")
            db.rollback()
            raise
        
        logger.info(f"✅ EDA analysis completed: {job_id}")
        
    except Exception as e:
        logger.error(f"❌ EDA analysis failed: {str(e)}", exc_info=True)
        original_job_data = await cache_manager.get(f"eda:job:{job_id}")
        if original_job_data:
            original_job = original_job_data if isinstance(original_job_data, dict) else json.loads(original_job_data)
            failed_job = {
                **original_job,
                "status": "failed",
                "error": str(e),
                "progress": 0,
                "current_phase": "Failed",
                "updated_at": datetime.utcnow().isoformat()
            }
        else:
            failed_job = {
                "job_id": job_id,
                "dataset_id": dataset_id,
                "status": "failed",
                "error": str(e),
                "progress": 0,
                "current_phase": "Failed",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        await cache_manager.set(f"eda:job:{job_id}", failed_job, ttl=86400)


# ============================================================================
# ENDPOINT 1: HEALTH CHECK
# ============================================================================

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK, tags=["Health"])
async def eda_health_check():
    """✅ EDA Service Health Check"""
    logger.info(f"🏥 EDA health check requested")
    return {
        "status": "healthy",
        "service": "EDA Engine",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# ENDPOINT 2: START ANALYSIS
# ============================================================================

@router.post(
    "/dataset/{dataset_id}/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Analysis"]
)
async def start_eda_analysis(
    request: Request,
    dataset_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """✅ Start EDA Analysis - Returns job_id for polling"""
    try:
        logger.info(f"📊 EDA analysis requested for dataset: {dataset_id}")
        
        user_id = get_user_id_from_token(request)
        logger.info(f"👤 User authenticated: {user_id}")
        
        # Verify dataset exists
        from app.models.models import Dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        logger.info(f"✅ Dataset verified: {dataset.file_name}")
        
        # Create job
        from uuid import uuid4
        job_id = str(uuid4())
        
        job_data = {
            "job_id": job_id,
            "dataset_id": dataset_id,
            "user_id": user_id,
            "status": "queued",
            "progress": 0,
            "current_phase": "Queued",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await cache_manager.set(f"eda:job:{job_id}", job_data, ttl=86400)
        logger.info(f"🔄 Job created: {job_id}")
        
        # Log activity
        from app.models.models import Activity
        activity = Activity(
            user_id=user_id,
            action="analysis_started",
            entity_type="dataset",
            entity_id=dataset_id,
            details=json.dumps({"job_id": job_id})
        )
        db.add(activity)
        db.commit()
        logger.info(f"📝 Activity logged")
        
        # Start background task
        background_tasks.add_task(run_eda_analysis, job_id, dataset_id, db)
        logger.info(f"🚀 Background analysis task started for job: {job_id}")
        
        return {
            "job_id": job_id,
            "dataset_id": dataset_id,
            "status": "queued",
            "message": "Analysis started. Use GET /api/eda/jobs/{job_id} to check progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 3: GET JOB STATUS
# ============================================================================

@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"]
)
async def get_job_status(request: Request, job_id: str, db: Session = Depends(get_db)):
    """✅ Get Job Status - Check analysis progress"""
    try:
        logger.info(f"🔍 Job status requested: {job_id}")
        
        user_id = get_user_id_from_token(request)
        
        job_data = await cache_manager.get(f"eda:job:{job_id}")
        
        if not job_data:
            logger.warning(f"⚠️ Job not found: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found or expired")
        
        job = job_data if isinstance(job_data, dict) else json.loads(job_data)
        job.setdefault("progress", 0)
        job.setdefault("current_phase", "Processing")
        job.setdefault("updated_at", datetime.utcnow().isoformat())
        job.setdefault("dataset_id", job.get("dataset_id", "unknown"))
        job.setdefault("created_at", job.get("created_at", datetime.utcnow().isoformat()))
        
        logger.info(f"✅ Job status: {job['status']} (progress: {job.get('progress', 0)}%)")
        
        return JobStatusResponse(**job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching job status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

# ============================================================================
# ENDPOINT 4: GET SUMMARY (FROM DATABASE)
# ============================================================================

@router.get(
    "/{dataset_id}/summary",
    status_code=status.HTTP_200_OK,
    tags=["Results"]
)
async def get_summary(request: Request, dataset_id: str, db: Session = Depends(get_db)):
    """✅ Get Data Summary - Basic profile from database"""
    try:
        logger.info(f"📋 Summary requested for dataset: {dataset_id}")
        
        user_id = get_user_id_from_token(request)
        
        result = db.query(EdaResult).filter(EdaResult.dataset_id == dataset_id).first()
        
        if not result or not result.summary:
            logger.warning(f"⚠️ Summary not found for dataset: {dataset_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found. Run analysis first using POST /dataset/{id}/analyze"
            )
        
        summary = json.loads(result.summary)
        logger.info(f"✅ Summary retrieved from database")
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

# ============================================================================
# ENDPOINT 5: GET STATISTICS (FROM DATABASE)
# ============================================================================

@router.get(
    "/{dataset_id}/statistics",
    status_code=status.HTTP_200_OK,
    tags=["Results"]
)
async def get_statistics(request: Request, dataset_id: str, db: Session = Depends(get_db)):
    """✅ Get Statistics - Descriptive statistics from database"""
    try:
        logger.info(f"📊 Statistics requested for dataset: {dataset_id}")
        
        user_id = get_user_id_from_token(request)
        
        result = db.query(EdaResult).filter(EdaResult.dataset_id == dataset_id).first()
        
        if not result or not result.statistics:
            logger.warning(f"⚠️ Statistics not found for dataset: {dataset_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Statistics not found. Run analysis first using POST /dataset/{id}/analyze"
            )
        
        statistics = json.loads(result.statistics)
        logger.info(f"✅ Statistics retrieved from database")
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# ============================================================================
# ENDPOINT 6: GET QUALITY REPORT (FROM DATABASE)
# ============================================================================

@router.get(
    "/{dataset_id}/quality-report",
    status_code=status.HTTP_200_OK,
    tags=["Results"]
)
async def get_quality_report(request: Request, dataset_id: str, db: Session = Depends(get_db)):
    """✅ Get Quality Report - Data quality metrics from database"""
    try:
        logger.info(f"🔍 Quality report requested for dataset: {dataset_id}")
        
        user_id = get_user_id_from_token(request)
        
        result = db.query(EdaResult).filter(EdaResult.dataset_id == dataset_id).first()
        
        if not result or not result.quality:
            logger.warning(f"⚠️ Quality report not found for dataset: {dataset_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality report not found. Run analysis first using POST /dataset/{id}/analyze"
            )
        
        quality = json.loads(result.quality)
        logger.info(f"✅ Quality report retrieved from database")
        return quality
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching quality report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quality report: {str(e)}")

# ============================================================================
# ENDPOINT 7: GET CORRELATIONS (FROM DATABASE)
# ============================================================================

@router.get(
    "/{dataset_id}/correlations",
    status_code=status.HTTP_200_OK,
    tags=["Results"]
)
async def get_correlations(request: Request, dataset_id: str, threshold: float = 0.3, db: Session = Depends(get_db)):
    """✅ Get Correlations - Correlation matrix from database"""
    try:
        logger.info(f"🔗 Correlations requested for dataset: {dataset_id} (threshold: {threshold})")
        
        user_id = get_user_id_from_token(request)
        
        result = db.query(EdaResult).filter(EdaResult.dataset_id == dataset_id).first()
        
        if not result or not result.correlations:
            logger.warning(f"⚠️ Correlations not found for dataset: {dataset_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Correlations not found. Run analysis first using POST /dataset/{id}/analyze"
            )
        
        correlations = json.loads(result.correlations)
        logger.info(f"✅ Correlations retrieved from database")
        return correlations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get correlations: {str(e)}")

