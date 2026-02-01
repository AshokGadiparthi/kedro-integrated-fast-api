"""
EDA Pipeline - Exploratory Data Analysis
INTEGRATED: Ready to register in your Kedro project

This module contains all EDA analysis pipelines:
- Phase 1: Data Profiling (implemented)
- Phase 2: Statistical Analysis (to be added)
- Phase 3: Correlation Analysis (to be added)
- Phase 4: Data Quality (to be added)
- Phase 5: Visualizations (to be added)
- Phase 6: Advanced Analysis (to be added)
"""

from kedro.pipeline import Pipeline, node
from .phase1_profiling import profile_data_node

def create_eda_pipeline() -> Pipeline:
    """
    Create complete EDA analysis pipeline
    
    INTEGRATED: Call this from your pipeline_registry.py
    
    Example in pipeline_registry.py:
        from ml_engine.pipelines.eda import create_eda_pipeline
        
        def register_pipelines() -> Dict[str, Pipeline]:
            return {
                "eda": create_eda_pipeline(),
                ...other pipelines...
            }
    
    Returns:
        Kedro Pipeline object
    """
    return Pipeline([
        # ====================================================================
        # PHASE 1: DATA PROFILING
        # ====================================================================
        node(
            func=profile_data_node,
            inputs="raw_dataset",
            outputs="data_profile",
            name="phase_1_data_profiling",
            tags=["eda", "profiling"]
        ),
        # ====================================================================
        # Phase 2-6 nodes will be added here as they are implemented
        # ====================================================================
    ])

# ============================================================================
# PHASE-SPECIFIC PIPELINE CREATORS (for modular development)
# ============================================================================

def create_eda_phase1_only() -> Pipeline:
    """Create only Phase 1 profiling pipeline (for testing)"""
    return Pipeline([
        node(
            func=profile_data_node,
            inputs="raw_dataset",
            outputs="data_profile",
            name="phase_1_data_profiling",
            tags=["eda", "profiling"]
        ),
    ])

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'create_eda_pipeline',
    'create_eda_phase1_only'
]
