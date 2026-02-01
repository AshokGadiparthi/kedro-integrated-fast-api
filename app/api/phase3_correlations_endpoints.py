"""
Phase 3: Advanced Correlations API Endpoints
FastAPI router for advanced correlation analysis
FINAL CUSTOMIZED VERSION - Works with YOUR Dataset model!
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
from datetime import datetime
import pandas as pd
import os

# ✅ Correct imports
from app.core.phase3_advanced_correlations import AdvancedCorrelationAnalysis
from app.core.database import get_db
from app.models.models import Dataset
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/eda", tags=["Phase 3 - Correlations"])
logger = logging.getLogger(__name__)


def get_dataset_from_db(dataset_id: str, db: Session) -> Optional[pd.DataFrame]:
    """
    Get dataset from database - CUSTOMIZED for YOUR schema

    Your Dataset model has these attributes:
    - id: Dataset ID
    - project_id: Project reference
    - file_name: ✅ THE FILE PATH/NAME
    - created_at: Creation timestamp
    - description: Description text
    - name: Dataset name
    - file_size_bytes: File size

    Args:
        dataset_id: The dataset ID
        db: Database session (dependency injection)

    Returns:
        pandas DataFrame or None if not found
    """
    try:
        logger.info(f"📂 Retrieving dataset: {dataset_id}")

        # Query the database using the session
        dataset_record = db.query(Dataset).filter(
            Dataset.id == dataset_id
        ).first()

        if not dataset_record:
            logger.warning(f"⚠️ Dataset not found: {dataset_id}")
            return None

        # ✅ YOUR SCHEMA: Use file_name attribute
        file_path = None

        # Try primary attribute first (YOUR schema)
        if hasattr(dataset_record, 'file_name') and dataset_record.file_name:
            file_path = dataset_record.file_name
            logger.info(f"✅ Found file path in attribute: 'file_name'")

        # Fallback to other common attributes if needed
        if not file_path:
            possible_attributes = [
                'file_path',      # Alternative names
                'storage_path',
                'path',
                'file_location',
                'upload_path',
                'data_path',
                'filepath'
            ]

            for attr_name in possible_attributes:
                if hasattr(dataset_record, attr_name):
                    potential_path = getattr(dataset_record, attr_name)
                    if potential_path:
                        file_path = potential_path
                        logger.info(f"✅ Found file path in attribute: '{attr_name}'")
                        break

        # If still no file path found, log available attributes
        if not file_path:
            available_attrs = [k for k in dataset_record.__dict__.keys() if not k.startswith('_')]
            logger.error(f"❌ No file path found in Dataset attributes")
            logger.error(f"   Available: {available_attrs}")
            logger.error(f"   Expected one of: file_name, file_path, storage_path, path, file_location")
            raise HTTPException(
                status_code=500,
                detail=f"Cannot determine file path. Dataset attributes: {available_attrs}"
            )

        # Verify file exists
        if not os.path.exists(file_path):
            logger.error(f"❌ File not found at path: {file_path}")
            logger.error(f"   File path type: {type(file_path)}")
            logger.error(f"   File path value: {file_path}")
            raise HTTPException(status_code=500, detail=f"Dataset file not found: {file_path}")

        # Load the CSV file
        logger.info(f"📖 Loading CSV from: {file_path}")
        df = pd.read_csv(file_path)
        logger.info(f"✅ Loaded dataset {dataset_id} with shape {df.shape}")
        return df

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving dataset {dataset_id}: {str(e)}")
        logger.error(f"   Exception type: {type(e).__name__}")
        return None


@router.get("/{dataset_id}/phase3/correlations/enhanced")
async def get_enhanced_correlations(
        dataset_id: str,
        threshold: float = Query(0.3, ge=0.0, le=1.0),
        db: Session = Depends(get_db)
) -> dict:
    """
    Get enhanced correlation analysis

    Parameters:
    - dataset_id: Dataset ID
    - threshold: Correlation threshold (0.0-1.0, default: 0.3)

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
        df = get_dataset_from_db(dataset_id, db)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in enhanced correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing correlations: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/vif")
async def get_vif_analysis(
        dataset_id: str,
        db: Session = Depends(get_db)
) -> dict:
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

        df = get_dataset_from_db(dataset_id, db)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in VIF analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in VIF analysis: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/heatmap-data")
async def get_heatmap_data(
        dataset_id: str,
        db: Session = Depends(get_db)
) -> dict:
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

        df = get_dataset_from_db(dataset_id, db)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating heatmap data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating heatmap: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/clustering")
async def get_correlation_clustering(
        dataset_id: str,
        db: Session = Depends(get_db)
) -> dict:
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

        df = get_dataset_from_db(dataset_id, db)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in correlation clustering: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in clustering: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/relationship-insights")
async def get_relationship_insights(
        dataset_id: str,
        db: Session = Depends(get_db)
) -> dict:
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

        df = get_dataset_from_db(dataset_id, db)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating relationship insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/warnings")
async def get_multicollinearity_warnings(
        dataset_id: str,
        db: Session = Depends(get_db)
) -> dict:
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

        df = get_dataset_from_db(dataset_id, db)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating warnings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating warnings: {str(e)}")


@router.get("/{dataset_id}/phase3/correlations/complete")
async def get_complete_correlation_analysis(
        dataset_id: str,
        threshold: float = Query(0.3, ge=0.0, le=1.0),
        db: Session = Depends(get_db)
) -> dict:
    """
    Get complete correlation analysis (all endpoints combined)

    This is the RECOMMENDED endpoint - use this for best performance!

    Parameters:
    - dataset_id: Dataset ID
    - threshold: Correlation threshold (0.0-1.0, default: 0.3)

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

        df = get_dataset_from_db(dataset_id, db)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in complete correlation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")