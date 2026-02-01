"""
Phase 3: Advanced Correlations API Endpoints
FastAPI router for advanced correlation analysis
FIXED VERSION - Correct imports for your project structure
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime
import pandas as pd

# ✅ FIXED: Use correct import path
from app.core.phase3_advanced_correlations import AdvancedCorrelationAnalysis
from app.core.database import get_db
from app.models.models import Dataset

router = APIRouter(prefix="/api/eda", tags=["Phase 3 - Correlations"])
logger = logging.getLogger(__name__)


@router.get("/{dataset_id}/phase3/correlations/enhanced")
async def get_enhanced_correlations(
        dataset_id: str,
        threshold: float = Query(0.3, ge=0.0, le=1.0)
) -> dict:
    """
    Get enhanced correlation analysis

    Returns:
    - Correlation matrix
    - Correlation pairs above threshold
    - High correlation pairs (>0.7)
    - Very high correlation pairs (>0.9)
    - Multicollinearity pairs
    - Strength distribution
    - Statistics

    Response time: ~200-300ms
    """
    try:
        logger.info(f"📊 Enhanced correlations requested for dataset: {dataset_id}")

        # Get dataset
        df = await get_dataset(dataset_id)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        # Perform analysis
        analyzer = AdvancedCorrelationAnalysis(df)
        results = analyzer.get_enhanced_correlations(threshold=threshold)

        logger.info(f"✅ Enhanced correlations analysis completed")

        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": results,
            "threshold": threshold,
            "analysis_type": "Enhanced Correlations",
            "total_features": len(df.select_dtypes(include=['number']).columns)
        }

    except Exception as e:
        logger.error(f"❌ Error in enhanced correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing correlations: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/vif")
async def get_vif_analysis(dataset_id: str) -> dict:
    """
    Get Variance Inflation Factor (VIF) analysis

    Returns:
    - VIF scores for each numeric feature
    - Severity levels
    - Problematic features
    - Overall multicollinearity level
    - Interpretation

    VIF Interpretation:
    - VIF < 5: Acceptable
    - VIF 5-10: Moderate multicollinearity (caution)
    - VIF > 10: High multicollinearity (action needed)

    Response time: ~250-350ms
    """
    try:
        logger.info(f"📈 VIF analysis requested for dataset: {dataset_id}")

        df = await get_dataset(dataset_id)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        analyzer = AdvancedCorrelationAnalysis(df)
        vif_results = analyzer.get_vif_analysis()

        logger.info(f"✅ VIF analysis completed")

        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": vif_results,
            "analysis_type": "VIF (Variance Inflation Factor)",
            "interpretation_guide": {
                "low": "VIF < 5: Acceptable multicollinearity",
                "moderate": "VIF 5-10: Moderate multicollinearity - caution recommended",
                "high": "VIF > 10: High multicollinearity - action needed"
            }
        }

    except Exception as e:
        logger.error(f"❌ Error in VIF analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in VIF analysis: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/heatmap-data")
async def get_heatmap_data(dataset_id: str) -> dict:
    """
    Get correlation heatmap visualization data

    Returns:
    - Heatmap data in list format
    - Column names
    - Min/max correlation values

    Response time: ~150-250ms
    """
    try:
        logger.info(f"🔥 Heatmap data requested for dataset: {dataset_id}")

        df = await get_dataset(dataset_id)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        analyzer = AdvancedCorrelationAnalysis(df)
        heatmap_data = analyzer.get_correlation_heatmap_data()

        logger.info(f"✅ Heatmap data generated")

        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "heatmap": heatmap_data,
            "analysis_type": "Correlation Heatmap Data"
        }

    except Exception as e:
        logger.error(f"❌ Error generating heatmap data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating heatmap: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/clustering")
async def get_correlation_clustering(dataset_id: str) -> dict:
    """
    Get feature clustering based on correlations

    Returns:
    - Feature clusters
    - Cluster count
    - Cluster interpretation

    Response time: ~300-400ms
    """
    try:
        logger.info(f"🎯 Correlation clustering requested for dataset: {dataset_id}")

        df = await get_dataset(dataset_id)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        analyzer = AdvancedCorrelationAnalysis(df)
        clustering = analyzer.get_correlation_clustering()

        logger.info(f"✅ Correlation clustering completed")

        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "clustering": clustering,
            "analysis_type": "Correlation-Based Feature Clustering"
        }

    except Exception as e:
        logger.error(f"❌ Error in correlation clustering: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in clustering: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/relationship-insights")
async def get_relationship_insights(dataset_id: str) -> dict:
    """
    Get relationship insights and patterns

    Returns:
    - Strongest positive relationships
    - Strongest negative relationships
    - Uncorrelated pairs
    - Feature connectivity scores
    - Interesting patterns

    Response time: ~200-300ms
    """
    try:
        logger.info(f"🔗 Relationship insights requested for dataset: {dataset_id}")

        df = await get_dataset(dataset_id)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        analyzer = AdvancedCorrelationAnalysis(df)
        insights = analyzer.get_relationship_insights()

        logger.info(f"✅ Relationship insights generated")

        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "insights": insights,
            "analysis_type": "Relationship Insights"
        }

    except Exception as e:
        logger.error(f"❌ Error generating relationship insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/warnings")
async def get_multicollinearity_warnings(dataset_id: str) -> dict:
    """
    Get multicollinearity warnings and recommendations

    Returns:
    - Warning list
    - Warning count
    - Overall assessment
    - Specific recommendations

    Response time: ~250-350ms
    """
    try:
        logger.info(f"⚠️ Multicollinearity warnings requested for dataset: {dataset_id}")

        df = await get_dataset(dataset_id)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        analyzer = AdvancedCorrelationAnalysis(df)
        warnings = analyzer.get_multicollinearity_warnings()

        logger.info(f"✅ Multicollinearity warnings generated")

        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "warnings": warnings,
            "analysis_type": "Multicollinearity Warnings"
        }

    except Exception as e:
        logger.error(f"❌ Error generating warnings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating warnings: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/complete")
async def get_complete_correlation_analysis(
        dataset_id: str,
        threshold: float = Query(0.3, ge=0.0, le=1.0)
) -> dict:
    """
    Get complete correlation analysis (all endpoints combined)

    Returns:
    - Enhanced correlations
    - VIF analysis
    - Heatmap data
    - Feature clustering
    - Relationship insights
    - Multicollinearity warnings

    Response time: ~1-2 seconds (combined)
    """
    try:
        logger.info(f"📊 Complete correlation analysis requested for dataset: {dataset_id}")

        df = await get_dataset(dataset_id)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

        analyzer = AdvancedCorrelationAnalysis(df)

        # Gather all analyses
        complete_analysis = {
            "enhanced_correlations": analyzer.get_enhanced_correlations(threshold=threshold),
            "vif_analysis": analyzer.get_vif_analysis(),
            "heatmap_data": analyzer.get_correlation_heatmap_data(),
            "clustering": analyzer.get_correlation_clustering(),
            "relationship_insights": analyzer.get_relationship_insights(),
            "multicollinearity_warnings": analyzer.get_multicollinearity_warnings()
        }

        logger.info(f"✅ Complete correlation analysis finished")

        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": complete_analysis,
            "analysis_type": "Complete Phase 3 Correlation Analysis",
            "components": 6,
            "total_features": len(df.select_dtypes(include=['number']).columns)
        }

    except Exception as e:
        logger.error(f"❌ Error in complete correlation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ✅ FIXED: Correct helper function
async def get_dataset(dataset_id: str):
    """
    Get dataset from your data store
    """
    try:
        db = get_db()

        # Query dataset from database
        dataset_record = db.query(Dataset).filter(
            Dataset.id == dataset_id
        ).first()

        if not dataset_record:
            logger.warning(f"Dataset {dataset_id} not found in database")
            return None

        # Load from file
        df = pd.read_csv(dataset_record.file_path)
        logger.info(f"✅ Loaded dataset {dataset_id} with shape {df.shape}")
        return df

    except Exception as e:
        logger.error(f"❌ Error retrieving dataset {dataset_id}: {str(e)}")
        return None