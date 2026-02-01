"""
EDA Integration Test Suite
INTEGRATED: Tests all EDA components

Run with: python test_eda_integration.py
"""

import pandas as pd
import numpy as np
import asyncio
import json
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# TEST 1: Phase 1 Profiling
# ============================================================================

def test_phase1_profiling():
    """Test Phase 1 data profiling"""
    logger.info("=" * 70)
    logger.info("[TEST 1/5] Phase 1: Data Profiling")
    logger.info("=" * 70)
    
    try:
        from src.ml_engine.pipelines.eda.phase1_profiling import DataProfiler
        
        # Create test data
        df = pd.DataFrame({
            'id': range(1, 101),
            'age': np.random.randint(18, 80, 100),
            'salary': np.random.randint(20000, 200000, 100),
            'department': np.random.choice(['Sales', 'Engineering', 'HR', 'Marketing'], 100),
            'hired_date': pd.date_range('2020-01-01', periods=100),
            'score': np.random.uniform(0, 100, 100)
        })
        
        # Add some missing values
        df.loc[5:10, 'salary'] = None
        df.loc[20:25, 'department'] = None
        
        logger.info(f"📊 Test data created: {df.shape}")
        
        # Profile
        profile = DataProfiler.profile_data(df)
        
        # Verify
        assert profile['rows'] == 100, "Row count mismatch"
        assert profile['columns'] == 6, "Column count mismatch"
        assert len(profile['numeric_columns']) > 0, "No numeric columns"
        assert len(profile['categorical_columns']) > 0, "No categorical columns"
        assert profile['missing_values']['count'] > 0, "Missing values not detected"
        
        logger.info(f"✅ Rows: {profile['rows']}")
        logger.info(f"✅ Columns: {profile['columns']}")
        logger.info(f"✅ Memory: {profile['memory_mb']:.3f} MB")
        logger.info(f"✅ Missing values: {profile['missing_values']['count']}")
        logger.info(f"✅ Data types: {profile['data_types']}")
        logger.info(f"✅ Test 1 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 1 FAILED: {str(e)}", exc_info=True)
        return False

# ============================================================================
# TEST 2: Cache Manager
# ============================================================================

async def test_cache_manager():
    """Test cache operations"""
    logger.info("=" * 70)
    logger.info("[TEST 2/5] Cache Manager")
    logger.info("=" * 70)
    
    try:
        from app.core.cache import cache_manager
        
        # Test data
        test_data = {
            "rows": 100,
            "columns": 6,
            "memory_mb": 0.01
        }
        
        # Set
        logger.info("🧪 Testing SET...")
        result = await cache_manager.set("test:eda", test_data, ttl=3600)
        assert result, "SET failed"
        logger.info("✅ SET successful")
        
        # Get
        logger.info("🧪 Testing GET...")
        retrieved = await cache_manager.get("test:eda")
        assert retrieved, "GET failed"
        logger.info("✅ GET successful")
        
        # Ping
        logger.info("🧪 Testing PING...")
        ping_result = await cache_manager.ping()
        assert ping_result, "PING failed"
        logger.info("✅ PING successful")
        
        # Delete
        logger.info("🧪 Testing DELETE...")
        delete_result = await cache_manager.delete("test:eda")
        assert delete_result, "DELETE failed"
        logger.info("✅ DELETE successful")
        
        logger.info(f"✅ Test 2 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 2 FAILED: {str(e)}", exc_info=True)
        return False

# ============================================================================
# TEST 3: EDA Schemas
# ============================================================================

def test_schemas():
    """Test Pydantic schemas"""
    logger.info("=" * 70)
    logger.info("[TEST 3/5] Pydantic Schemas")
    logger.info("=" * 70)
    
    try:
        from app.schemas.eda_schemas import (
            HealthResponse,
            JobStatusResponse,
            DataProfile,
            StatisticsResponse
        )
        from datetime import datetime
        
        # Test HealthResponse
        logger.info("🧪 Testing HealthResponse...")
        health = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components={
                "api": "healthy",
                "cache": "healthy",
                "database": "healthy"
            }
        )
        assert health.status == "healthy"
        logger.info("✅ HealthResponse valid")
        
        # Test JobStatusResponse
        logger.info("🧪 Testing JobStatusResponse...")
        job = JobStatusResponse(
            job_id="test-job-123",
            dataset_id="test-dataset-123",
            status="processing",
            progress=50,
            current_phase="Statistical Analysis",
            created_at=datetime.utcnow()
        )
        assert job.job_id == "test-job-123"
        logger.info("✅ JobStatusResponse valid")
        
        # Test DataProfile
        logger.info("🧪 Testing DataProfile...")
        profile = DataProfile(
            rows=100,
            columns=6,
            memory_mb=0.01,
            missing_values_percent=2.5,
            duplicate_rows=0,
            data_types={"int64": 3, "object": 2, "datetime64": 1},
            numeric_columns=["age", "salary", "score"],
            categorical_columns=["department"],
            generated_at=datetime.utcnow()
        )
        assert profile.rows == 100
        logger.info("✅ DataProfile valid")
        
        logger.info(f"✅ Test 3 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 3 FAILED: {str(e)}", exc_info=True)
        return False

# ============================================================================
# TEST 4: End-to-End Integration
# ============================================================================

async def test_e2e_integration():
    """Test end-to-end integration"""
    logger.info("=" * 70)
    logger.info("[TEST 4/5] End-to-End Integration")
    logger.info("=" * 70)
    
    try:
        from src.ml_engine.pipelines.eda.phase1_profiling import DataProfiler
        from app.core.cache import cache_manager
        import json
        
        # Create test data
        logger.info("🧪 Creating test data...")
        df = pd.DataFrame({
            'id': range(1, 51),
            'value': np.random.randint(0, 100, 50),
            'category': np.random.choice(['A', 'B', 'C'], 50)
        })
        logger.info(f"✅ Test data created: {df.shape}")
        
        # Profile data
        logger.info("🧪 Profiling data...")
        profile = DataProfiler.profile_data(df)
        logger.info(f"✅ Data profiled")
        
        # Cache results
        logger.info("🧪 Caching results...")
        await cache_manager.set(
            "test:eda:summary:e2e",
            profile,
            ttl=3600
        )
        logger.info(f"✅ Results cached")
        
        # Retrieve from cache
        logger.info("🧪 Retrieving from cache...")
        cached = await cache_manager.get("test:eda:summary:e2e")
        assert cached, "Cache retrieval failed"
        cached_data = json.loads(cached)
        logger.info(f"✅ Results retrieved from cache")
        
        # Verify data integrity
        logger.info("🧪 Verifying data integrity...")
        assert cached_data['rows'] == 50
        assert cached_data['columns'] == 3
        logger.info(f"✅ Data integrity verified")
        
        logger.info(f"✅ Test 4 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 4 FAILED: {str(e)}", exc_info=True)
        return False

# ============================================================================
# TEST 5: File I/O (Kedro integration)
# ============================================================================

def test_file_io():
    """Test data file handling"""
    logger.info("=" * 70)
    logger.info("[TEST 5/5] File I/O & Kedro Integration")
    logger.info("=" * 70)
    
    try:
        # Create sample CSV
        logger.info("🧪 Creating sample CSV...")
        df = pd.DataFrame({
            'age': [25, 30, 35, 40, 45],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'department': ['Sales', 'Engineering', 'Sales', 'HR', 'Engineering']
        })
        
        csv_path = Path("data/01_raw/test_sample.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        logger.info(f"✅ Sample CSV created: {csv_path}")
        
        # Read and profile
        logger.info("🧪 Reading and profiling CSV...")
        from src.ml_engine.pipelines.eda.phase1_profiling import DataProfiler
        
        df_read = pd.read_csv(csv_path)
        profile = DataProfiler.profile_data(df_read)
        
        assert profile['rows'] == 5
        logger.info(f"✅ CSV profiling successful")
        
        # Cleanup
        logger.info("🧪 Cleaning up...")
        csv_path.unlink()
        logger.info(f"✅ Test file cleaned up")
        
        logger.info(f"✅ Test 5 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 5 FAILED: {str(e)}", exc_info=True)
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 15 + "EDA INTEGRATION TEST SUITE" + " " * 27 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Test 1: Profiling
    results.append(("Phase 1 Profiling", test_phase1_profiling()))
    
    # Test 2: Cache
    results.append(("Cache Manager", await test_cache_manager()))
    
    # Test 3: Schemas
    results.append(("Pydantic Schemas", test_schemas()))
    
    # Test 4: E2E
    results.append(("End-to-End", await test_e2e_integration()))
    
    # Test 5: File I/O
    results.append(("File I/O", test_file_io()))
    
    # Summary
    logger.info("\n")
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("=" * 70)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 70)
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Ready for production!")
        return True
    else:
        logger.error(f"⚠️ {total - passed} test(s) failed")
        return False

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
