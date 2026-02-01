"""
Kedro EDA Pipeline - Phase 1: Data Profiling
INTEGRATED: Ready to add to existing Kedro project
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DATA PROFILER CLASS
# ============================================================================

class DataProfiler:
    """
    Generate comprehensive data profile
    INTEGRATED: Phase 1 of EDA analysis
    """
    
    @staticmethod
    def profile_data(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Profile complete dataset
        
        Args:
            df: Input DataFrame
        
        Returns:
            Dictionary with complete data profile
            
        Example:
            >>> df = pd.read_csv('data.csv')
            >>> profile = DataProfiler.profile_data(df)
            >>> print(profile['rows'])
            10000
        """
        logger.info(f"📊 Profiling dataset: {df.shape[0]} rows, {df.shape[1]} columns")
        
        try:
            profile = {
                # Basic shape and size
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "memory_mb": float(df.memory_usage(deep=True).sum() / (1024**2)),
                
                # Data types
                "data_types": DataProfiler._analyze_data_types(df),
                
                # Missing values
                "missing_values": DataProfiler._analyze_missing_values(df),
                
                # Duplicates
                "duplicates": DataProfiler._analyze_duplicates(df),
                
                # Column types
                "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
                "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
                "datetime_columns": df.select_dtypes(include=['datetime64']).columns.tolist(),
                
                # Metadata
                "profile_generated_at": pd.Timestamp.now().isoformat()
            }
            
            logger.info("✅ Data profiling complete")
            return profile
        
        except Exception as e:
            logger.error(f"❌ Profiling failed: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _analyze_data_types(df: pd.DataFrame) -> Dict[str, int]:
        """Count columns by data type"""
        return {
            str(dtype): int(count)
            for dtype, count in df.dtypes.value_counts().items()
        }
    
    @staticmethod
    def _analyze_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze missing values in detail
        """
        missing_total = int(df.isnull().sum().sum())
        total_cells = len(df) * len(df.columns)
        
        return {
            "count": missing_total,
            "percent": round(missing_total / total_cells * 100, 2) if total_cells > 0 else 0,
            "by_column": {
                col: int(df[col].isnull().sum())
                for col in df.columns
            },
            "by_column_percent": {
                col: round(df[col].isnull().sum() / len(df) * 100, 2)
                for col in df.columns
            }
        }
    
    @staticmethod
    def _analyze_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze duplicate rows
        """
        dup_count = int(df.duplicated().sum())
        
        return {
            "count": dup_count,
            "percent": round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0,
            "by_column": {
                col: int(df[col].duplicated().sum())
                for col in df.columns
            }
        }

# ============================================================================
# KEDRO NODE FUNCTION
# ============================================================================

def profile_data_node(raw_dataset: pd.DataFrame) -> Dict[str, Any]:
    """
    Kedro node for data profiling
    
    INTEGRATED: Ready to use in your Kedro pipeline
    
    Input:
        raw_dataset: DataFrame from catalog
    
    Output:
        data_profile: Dictionary with profile results
    
    Usage in pipeline:
        node(
            func=profile_data_node,
            inputs="raw_dataset",
            outputs="data_profile",
            name="phase_1_data_profiling"
        )
    """
    logger.info("🔄 Executing Phase 1: Data Profiling")
    return DataProfiler.profile_data(raw_dataset)

# ============================================================================
# ADDITIONAL UTILITIES
# ============================================================================

def format_profile_for_display(profile: Dict[str, Any]) -> str:
    """
    Format profile data for console display
    
    Args:
        profile: Profile dictionary
    
    Returns:
        Formatted string for logging
    """
    lines = [
        "=" * 70,
        "DATA PROFILE SUMMARY",
        "=" * 70,
        f"📊 Rows: {profile['rows']:,}",
        f"📊 Columns: {profile['columns']}",
        f"💾 Memory: {profile['memory_mb']:.2f} MB",
        f"📋 Data Types: {profile['data_types']}",
        f"❌ Missing Values: {profile['missing_values']['count']:,} ({profile['missing_values']['percent']:.2f}%)",
        f"🔄 Duplicate Rows: {profile['duplicates']['count']:,} ({profile['duplicates']['percent']:.2f}%)",
        f"🔢 Numeric Columns: {len(profile['numeric_columns'])} - {profile['numeric_columns'][:5]}...",
        f"📝 Categorical Columns: {len(profile['categorical_columns'])} - {profile['categorical_columns'][:5]}...",
        "=" * 70,
    ]
    return "\n".join(lines)

# ============================================================================
# EXPORT FOR INTEGRATION
# ============================================================================

__all__ = [
    'DataProfiler',
    'profile_data_node',
    'format_profile_for_display'
]
