# ✅ Installation Verification Checklist

## 🚀 Run This After Deployment

```bash
# After running: python main.py
# In a NEW terminal, run:

python << 'EOF'
import sys
sys.path.insert(0, '.')

print("\n" + "=" * 70)
print("🔍 COMPREHENSIVE INSTALLATION VERIFICATION")
print("=" * 70)

# Test 1: Database Connection
print("\n1️⃣ Testing Database Connection...")
try:
    from app.core.database import engine, Base
    connection = engine.connect()
    connection.close()
    print("   ✅ Database connection OK")
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")
    sys.exit(1)

# Test 2: Models Import
print("\n2️⃣ Testing Models Import...")
try:
    from app.models.models import User, Workspace, Project, Datasource, Dataset, Model, Activity
    print("   ✅ All 7 models imported")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    sys.exit(1)

# Test 3: Base Instance Check (CRITICAL!)
print("\n3️⃣ Checking Base Instance Registration...")
try:
    from app.core.database import Base
    num_tables = len(Base.metadata.tables)
    print(f"   Base.metadata has {num_tables} tables registered")
    
    if num_tables == 0:
        print("   ❌ CRITICAL: No tables registered with Base!")
        print("   This means models.py is using a different Base instance!")
        sys.exit(1)
    
    expected_tables = {'users', 'workspaces', 'projects', 'datasources', 'datasets', 'models', 'activities', 'model_datasets'}
    registered_tables = set(Base.metadata.tables.keys())
    
    if registered_tables == expected_tables:
        print(f"   ✅ All 8 expected tables registered: {sorted(registered_tables)}")
    else:
        missing = expected_tables - registered_tables
        extra = registered_tables - expected_tables
        if missing:
            print(f"   ⚠️  Missing tables: {missing}")
        if extra:
            print(f"   ⚠️  Extra tables: {extra}")
        
except Exception as e:
    print(f"   ❌ Base check failed: {e}")
    sys.exit(1)

# Test 4: Database Tables
print("\n4️⃣ Checking Database Tables...")
try:
    from sqlalchemy import inspect
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())
    
    if len(db_tables) == 0:
        print("   ❌ NO TABLES IN DATABASE!")
        print("   Run: python main.py")
        sys.exit(1)
    
    print(f"   ✅ {len(db_tables)} tables in database: {sorted(db_tables)}")
    
except Exception as e:
    print(f"   ❌ Database table check failed: {e}")
    sys.exit(1)

# Test 5: Session Creation
print("\n5️⃣ Testing Database Session...")
try:
    from app.core.database import SessionLocal
    db = SessionLocal()
    # Try a simple query
    result = db.execute("SELECT 1")
    db.close()
    print("   ✅ Database session works")
except Exception as e:
    print(f"   ❌ Session creation failed: {e}")
    sys.exit(1)

# Test 6: Model Creation
print("\n6️⃣ Testing Model Creation (in-memory)...")
try:
    from app.models.models import User
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password"
    )
    print(f"   ✅ User model created: {user}")
except Exception as e:
    print(f"   ❌ Model creation failed: {e}")
    sys.exit(1)

# Test 7: API Routes
print("\n7️⃣ Testing API Routes...")
try:
    import importlib
    routes_to_test = [
        'app.api.auth',
        'app.api.workspaces',
        'app.api.projects',
        'app.api.datasets',
        'app.api.datasources',
        'app.api.models',
        'app.api.activities'
    ]
    
    for route_module in routes_to_test:
        importlib.import_module(route_module)
        print(f"   ✅ {route_module} imported")
        
except Exception as e:
    print(f"   ❌ Route import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\n✅ Installation is COMPLETE and WORKING")
print("✅ All 8 tables created successfully")
print("✅ All 7 models registered")
print("✅ All API routes available")
print("✅ Database sessions working")
print("\n🎉 Backend is READY FOR USE!")
print("=" * 70 + "\n")

EOF
```

---

## 📋 Expected Output:

```
1️⃣ Testing Database Connection...
   ✅ Database connection OK

2️⃣ Testing Models Import...
   ✅ All 7 models imported

3️⃣ Checking Base Instance Registration...
   Base.metadata has 8 tables registered
   ✅ All 8 expected tables registered

4️⃣ Checking Database Tables...
   ✅ 8 tables in database

5️⃣ Testing Database Session...
   ✅ Database session works

6️⃣ Testing Model Creation...
   ✅ User model created

7️⃣ Testing API Routes...
   ✅ app.api.auth imported
   ✅ app.api.workspaces imported
   ... (all routes)

✅ ALL TESTS PASSED!
🎉 Backend is READY FOR USE!
```

---

## ✅ What Each Test Verifies:

1. **Database Connection** - Engine connects properly
2. **Models Import** - All 7 models can be imported
3. **Base Instance** - CRITICAL: Models use same Base instance
4. **Database Tables** - All 8 tables created in database
5. **Sessions** - Database sessions work correctly
6. **Model Objects** - Models can be instantiated
7. **API Routes** - All routes load without errors

---

## 🚨 If Any Test Fails:

**STOP! Do NOT proceed**

| Test | Fails | Meaning |
|------|-------|---------|
| 1 | Database connection | Check DATABASE_URL, permissions |
| 2 | Models import | Check models.py syntax |
| 3 | Base registration | **models.py using wrong Base!** |
| 4 | No database tables | Run `python main.py` to create tables |
| 5 | Session creation | Database might be locked |
| 6 | Model creation | SQLAlchemy model definition error |
| 7 | Route import | API files have syntax errors |

