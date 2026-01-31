# 🚀 PHASE 0 - SETUP INSTRUCTIONS

## What's in Phase 0?

✅ User Registration
✅ User Login with JWT Tokens
✅ Workspace Management (CRUD)
✅ SQLite Database Setup
✅ API Documentation

**Total Setup Time: 30 minutes**

---

## Step 1: Create Virtual Environment

### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

**Expected output:**
```
(venv) $ 
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 pydantic-2.5.0 ...
```

---

## Step 3: Setup Environment File

```bash
cp .env.example .env
```

**The defaults are fine for local development.**

---

## Step 4: Initialize Database

```bash
python -c "from app.core.database import init_db; init_db()"
```

**Expected output:**
```
INFO:__main__:Creating database tables...
✅ Database tables created successfully!
```

**This creates:**
- `ml_platform.db` (SQLite database file)
- `users` table
- `workspaces` table

---

## Step 5: Start the Server

```bash
python main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
✅ Server ready!
```

---

## Step 6: Test the API

### Option A: Interactive API Documentation (Recommended for beginners)

Open in browser:
```
http://127.0.0.1:8000/docs
```

You'll see a beautiful interactive UI where you can:
- See all endpoints
- Try them out
- See request/response examples

### Option B: Using cURL Commands

**Test 1: Register a user**

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "john_doe",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

**Expected response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "username": "john_doe",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

---

**Test 2: Login**

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

**Expected response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@example.com",
    "username": "john_doe",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**⭐ COPY the `access_token` value** - you'll need it for the next requests!

---

**Test 3: Create a Workspace**

Replace `YOUR_TOKEN_HERE` with the token from Test 2:

```bash
TOKEN="YOUR_TOKEN_HERE"

curl -X POST "http://127.0.0.1:8000/api/workspaces" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "My First Workspace",
    "slug": "my-first-workspace",
    "description": "For testing Phase 0"
  }'
```

**Expected response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "My First Workspace",
  "slug": "my-first-workspace",
  "description": "For testing Phase 0",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": true,
  "created_at": "2024-01-15T10:35:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

---

**Test 4: List Workspaces**

```bash
TOKEN="YOUR_TOKEN_HERE"

curl -X GET "http://127.0.0.1:8000/api/workspaces" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "My First Workspace",
    "slug": "my-first-workspace",
    "description": "For testing Phase 0",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "created_at": "2024-01-15T10:35:00",
    "updated_at": "2024-01-15T10:35:00"
  }
]
```

---

## Project Structure

```
ml_platform_phase1/
├── main.py                          ← Start server from here
├── requirements.txt                 ← Python packages
├── .env.example                     ← Environment template
├── SETUP_PHASE_0.md                ← You're reading this!
│
├── app/
│   ├── __init__.py
│   ├── schemas.py                  ← Request/Response validation
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py                 ← Login/Register endpoints
│   │   └── workspaces.py           ← Workspace CRUD endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py             ← Database configuration
│   │   └── auth.py                 ← Password hashing, JWT tokens
│   │
│   └── models/
│       ├── __init__.py
│       └── models.py               ← SQLAlchemy ORM models
│
└── ml_platform.db                  ← SQLite database (created automatically)
```

---

## File Explanations

### main.py
- **What**: FastAPI application entry point
- **Why**: Brings everything together
- **Run**: `python main.py`

### app/schemas.py
- **What**: Pydantic models for validation
- **Why**: Validate JSON from frontend, define response structure
- **Used by**: API routes

### app/models/models.py
- **What**: SQLAlchemy ORM models
- **Why**: Define database tables and relationships
- **Tables**: User, Workspace

### app/core/database.py
- **What**: Database configuration
- **Why**: Setup SQLAlchemy, create session, initialize DB
- **Uses**: SQLite (can switch to PostgreSQL later)

### app/core/auth.py
- **What**: Authentication utilities
- **Why**: Hash passwords, create/verify JWT tokens
- **Functions**: `hash_password()`, `verify_password()`, `create_access_token()`, `verify_token()`

### app/api/auth.py
- **What**: Login/Register endpoints
- **Routes**:
  - `POST /auth/register` - Create account
  - `POST /auth/login` - Get JWT token
  - `GET /auth/me` - Get current user (requires token)

### app/api/workspaces.py
- **What**: Workspace CRUD endpoints
- **Routes**:
  - `GET /api/workspaces` - List workspaces
  - `POST /api/workspaces` - Create workspace
  - `GET /api/workspaces/{id}` - Get details
  - `PUT /api/workspaces/{id}` - Update
  - `DELETE /api/workspaces/{id}` - Delete

---

## How the System Works

### Registration Flow

```
1. User fills form
   {
     "email": "john@example.com",
     "username": "john_doe",
     "password": "password123",
     "full_name": "John Doe"
   }

2. POST /auth/register
   ↓

3. System:
   - Checks if email/username exists
   - Hashes password with bcrypt
   - Saves user to database
   ↓

4. Response:
   {
     "id": "550e8400-...",
     "email": "john@example.com",
     ...
   }
```

### Login Flow

```
1. User fills form
   {
     "email": "john@example.com",
     "password": "password123"
   }

2. POST /auth/login
   ↓

3. System:
   - Finds user by email
   - Verifies password against hash
   - Creates JWT token with user_id
   ↓

4. Response:
   {
     "access_token": "eyJ0eXAi...",
     "token_type": "bearer",
     "user": {...}
   }
```

### Workspace CRUD Flow

```
1. User has token from login
   Authorization: Bearer eyJ0eXAi...

2. POST /api/workspaces
   {
     "name": "My Workspace",
     "slug": "my-workspace",
     "description": "..."
   }
   ↓

3. System:
   - Extracts token
   - Verifies token
   - Gets user_id from token
   - Creates workspace for that user
   - Saves to database
   ↓

4. Response:
   {
     "id": "550e8400-...",
     "name": "My Workspace",
     "owner_id": "550e8400-... (the current user)",
     ...
   }
```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'app'"

**Cause**: Running Python from wrong directory

**Fix**: Make sure you're in `ml_platform_phase1/` when running commands
```bash
cd ml_platform_phase1
python main.py
```

---

### Error: "sqlite3.OperationalError: no such table"

**Cause**: Database not initialized

**Fix**: Run database init
```bash
python -c "from app.core.database import init_db; init_db()"
```

---

### Error: "ModuleNotFoundError: No module named 'passlib'"

**Cause**: Dependencies not installed

**Fix**: Install requirements
```bash
pip install -r requirements.txt
```

---

### Error: "Invalid email or password" when registering

**Cause**: Email format invalid or username already taken

**Fix**: 
- Use valid email format (with @)
- Use unique username
- Check error message in response

---

### Error: Database locked (SQLite)

**Cause**: Another process using database

**Fix**: Close other terminals/applications and try again

---

## Next Steps

1. ✅ **Test everything** - Use /docs at http://127.0.0.1:8000/docs
2. ✅ **Create your first UI screen** - Login/Register form
3. ✅ **Test integration** - Connect frontend to these endpoints
4. ✅ **Once comfortable** - Create Project Management UI
5. ✅ **Share screenshot** - We'll plan Phase 1 together

---

## Questions?

If anything is unclear:
- Read the comments in the code
- Check the error messages
- Ask me! I'm here to help.

This is just the beginning. We'll add features ONE AT A TIME.

**Welcome to baby steps development! 👶** 

Let me know when Phase 0 is working and ready for Phase 1!
